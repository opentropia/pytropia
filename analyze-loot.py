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

def main():
    parser = argparse.ArgumentParser(
        description='Analyze individual loot events from log and aggregate data')
    parser.add_argument('--file', '-f', default=None, type=argparse.FileType('r'),
                        help='chat.log', required=True)
    parser.add_argument('--cost', '-c', default=None, type=float,
                        help='Cost per shot (PEC)', required=True)
    parser.add_argument('--remove-shrap', '-s', action='store_true',
                        help='Remove bonus shrapnel from returns')
    parser.add_argument('--write-csv', '-csv', action='store_true',
                        help='Write parsed output as a csv (will be written to loot.csv)')

    args = parser.parse_args()

    data = {}

    data['ped_per_shot'] = args.cost / 100
    data['bonus_shraps'] = []
    data['bonus_shraps_multis'] = []
    data['loots'] = []
    data['costs'] = []
    data['returns'] = []
    data['timestamps'] = []
    data['shots'] = 0

    parse_log(args.file.name, data)

    for i in range(len(data['loots'])):
        if args.remove_shrap:
            data['loots'][i] -= data['bonus_shraps'][i]

        multi = data['loots'][i] / data['costs'][i]
        data['returns'].append(multi)

        data['bonus_shraps_multis'].append(data['bonus_shraps'][i] / data['costs'][i])

    if args.write_csv:
        with open('loot.csv', 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'cost', 'return', 'multi']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(data['loots'])):
                writer.writerow({'timestamp': data['timestamps'][i], 'cost': data['costs']
                                 [i], 'return': data['loots'][i], 'multi': data['returns'][i]})

    # Subtract min timestamp for relative time from first loot
    min_timesamp = min(data['timestamps'])
    data['timestamps'] = [x - min_timesamp for x in data['timestamps']]


    # Analyze loot in four groups
    all_loot = 0.0
    all_cost = 0.0
    g1 = 0.6
    g1_cost = 0.00000001
    g1_loot = 0.00000001
    g2 = 2
    g2_cost = 0.00000001
    g2_loot = 0.00000001
    g3 = 5
    g3_cost = 0.00000001
    g3_loot = 0.00000001
    g4 = 100000
    g4_cost = 0.00000001
    g4_loot = 0.00000001
    for i in range(0, len(data['loots'])):
        multi = data['loots'][i] / data['costs'][i]
        if multi < g1:
            g1_cost += data['costs'][i]
            g1_loot += data['loots'][i]
        elif multi < g2:
            g2_cost += data['costs'][i]
            g2_loot += data['loots'][i]
        elif multi < g3:
            g3_cost += data['costs'][i]
            g3_loot += data['loots'][i]
        else:
            g4_cost += data['costs'][i]
            g4_loot += data['loots'][i]
        all_cost += data['costs'][i]
        all_loot += data['loots'][i]

    print(f"\nNum kills: {len(data['loots'])}")
    print(f"Shots: {data['shots']}")
    print(f"Total loot {(all_loot/all_cost) * 100:.2f}% ({all_loot:.2f}/{all_cost:.2f})")
    print(f"Total bonus shrap {np.sum(data['bonus_shraps']):.2f} ({np.sum(data['bonus_shraps'])/all_cost * 100:.2f}%)")
    print(f"G1 (0.0 - {g1}) returns: {(g1_loot/g1_cost) * 100:.2f}% - ({(g1_loot/all_cost) * 100:.2f}% of total cost)")
    print(f"G2 ({g1} - {g2}) returns: {(g2_loot/g2_cost) * 100:.2f}% - ({(g2_loot/all_cost) * 100:.2f}% of total cost)")
    print(f"G3 ({g2} - {g3})  returns: {(g3_loot/g3_cost) * 100:.2f}% - ({(g3_loot/all_cost) * 100:.2f}% of total cost)")
    print(f"G4 ({g3} - inf)  returns: {(g4_loot/g4_cost) * 100:.2f}% - ({(g4_loot/all_cost) * 100:.2f}% of total cost)")
    print("")
    print(f"G1 (0.0 - {g1}) returns: {(g1_loot/all_cost) * 100:.2f}%")
    print(f"G2 (0.0 - {g2}) returns: {((g1_loot+g2_loot)/all_cost) * 100:.2f}%")
    print(f"G3 (0.0 - {g3}) returns: {((g1_loot+g2_loot+g3_loot)/all_cost) * 100:.2f}%")
    print(f"G4 (0.0 - inf)  returns: {((g1_loot+g2_loot+g3_loot+g4_loot)/all_cost) * 100:.2f}%")

    # Analyze bottom
    remove_bottom_n = 2
    bottom_procent = 2
    num_samples = int(math.ceil(len(data['returns']) * (bottom_procent / 100)))
    sorted_returns = np.sort(data['returns'])
    print(f"\nBottom {bottom_procent}% multis:")
    for i in range(remove_bottom_n, num_samples):
        print(sorted_returns[i])

    print(f"Average ({num_samples}): {np.sum(sorted_returns[remove_bottom_n:num_samples+remove_bottom_n] / num_samples)}")
    print(f"Average (5): {np.sum(sorted_returns[remove_bottom_n:5+remove_bottom_n] / 5)}")

    # Plot some things
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"TODO")

    axs[0, 0].set_title("Returns over time")
    axs[0, 0].set_xlabel("Time (s)")
    axs[0, 0].set_ylabel("Loot (multiplier)")
    axs[0, 0].set_ylim([0, 80])
    axs[0, 0].plot(data['timestamps'], data['returns'])
    axs[0, 0].grid()

    #t = np.linspace(0, num_mobs, num_mobs)
    axs[1, 0].set_title("Returns sorted")
    axs[1, 0].set_xlabel("Kills")
    axs[1, 0].set_ylabel("Loot (multiplier)")
    axs[1, 0].plot(np.sort(data['returns']))
    axs[1, 0].grid()

    #axs[1, 1].set_title("Histogram (just a test)")
    #axs[1, 1].hist(returns, bins=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], density='true')
    #axs[1, 1].grid()


    # Plot bonus shraps
    axs[0, 1].set_title("Bonus shrap multis")
    axs[0, 1].plot(data['timestamps'], data['bonus_shraps_multis'])
    axs[0, 1].set_ylabel("Multiplier")
    axs[0, 0].set_xlabel("Time (s)")
    axs[0, 1].grid()

    axs[1, 1].set_title("Bonus shrap sorted")
    axs[1, 1].set_xlabel("Kills")
    axs[1, 1].set_ylabel("Multiplier")
    axs[1, 1].plot(np.sort(data['bonus_shraps_multis']))
    axs[1, 1].grid()

    plt.show()

if __name__ == "__main__":
    main()
