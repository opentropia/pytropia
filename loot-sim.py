#!/usr/bin/env python3

import numpy as np
import random
from matplotlib import pyplot as plt
from sklearn import multiclass 

efficiency = 80
looter = 50

cost_per_mob = 1.00 # PED
cost_randomness = 0.10 # The randomness of a kill cost, 0.05 = +-5%
num_mobs = 10000

bonus_shrap_prop = 0.1
bonus_shrap_multi = 0.6
bonus_shrap_spread = 0.05

# Tuned for 93% TT from normal loot + 6% from bonus shrap. 99% total
loot_probabilities  = [0.100, 0.100, 0.250, 0.350, 0.120, 0.040, 0.020, 0.01, 0.0025, 0.0035, 0.002, 0.0018733, 0.00006, 0.00004, 0.00002, 0.0000067]
loot_multipliers    = [0.282, 0.376, 0.469, 0.525, 0.941, 1.883, 3.765, 7.53, 11.275, 15.045, 18.87, 33.5     , 150    , 250    , 700    , 1500]
loot_spreads        = [0.028, 0.038, 0.046, 0.099, 0.094, 0.188, 0.375, 0.75,  1.025,  1.495,  2.33, 10       ,  50    , 100    , 200    ,  500]

print_loots = False
plot_outcome = True

if len(loot_multipliers) != len(loot_probabilities) or len(loot_multipliers) != len(loot_spreads):
    print("lengths mismatch")
    exit(1)

props = sum(loot_probabilities)
print(f"prop sum = {props}")

if abs(props - 1) > 0.000001:
    print("prop must be 1")
    exit(1)

factor = 0.86 + 0.07 * (efficiency/100) + 0.07 * (looter/100)
avg_returns = 0
for bin in range(len(loot_probabilities)):
    avg_returns += loot_probabilities[bin] * loot_multipliers[bin]
avg_shrap = bonus_shrap_prop *bonus_shrap_multi
long_term_total_norm = (avg_shrap+avg_returns)*100
long_term_total = long_term_total_norm * factor
print(f"Long term return: {avg_returns*100:.2f}% + Bonus shrap: {avg_shrap*100:.2f}%, Total: {long_term_total_norm:.2f}%")
print(f"Returns with factor: {factor:.4f} from looter {looter} and eff {efficiency}%: {long_term_total:.2f}%")

print("Multipliers:")
print(loot_multipliers)
print("Probabilities:")
print(loot_probabilities)
print("Spreads")
print(loot_spreads)

loot_bins = np.cumsum(loot_probabilities)
print("Bins:")
print(loot_bins)

total_loot = 0
total_cost = 0

loots = np.zeros(num_mobs)
costs = np.zeros(num_mobs)

for kill in range(num_mobs):
    roll = random.random()
    for bin in range(len(loot_bins)):
        if roll <= loot_bins[bin]:
            multiplier = loot_multipliers[bin]
            spread = loot_spreads[bin]
            break

    # Multiplier with randomness
    multiplier = random.uniform(multiplier-spread, multiplier+spread)
    # Cost with randomness
    cost = cost_per_mob * (1 + random.uniform(-cost_randomness, cost_randomness))
    loot = cost * multiplier

    # Roll bonus shrap
    roll = random.random()
    if roll < bonus_shrap_prop:
        loot += cost * random.uniform(bonus_shrap_multi-bonus_shrap_spread, bonus_shrap_multi+bonus_shrap_spread)

    loot = loot * factor

    total_cost += cost
    total_loot += loot

    loots[kill] = loot
    costs[kill] = cost

    if print_loots:
        print(f"Total loot {total_loot:.0f}, Total cost {total_cost:.0f}, return {total_loot/total_cost:.2f}, Loot: {loot:.2f}" )

print(f"Total loot {total_loot:.0f}, Total cost {total_cost:.0f}, Delta {total_loot-total_cost:.0f} ({(total_loot/total_cost)*100:.2f}%)")

multis = []
for i in range(0, len(loots)):
    multis.append(loots[i]/costs[i])

if plot_outcome:
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"Eff: {efficiency}%, Looter: {looter}, Expected ret {long_term_total:.2f}% Cost/Mob {cost_per_mob:.2f}, Num Mobs {num_mobs}, Loot {total_loot:.0f}, Cost {total_cost:.0f}, Delta {total_loot-total_cost:.0f} ({(total_loot/total_cost)*100:.2f}%)")

    t = np.linspace(0, num_mobs, num_mobs)
    axs[0, 0].set_title("Loot over time")
    axs[0, 0].set_xlabel("Num kills")
    axs[0, 0].set_ylabel("Loot (PED)")
    axs[0, 0].plot(t, loots)
    axs[0, 0].grid()

    returns = np.cumsum(loots)
    axs[0, 1].set_title("Sorted Multis")
    axs[0, 1].set_xlabel("Kills")
    axs[0, 1].set_ylabel("Loot (Multiplier)")
    axs[0, 1].plot(np.sort(multis))
    axs[0, 1].grid()

    cost = np.cumsum(costs)
    delta = returns - cost
    axs[1, 0].set_title("Accumulated Delta")
    axs[1, 0].set_xlabel("Num kills")
    axs[1, 0].set_ylabel("Delta (PED)")
    axs[1, 0].plot(t, delta)
    axs[1, 0].grid()

    axs[1, 1].set_title("Accumulated Return (%)")
    axs[1, 1].set_xlabel("Num kills")
    axs[1, 1].set_ylabel("Return")
    axs[1, 1].plot(t, returns / cost)
    axs[1, 1].grid()

    plt.show()

