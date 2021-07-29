#!/usr/bin/env python3

import numpy as np
import random
from matplotlib import pyplot as plt 

cost_per_mob = .10 # PED
cost_randomness = 0.10 # The randomness of a kill cost, 0.05 = +-5%
num_mobs = 120000

# First value will be calculated based on the other multipliers to
# satisfy that the total propability is 1 and long_term_return.
loot_multipliers   = [0.0, 0.8, 1  , 2   , 10   , 100   , 1000]
loot_probabilities = [0.0, 0.2, 0.1, 0.05, 0.01, 0.0005, 0.00001]

loot_randomness = 0.1 # The randomness of a loot instance, 0.5 = +-50%
                      # Applied after the multiplier has been chosen

# This is the long time return. 1 = 100%, 0.95 = 95% and so on.
long_term_return_tt = 0.95
long_term_return_mu = 0.05
long_term_return = long_term_return_tt + long_term_return_mu

print_loots = False
plot_outcome = True

if len(loot_multipliers) != len(loot_probabilities):
    print("lengths mismatch")
    exit(1)

# Derive first probability
first_prop = sum(loot_probabilities)

if first_prop >= 1:
    print("invalid loot_probabilities")
    exit(1)

loot_probabilities[0] = 1 - first_prop

# Derive first multiplier
return_left = long_term_return - sum([a * b for a, b in zip(loot_multipliers, loot_probabilities)])
loot_multipliers[0] = return_left / loot_probabilities[0]

if loot_multipliers[0] <= 0:
    print("invalid loot_multipliers")
    exit(1)

print("Multipliers:")
print(loot_multipliers)
print("Probabilities:")
print(loot_probabilities)

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
            break

    # Multiplier with randomness
    multiplier = multiplier * (1 + random.uniform(-loot_randomness, loot_randomness))
    # Cost with randomness
    cost = cost_per_mob * (1 + random.uniform(-cost_randomness, cost_randomness))
    loot = cost * multiplier
    total_cost += cost
    total_loot += loot

    loots[kill] = loot
    costs[kill] = cost

    if print_loots:
        print(f"Total loot {total_loot:.0f}, Total cost {total_cost:.0f}, return {total_loot/total_cost:.2f}, Loot: {loot:.2f}" )

print(f"Total loot {total_loot:.0f}, Total cost {total_cost:.0f}, Delta {total_loot-total_cost:.0f} ({(total_loot/total_cost)*100:.2f}%)")

if plot_outcome:
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"Long time return {long_term_return*100:.2f}%, Cost/Mob {cost_per_mob:.2f}, Num Mobs {num_mobs}, Loot {total_loot:.0f}, Cost {total_cost:.0f}, Delta {total_loot-total_cost:.0f} ({(total_loot/total_cost)*100:.2f}%)")

    t = np.linspace(0, num_mobs, num_mobs)
    axs[0, 0].set_title("Loot over time")
    axs[0, 0].set_xlabel("Num kills")
    axs[0, 0].set_ylabel("Loot (PED)")
    axs[0, 0].plot(t, loots)
    axs[0, 0].grid()

    returns = np.cumsum(loots)
    axs[0, 1].set_title("Accumulated Return")
    axs[0, 1].set_xlabel("Num kills")
    axs[0, 1].set_ylabel("Return (PED)")
    axs[0, 1].plot(t, returns)
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

