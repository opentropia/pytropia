#!/usr/bin/env python3

import argparse
from os import times
import re
import time
import datetime
import csv
import math

import numpy as np
from matplotlib import pyplot as plt 

from logregex import *

# TODO: Ignore list:
# Fruit: 
# Stones: Kaldon
# Universal Ammo

def parse_log(file_name, data):
    last_message = 'cost'
    shots_current = 0
    num_shrap = 0
    bonus_shrap = 0

    with open(file_name, "r", encoding="utf8") as log:
        regex = re_base

        current_cost = 0.00000001
        current_loot = 0.00000001
        for line in log.readlines():
            result = re.match(regex, line)
            timestamp = time.mktime(datetime.datetime.strptime(result.group(1), "%Y-%m-%d %H:%M:%S").timetuple())

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

                # Special handling to calculate value of Shrapnel since
                # to avoid rounding errors.
                if item == "Shrapnel":
                    value = count / 10000

                    if num_shrap == 1:
                        bonus_shrap = value

                    num_shrap += 1

                # Don't count universal ammo
                if item != "Universal Ammo":
                    current_loot += value


def get_data(files, cost_per_shot, remove_shrap):
    data = {}

    data['ped_per_shot'] = cost_per_shot / 100
    data['bonus_shraps'] = []
    data['bonus_shraps_multis'] = []
    data['loots'] = []
    data['costs'] = []
    data['returns'] = []
    data['timestamps'] = []
    data['shots'] = 0

    for f in files:
        parse_log(f.name, data)

    for i in range(len(data['loots'])):
        if remove_shrap:
            data['loots'][i] -= data['bonus_shraps'][i]

        multi = data['loots'][i] / data['costs'][i]
        data['returns'].append(multi)

        data['bonus_shraps_multis'].append(data['bonus_shraps'][i] / data['costs'][i])

    # Subtract min timestamp for relative time from first loot
    min_timesamp = min(data['timestamps'])
    data['timestamps'] = [x - min_timesamp for x in data['timestamps']]

    return data

def print_summary(data):
    all_cost = 0
    all_loot = 0
    for i in range(0, len(data['loots'])):
        all_cost += data['costs'][i]
        all_loot += data['loots'][i]

    print(f"\nNum kills: {len(data['loots'])}")
    print(f"Shots: {data['shots']}")
    print(f"Total loot {(all_loot/all_cost) * 100:.2f}% ({all_loot:.2f}/{all_cost:.2f})")
    print(f"Total bonus shrap {np.sum(data['bonus_shraps']):.2f} ({np.sum(data['bonus_shraps'])/all_cost * 100:.2f}%)")

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

    axs[0, 0].set_title("Returns over time")
    axs[0, 0].set_xlabel("Time (s)")
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


    # Plot bonus shraps
    axs[0, 1].set_title("Bonus shrap multis")
    axs[0, 1].plot(data['timestamps'], data['bonus_shraps_multis'])
    if data2:
        axs[0, 1].plot(data2['timestamps'], data2['bonus_shraps_multis'])
    axs[0, 1].set_ylabel("Multiplier")
    axs[0, 1].set_xlabel("Time (s)")
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

def main():
    parser = argparse.ArgumentParser(
        description='Analyze individual loot events from log and aggregate data')
    parser.add_argument('--files', '-f', default=None, type=argparse.FileType('r'),
                        help='chat.log', required=True, nargs='+')
    parser.add_argument('--cost', '-c', default=None, type=float,
                        help='Cost per shot (PEC)', required=True)
    parser.add_argument('--files-compare', '-f2', default=None, type=argparse.FileType('r'),
                        help='chat.log', nargs='+')
    parser.add_argument('--cost-compare', '-c2', default=None, type=float,
                        help='Cost per shot (PEC)')
    parser.add_argument('--remove-shrap', '-s', action='store_true',
                        help='Remove bonus shrapnel from returns')
    parser.add_argument('--write-csv', '-csv', action='store_true',
                        help='Write parsed output as a csv (will be written to loot.csv)')

    args = parser.parse_args()

    data = get_data(args.files, args.cost, args.remove_shrap)

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
        data2 = get_data(args.files_compare, args.cost_compare, args.remove_shrap)
        print_summary(data2)


    plot_data(data, data2)

if __name__ == "__main__":
    main()
