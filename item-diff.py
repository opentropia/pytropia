#!/usr/bin/env python3

import argparse
import json
import re
import sys

from tabulate import tabulate

# The json format from
#  https://account.entropiauniverse.com/account/my-account/my-items/json.xml
# looks like this:
"""
{
"itemlist": [
    {
        "id": "1",
        "n": "A&amp;P Series Mayhem LP-100, Modified (L)",
        "q": "1",
        "v": "139.47",
        "c": "STORAGE (Calypso)"
    },
    {
        "id": "2",
        "n": "A-3 Punisher Mk. 1",
        "q": "1",
        "v": "30.00",
        "c": "STORAGE (Calypso)"
    }
]
}
"""

# "id": Identifer, example: "119"
# "n": Name, example: "Gremlin Shin Guards (F)"
# "q": Quantity: "1"
# "v": Value: "73.40"
# "c": Container: "CARRIED"

# container:
#   AUCTION
#   CARRIED
#   STORAGE ({PLANET})
#   {ITEM_NAME} ({ITEM_ID})
# What about Shops/Apartments?

# Resolve "container" to base location (like amp -> gun -> carried)


def resolve_container(item, items):
    # Find container by id enclosed in parenthesis. Like "foo (12)".
    result = re.match(r'.*\(([0-9]+)\)', item['c'])

    # Base case
    if result == None:
        return

    if result:
        #print(f"Resolving '{item['n']}' to '{items[result.group(1)]['c']}'")
        item['c'] = items[result.group(1)]['c']
        # Recursion
        resolve_container(item, items)


def get_item_values(file, container_filter):
    id_dict = {}

    with open(file) as json_file:
        data = json.load(json_file)
        for item in data['itemlist']:
            id_dict[item['id']] = item

    for id, item in id_dict.items():
        resolve_container(item, id_dict)

    # Filter based on container (like carried, storage, auction)
    if container_filter:
        id_dict = dict(filter(lambda elem: container_filter.lower()
                              in elem[1]['c'].lower(), id_dict.items()))

    name_dict = {}

    # Merge all things with the same name, add together PED value and quantity
    for id, item in id_dict.items():
        prev_value = name_dict.get(item['n'], (0, 0))
        name_dict[item['n']] = (
            float(item['v']) + prev_value[0], float(item['q']) + prev_value[1])

    return name_dict


def main():
    parser = argparse.ArgumentParser(
        description='Compare two item dumps')
    parser.add_argument('--file-start', '-a', default=None, type=argparse.FileType('r'),
                        help='Start items json', required=True)
    parser.add_argument('--file-end', '-b', default=None, type=argparse.FileType('r'),
                        help='End items json', required=True)
    parser.add_argument('--container-filter', '-f',
                        default="carried", help='Filter based on container type')
    parser.add_argument('--mark-up', '-m', default=None, type=argparse.FileType('r'),
                        help='File with markup values. If this is provided MU in/out will also be calculated')

    args = parser.parse_args()

    item_values_start = get_item_values(
        args.file_start.name, args.container_filter)
    item_values_end = get_item_values(
        args.file_end.name, args.container_filter)

    mu_data = {}
    if args.mark_up:
        with open(args.mark_up.name) as mu_json_file:
            mu_data = json.load(mu_json_file)

    total_mu_pos = 0
    total_mu_neg = 0

    # Diff ped value for each item type
    all_keys = set(item_values_start.keys() | item_values_end.keys())
    cost = 0.000000001
    ret = 0.000000001
    item_diff = {}
    for key in all_keys:
        diff_ped = item_values_end.get( 
            key, (0, 0))[0] - item_values_start.get(key, (0, 0))[0]
        diff_quantity = item_values_end.get(
            key, (0, 0))[1] - item_values_start.get(key, (0, 0))[1]

        if diff_ped < 0:
            cost += abs(diff_ped)
        else:
            ret += diff_ped

        if abs(diff_ped) > sys.float_info.epsilon or abs(diff_quantity) > 0:
            markup = 0
            if key in mu_data:
                if "percent" in mu_data[key]:
                    markup = diff_ped * (mu_data[key]["percent"] / 100 - 1)
                elif "ped" in mu_data[key]:
                    markup = diff_quantity * mu_data[key]["ped"]
                elif "other-percent" in mu_data[key]:
                    markup = diff_ped * (mu_data[mu_data[key]["other-percent"]]["percent"] / 100 - 1)

            if diff_quantity < 0 or diff_ped < 0:
                total_mu_neg += abs(markup)
            else:
                total_mu_pos += abs(markup)

            item_diff[key] = [diff_ped, int(diff_quantity), markup]

    mu_delta = total_mu_pos - total_mu_neg

    if len(item_diff) == 0:
        print("No differences found!")
        return 0

    results_expense = []
    results_gained = []
    # Print diff sorted on ped value
    for key, item in sorted(item_diff.items(), key=lambda x: x[1][0], reverse=True):
        if item[1] > 0:
            results_gained.append([key] + item)
        else:
            results_expense.append([key] + item)

    results_expense.append(["[Sum]", cost, 0, total_mu_neg])
    results_gained.append(["[Sum]", ret, 0, total_mu_pos])

    print(tabulate(results_expense, headers=['Expenses', 'PED', 'Count', 'Markup'], floatfmt=".2f"))
    print()
    print(tabulate(results_gained, headers=['Loot', 'PED', 'Count', 'Markup'], floatfmt=".2f"))

    print('\nMarkup')
    print(tabulate([[total_mu_pos, total_mu_neg, mu_delta, (mu_delta / cost) *100]], headers=['Gained', 'Lost', 'Delta', 'Delta (%)'], floatfmt=".2f"))

    print('\nSummary')
    print(tabulate([[cost, ret, ret - cost, (ret / cost) *100, ret - cost + mu_delta, ((ret+mu_delta) / cost) * 100]],
         headers=['Cost', 'Return', 'Delta', 'Delta (%)', 'Delta MU', 'Delta MU (%)'], floatfmt=".2f"))

    # TODO: Group cost based on things like Shrapnel, Ammo, Weapons, Tools, FAP, Armor and so on.


if __name__ == "__main__":
    main()
