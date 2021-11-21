#!/usr/bin/env python3

import argparse
from os import times
import re
import time
import datetime

import numpy as np
from matplotlib import pyplot as plt 

from logregex import *

def main():
    parser = argparse.ArgumentParser(
        description='Analyze individual loot events from log and aggregate data')
    parser.add_argument('--file', '-f', default=None, type=argparse.FileType('r'),
                        help='chat.log', required=True)
    parser.add_argument('--cost', '-c', default=None, type=float,
                        help='Cost per shot (PEC)', required=True)

    args = parser.parse_args()

    ped_per_shot = args.cost / 100

    # TODO: take as argument
    last_message = 'cost'

    # cost
    # BP-20 FEN: 6.984
    # Rubio: 0.738
    loots = []
    costs = []
    returns = []
    timestamps = []

    first_timestamp = -1

    with open(args.file.name, "r", encoding="utf8") as log:
        regex = re_base

        current_cost = 0.00000001
        current_loot = 0.00000001

        for line in log.readlines():
            result = re.match(regex, line)
            timestamp = time.mktime(datetime.datetime.strptime(result.group(1), "%Y-%m-%d %H:%M:%S").timetuple())

            if first_timestamp < 0:
                first_timestamp = timestamp

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

            # Target evade/dodge/miss
            result1 = re.match(re_sys_target_evade, message)
            result2 = re.match(re_sys_target_dodge, message)
            result3 = re.match(re_sys_target_jammed, message)
            result_hit = re.match(re_sys_you_inflict, message)
            result_miss = re.match(re_sys_you_missed, message)

            if result1 or result2 or result3 or result_hit or result_miss:
                if last_message == 'loot':
                    ret = (current_loot/current_cost)

                    # Ignore spurious data
                    if ret < 100000:
                        returns.append(ret)
                        loots.append(current_loot)
                        costs.append(current_cost)
                        # TODO: add option to use absolute time
                        timestamps.append(timestamp - first_timestamp)

                    #print(f"Loot: {ret*100:.2f}% - {current_cost:.4f} - {current_loot:.4f}")
                    current_loot = 0.0
                    current_cost = 0.0

                # TODO: how to treat misses?
                current_cost += ped_per_shot

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

                current_loot += value

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
    for i in range(0, len(loots)):
        multi = loots[i] / costs[i]
        if multi < g1:
            g1_cost += costs[i]
            g1_loot += loots[i]
        elif multi < g2:
            g2_cost += costs[i]
            g2_loot += loots[i]
        elif multi < g3:
            g3_cost += costs[i]
            g3_loot += loots[i]
        else:
            g4_cost += costs[i]
            g4_loot += loots[i]
        all_cost += costs[i]
        all_loot += loots[i]

    print(f"Num kills: {len(loots)}")
    print(f"Total loot {(all_loot/all_cost) * 100:.2f}% ({all_loot:.2f}/{all_cost:.2f})")
    print(f"G1 (0.0 - {g1}) returns: {(g1_loot/g1_cost) * 100:.2f}% - ({(g1_loot/all_loot) * 100:.2f}% of total returns)")
    print(f"G2 ({g1} - {g2}) returns: {(g2_loot/g2_cost) * 100:.2f}% - ({(g2_loot/all_loot) * 100:.2f}% of total returns)")
    print(f"G3 ({g2} - {g3})  returns: {(g3_loot/g3_cost) * 100:.2f}% - ({(g3_loot/all_loot) * 100:.2f}% of total returns)")
    print(f"G4 ({g3} - inf)  returns: {(g4_loot/g4_cost) * 100:.2f}% - ({(g4_loot/all_loot) * 100:.2f}% of total returns)")

    # Plot some things
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"TODO")

    axs[0, 0].set_title("Returns over time")
    axs[0, 0].set_xlabel("Time (s)")
    axs[0, 0].set_ylabel("Loot (multiplier)")
    axs[0, 0].plot(timestamps, returns)
    axs[0, 0].grid()

    #t = np.linspace(0, num_mobs, num_mobs)
    axs[1, 0].set_title("Returns sorted")
    axs[1, 0].set_xlabel("Kills")
    axs[1, 0].set_ylabel("Loot (multiplier)")
    axs[1, 0].plot(np.sort(returns))
    axs[1, 0].grid()

    axs[1, 1].set_title("Histogram (just a test)")
    axs[1, 1].hist(returns, bins=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], density='true')
    axs[1, 1].grid()


    # Look at spectrum to try to find any patters
    axs[0, 1].set_title("Magnitude Spectrum (just a test)")
    axs[0, 1].magnitude_spectrum(returns - np.mean(returns), Fs=1, color='C1')

    plt.show()

if __name__ == "__main__":
    main()
