#!/usr/bin/env python3

import argparse
import json
import re
import sys

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

    args = parser.parse_args()

    item_values_start = get_item_values(
        args.file_start.name, args.container_filter)
    item_values_end = get_item_values(
        args.file_end.name, args.container_filter)

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
            item_diff[key] = (diff_ped, int(diff_quantity))

    if len(item_diff) == 0:
        print("No differences found!")
        return 0

    # Print diff sorted on ped value
    for key, item in sorted(item_diff.items(), key=lambda x: x[1][0], reverse=True):
        print(f"{key}: {item[0]:.2f} PED ({item[1]})")

    print(f"\nCost, Return, Delta")
    print(f"{cost:.2f}  {ret:.2f}  {ret - cost:.2f}  {(ret / cost) * 100:.2f}%")

    # TODO: Group cost based on things like Shrapnel, Ammo, Weapons, Tools, FAP, Armor and so on.


if __name__ == "__main__":
    main()
