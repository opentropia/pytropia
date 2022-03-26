#!/usr/bin/env python3

import argparse
import json
from os import times
import os
import re
import time
import datetime
import csv
import math
from importlib_metadata import metadata

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates

from logregex import *

# TODO: Ignore list:
# Fruit: 
# Stones: Kaldon
# Universal Ammo

def invert_loot(loot, eff, looter):
    # Efficiency factor can be used to scale the returns according to the
    # theory that 0-100 eff translates to 0-7% TT return
    # Set the to value below to the eff of the setup, setting them to 100% (1.0)
    # is the same as igoring it since the factor will be 1.
    # The factor is applied as a dividend to invert the data.
    factor = 0.86 + 0.07 * (eff/100) + 0.07 * (looter/100)
    #factor = 0.94 + 0.07 * (eff/100)
    #print(factor)
    return loot / factor

def parse_log(file_name, data, normalize_loot):
    last_message = 'cost'
    shots_current = 0
    num_shrap = 0
    bonus_shrap = 0
    first_shrap = 0
    second_shrap = 0

    with open(file_name, "r", encoding="utf8") as log:
        regex = re_base

        current_cost = 0.00000001
        current_loot = 0.00000001
        for line in log.readlines():
            result = re.match(regex, line)
            #timestamp = time.mktime(datetime.datetime.strptime(result.group(1), "%Y-%m-%d %H:%M:%S").timetuple())
            timestamp = datetime.datetime.strptime(result.group(1), "%Y-%m-%d %H:%M:%S")

            channel = result.group(2)
            user = result.group(3)
            message = result.group(4)

            # The assumption is
            #  shot 1
            #  shot 2
            #  shot n
            #   loot 1
            #  shot 1
            #  shot 2
            #  shot n
            #   loot 2
            # etc
            # Works best with auto loot

            # damage taken is currently ignored, assumed to be neglactable

            # Don't treat enhancer breakage as loot
            result1 = re.match(re_sys_enhancer, message)
            if result1:
                value = float(result1.group(4))
                current_loot -= value
                last_message = 'hit'
                print(f"Enhancer broke: {result1.group(1)},  value: {value}")

            # Target evade/dodge/miss
            result1 = re.match(re_sys_target_evade, message)
            result2 = re.match(re_sys_target_dodge, message)
            result3 = re.match(re_sys_target_jammed, message)
            result_hit = re.match(re_sys_you_inflict, message)
            result_crit_hit = re.match(re_sys_you_crit, message)
            result_miss = re.match(re_sys_you_missed, message)

            if result1 or result2 or result3 or result_hit or result_crit_hit or result_miss:
                if last_message == 'loot':
                    ret = (current_loot/current_cost)

                    # Resolve shrapnel
                    if num_shrap >= 2:
                        # The theory is that the bonus loot is always the second shrapnel pile in loots with two shrapnel piles
                        bonus_shrap = second_shrap

                        # Code below is a test to use the first shrapnel pile if it's closer to the expected "multi"
                        #second_shrap_multi = second_shrap / current_cost
                        #first_shrap_multi = first_shrap / current_cost
                        #if (second_shrap_multi < 0.4 or second_shrap_multi > 0.8) and (first_shrap_multi > 0.4 and first_shrap_multi < 0.8):
                        #    bonus_shrap = first_shrap
                        #else:
                        #    bonus_shrap = second_shrap

                    # Ignore spurious data
                    if ret < 100000 and num_shrap <= 2:
                        data['loots'].append(current_loot)
                        data['costs'].append(current_cost)
                        data['bonus_shraps'].append(bonus_shrap)
                        data['timestamps'].append(timestamp)

                    current_loot = 0.0
                    current_cost = 0.0
                    shots_current = 0
                    num_shrap = 0
                    bonus_shrap = 0

                # TODO: how to treat misses? Add option to include or not?
                if not result_miss:
                    current_cost += data['ped_per_shot']

                shots_current += 1

                data['shots'] += 1

                last_message = 'hit'

            # Loot
            result = re.match(re_loot, message)
            if result:
                last_message = 'loot'
                item = result.group(1)
                count = int(result.group(2))
                value = float(result.group(3))

                if normalize_loot:
                    value = invert_loot(value, data['meta-data']['efficiency'], data['meta-data']['looter'])

                # Special handling to calculate value of Shrapnel since
                # to avoid rounding errors.
                if item == "Shrapnel":
                    value = count / 10000
                    value = invert_loot(value, data['meta-data']['efficiency'], data['meta-data']['looter'])

                    if num_shrap == 0:
                        first_shrap = value
                    if num_shrap == 1:
                        second_shrap = value

                    num_shrap += 1

                # Don't count universal ammo
                if item != "Universal Ammo":
                    current_loot += value


def get_data(files, cost_per_shot, remove_shrap, normalize_loot):
    data = {}

    # Check if a meta-data file exists.
    # If multiple files are provided the meta data from the first will be used for all.
    # TODO: handle meta data for each file
    meta_data = {}
    path, filename = os.path.split(files[0].name)
    meta_data_fname = os.path.join(path, "meta-data.json")
    if os.path.exists(meta_data_fname):
        with open(meta_data_fname, "r") as meta_data_file:
            meta_data = json.load(meta_data_file)
    else:
        meta_data['looter'] = 100
        meta_data['efficiency'] = 100
        meta_data['mob'] = "unknown"
        meta_data['weapon'] = "unknown"
        meta_data['attachments'] = "unknown"
        meta_data['pec-per-use'] = 0
        meta_data['comment'] = ""

    if meta_data['pec-per-use'] > 0:
        cost_per_shot = meta_data['pec-per-use']

    if cost_per_shot == 0:
        print("cost_per_shot must be provided, either through meta-data or as an argument!")
        exit(1)

    data['ped_per_shot'] = cost_per_shot / 100
    data['bonus_shraps'] = []
    data['bonus_shraps_multis'] = []
    data['loots'] = []
    data['costs'] = []
    data['returns'] = []
    data['timestamps'] = []
    data['shots'] = 0
    data['meta-data'] = meta_data

    for f in files:
        parse_log(f.name, data, normalize_loot)

    for i in range(len(data['loots'])):
        if remove_shrap:
            data['loots'][i] -= data['bonus_shraps'][i]

        multi = data['loots'][i] / data['costs'][i]

        # Only look at lowest multis
        #if multi > 0.31:
        #    multi = 0

        data['returns'].append(multi)

        data['bonus_shraps_multis'].append(data['bonus_shraps'][i] / data['costs'][i])

    # Subtract min timestamp for relative time from first loot
    # min_timesamp = min(data['timestamps'])
    # data['timestamps'] = [x - min_timesamp for x in data['timestamps']]

    return data

def print_summary(data):
    all_cost = 0
    all_loot = 0
    for i in range(0, len(data['loots'])):
        all_cost += data['costs'][i]
        all_loot += data['loots'][i]

    loots_with_bonus = len([i for i in data['bonus_shraps'] if i > 0])

    print(f"\nNum kills: {len(data['loots'])}")
    print(f"Shots: {data['shots']}")
    print(f"Total loot {(all_loot/all_cost) * 100:.2f}% ({all_loot:.2f}/{all_cost:.2f})")
    print(f"Total bonus shrap {np.sum(data['bonus_shraps']):.2f} PED ({np.sum(data['bonus_shraps'])/all_cost * 100:.2f}% of cost)")
    print(f"Loots with bonus: {(loots_with_bonus/len(data['loots'])*100):.2f}% of all loots")
    # Analyze bottom
    remove_bottom_n = 2
    bottom_procent = 2
    num_samples = int(math.ceil(len(data['returns']) * (bottom_procent / 100)))
    sorted_returns = np.sort(data['returns'])
    #print(f"\nBottom {bottom_procent}% multis:")
    #for i in range(remove_bottom_n, num_samples):
    #    print(sorted_returns[i])

    print(f"Average ({num_samples}): {np.sum(sorted_returns[remove_bottom_n:num_samples+remove_bottom_n] / num_samples)}")
    print(f"Average (5): {np.sum(sorted_returns[remove_bottom_n:5+remove_bottom_n] / 5)}")

def plot_data(data, data2):
    # Plot some things
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"TODO")

    axs[0, 0].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    axs[0, 0].tick_params('x', labelrotation=10)
    axs[0, 0].set_title("Returns over time")
    #axs[0, 0].set_xlabel("Time (s)")
    axs[0, 0].set_ylabel("Loot (multiplier)")
    axs[0, 0].set_ylim([0, 80])
    axs[0, 0].plot(data['timestamps'], data['returns'])
    if data2:
        axs[0, 0].plot(data2['timestamps'], data2['returns'])

    axs[0, 0].grid()

    #t = np.linspace(0, num_mobs, num_mobs)
    axs[1, 0].set_title("Returns sorted")
    axs[1, 0].set_xlabel("Kills")
    axs[1, 0].set_ylabel("Loot (multiplier)")
    axs[1, 0].plot(np.linspace(0, 1, num=len(data['returns'])), np.sort(data['returns']))
    if data2:
        axs[1, 0].plot(np.linspace(0, 1, num=len(data2['returns'])), np.sort(data2['returns']))
        axs[1, 0].set_xlabel(f"Kills normilzed (total {len(data['loots'])}, {len(data2['loots'])})")
    else:
        axs[1, 0].set_xlabel(f"Kills normilzed (total {len(data['loots'])})")
    axs[1, 0].grid()

    #axs[1, 1].set_title("Histogram (just a test)")
    #axs[1, 1].hist(returns, bins=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], density='true')
    #axs[1, 1].grid()



    axs[0, 1].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    axs[0, 1].tick_params('x', labelrotation=10)
    # Plot bonus shraps
    axs[0, 1].set_title("Bonus shrap multis")
    axs[0, 1].plot(data['timestamps'], data['bonus_shraps_multis'])
    if data2:
        axs[0, 1].plot(data2['timestamps'], data2['bonus_shraps_multis'])
    axs[0, 1].set_ylabel("Multiplier")
    #axs[0, 1].set_xlabel("Time (s)")
    axs[0, 1].grid()


    axs[1, 1].set_title("Bonus shrap sorted")
    axs[1, 1].set_ylabel("Multiplier")
    axs[1, 1].plot(np.linspace(0, 1, num=len(data['bonus_shraps_multis'])), np.sort(data['bonus_shraps_multis']))
    if data2:
        axs[1, 1].plot(np.linspace(0, 1, num=len(data2['bonus_shraps_multis'])), np.sort(data2['bonus_shraps_multis']))
        axs[1, 1].set_xlabel(f"Kills normilzed (total {len(data['loots'])}, {len(data2['loots'])})")
    else:
        axs[1, 1].set_xlabel(f"Kills normilzed (total {len(data['loots'])})")

    axs[1, 1].grid()

    plt.show()

def extract_simple_group(data, prev_end_index, step):
    sorted_ret = np.sort(data['returns'])
    diff_multis = np.diff(sorted_ret)

    start_index_guess = prev_end_index + int(len(diff_multis) * step)

    diff_max = 4 * np.amax(diff_multis[start_index_guess:start_index_guess+int(len(diff_multis) * (step/4))])
    print(f"group max {diff_max}")

    start_index = 0
    # search for start
    for i in range(start_index_guess, 0, -1):
        if diff_multis[i] > diff_max:
            start_index = i+1
            break
    # end index
    end_index = len(diff_multis)
    for i in range(start_index_guess, len(diff_multis)):
        if diff_multis[i] > diff_max:
            end_index = i+1
            break

    print(f"Group x: {start_index} -> {end_index}")
    group = sorted_ret[start_index:end_index]
    data["groups"].append(group)

    return end_index

def extract_groups(data):
    data["groups"] = []

    sorted_ret = np.sort(data['returns'])
    diff_multis = np.diff(sorted_ret)

    # Group 1
    group1_middle_guess = 0.05
    middle_index_guess = int(len(diff_multis) * group1_middle_guess)

    group1_diff_max = 4 * np.amax(diff_multis[middle_index_guess:middle_index_guess+int(len(diff_multis) * 0.015)])
    print(f"group1 max {group1_diff_max}")

    start_index = 1
    end_index = len(diff_multis)
    # search for start
    for i in range(middle_index_guess, 0, -1):
        if diff_multis[i] > group1_diff_max:
            start_index = i+1
            break
    for i in range(middle_index_guess, len(diff_multis)):
        if diff_multis[i] > group1_diff_max:
            end_index = i
            break

    print(f"Group 1: {start_index} -> {end_index}")
    group = sorted_ret[start_index:end_index]
    data["groups"].append(group)

    # Group 2
    # This group is actually three groups but they are difficult to resolve robustly
    # Start 5% from group 1 and search backwards
    start_index_guess = end_index + int(len(diff_multis) * 0.05)
    start_index = 0
    group_diff_max = group1_diff_max
    # search for start
    for i in range(start_index_guess, 0, -1):
        if diff_multis[i] > group_diff_max:
            start_index = i+1
            break
    # end index
    start_index_guess = int(len(diff_multis) * 0.6)
    end_index = len(diff_multis)
    for i in range(start_index_guess, len(diff_multis)):
        if diff_multis[i] > group_diff_max:
            end_index = i+1
            break

    print(f"Group 2: {start_index} -> {end_index}")
    group = sorted_ret[start_index:end_index]
    data["groups"].append(group)

    end_index = extract_simple_group(data, end_index, step=0.05)
    end_index = extract_simple_group(data, end_index, step=0.03)
    end_index = extract_simple_group(data, end_index, step=0.01)
    end_index = extract_simple_group(data, end_index, step=0.005)

def plot_multi_groups(data, data2):
    sorted_ret = np.sort(data['returns'])
    diff_multis = np.diff(sorted_ret)
    xvec = np.linspace(0, 1, num=len(data['returns']))

    fig, axs = plt.subplots(2, 1)

    axs[0].set_xlabel("Kills")
    axs[0].set_ylabel("Loot (multiplier)")
    axs[0].plot(xvec, sorted_ret)
    axs[0].grid()

    axs[1].set_xlabel("Kills")
    axs[1].set_ylabel("Loot (multiplier)")
    axs[1].plot(xvec[:-1], diff_multis)
    axs[1].grid()

    if data2:
        sorted_ret2 = np.sort(data2['returns'])
        diff_multis2 = np.diff(sorted_ret2)
        xvec2 = np.linspace(0, 1, num=len(data2['returns']))
        axs[0].plot(xvec2, sorted_ret2)
        axs[1].plot(xvec2[:-1], diff_multis2)

    plt.draw()

    # Plot some things
    fig, axs = plt.subplots(3, 2)

    if data2:
        fig.suptitle(f"Blue: {data['meta-data']['weapon']}/{data['meta-data']['mob']}" +
                     f" ({data['meta-data']['efficiency']}%/{data['meta-data']['looter']})" +
                     f" vs Orange: {data2['meta-data']['weapon']}/{data2['meta-data']['mob']}" + 
                     f" ({data2['meta-data']['efficiency']}%/{data2['meta-data']['looter']})")
    else:
        fig.suptitle(f"")

    extract_groups(data)

    if data2:
        extract_groups(data2)

    def plot_group(ax, data, data2, group):
        ax.set_xlabel("Kills")
        ax.set_ylabel("Loot (multiplier)")
        ax.plot(np.linspace(0, 1, num=len(data["groups"][group])), data["groups"][group])
        ax.set_xlabel(f"G1, Kills {len(data['groups'][group])}, {len(data['groups'][group]) / len(data['loots']) * 100:.2f}% of total")
        if data2:
            ax.plot(np.linspace(0, 1, num=len(data2["groups"][group])), data2["groups"][group])
        ax.grid()

    plot_group(axs[0, 0], data, data2, 0)
    plot_group(axs[0, 1], data, data2, 1)
    plot_group(axs[1, 0], data, data2, 2)
    plot_group(axs[1, 1], data, data2, 3)
    plot_group(axs[2, 0], data, data2, 4)
    plot_group(axs[2, 1], data, data2, 5)

    plt.show()

def main():
    parser = argparse.ArgumentParser(
        description='Analyze individual loot events from log and aggregate data')
    parser.add_argument('--files', '-f', default=None, type=argparse.FileType('r'),
                        help='chat.log', required=True, nargs='+')
    parser.add_argument('--cost', '-c', default=0, type=float,
                        help='Cost per shot (PEC)')
    parser.add_argument('--files-compare', '-f2', default=None, type=argparse.FileType('r'),
                        help='chat.log', nargs='+')
    parser.add_argument('--cost-compare', '-c2', default=0, type=float,
                        help='Cost per shot (PEC)')
    parser.add_argument('--remove-shrap', '-s', action='store_true',
                        help='Remove bonus shrapnel from returns')
    parser.add_argument('--write-csv', '-csv', action='store_true',
                        help='Write parsed output as a csv (will be written to loot.csv)')
    parser.add_argument('--plot-data', '-p', action='store_true',
                        help='Plot overview')
    parser.add_argument('--plot-groups', '-pg', action='store_true',
                        help='Plot grouping data')
    parser.add_argument('--normalize', '-n', action='store_true',
                        help='Normalize all data to 100 eff, 100 looter')

    args = parser.parse_args()

    data = get_data(args.files, args.cost, args.remove_shrap, args.normalize)

    if args.write_csv:
        with open('loot.csv', 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'cost', 'return', 'multi']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(data['loots'])):
                writer.writerow({'timestamp': data['timestamps'][i], 'cost': data['costs']
                                 [i], 'return': data['loots'][i], 'multi': data['returns'][i]})

    print_summary(data)

    data2 = None
    if args.files_compare:
        data2 = get_data(args.files_compare, args.cost_compare, args.remove_shrap, args.normalize)
        print_summary(data2)

    if args.plot_data:
        plot_data(data, data2)
    if args.plot_groups:
        plot_multi_groups(data, data2)

if __name__ == "__main__":
    main()
