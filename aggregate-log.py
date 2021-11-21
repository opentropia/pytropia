#!/usr/bin/env python3

import argparse
import re

import yaml


def float_representer(dumper, value):
    text = '{0:.4f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)
yaml.add_representer(float, float_representer)


# [System]
# Your ArMatrix LP-50 (L) has reached tier 2.24
# TODO: Jamming?

# [Team]
# Alli Golden received Shrapnel (9373)
# Alli Golden was killed
# Alli Golden was revived

# [Globals]
# Harry Hoob Hoobler killed a creature (Marcimex Devastator) with a value of 139 PED!
# Walen Wale Thor constructed an item (Explosive Projectiles) worth 173 PED!
# Mal Marshmellow Darkwater has found a rare item (Aeglic Ring, Adjusted) with a value of 10 PED! A record has been added to the Hall of Fame!
# Chaz THE JAZZ DeHetre killed a creature (Hogglo Guardian) with a value of 847 PED! A record has been added to the Hall of Fame!
# examined Treasure Chest in
# examined Mysterious Crate in
# has found a rare item
# examined Safe in

### System

# TODO:
### Your current position is (/pos)
### [Local] [Alli Golden]: [Calypso, 64109, 77782, 109, Waypoint]
### unreachable
### Left chat region?
### Entered chat region?
### has logged in
### item set effect 
### [System]: You took 10.9 points of damage
### You have claimed a resource! (Caldorite Stone)
### This resource is depleted
### Picked up Pappylon (77)
### The transaction was completed successfully
### Item(s) repaired successfully
### The Warchief's Sanctuary has been challenged!
### Typhon's Reach has been challenged!
### Robot forces have launched an attack on Fort Lahar at [Calypso, 67005, 74847, 202, Waypoint]

## You
# Example: "You healed yourself 42.0 points"
re_sys_you_heal = re.compile(r'You healed yourself (\d+\.\d+) points')
# Example: "You inflicted 127.9 points of damage"
re_sys_you_inflict = re.compile(r'You inflicted (\d+\.\d+) points of damage')
# Example: "You inflicted 127.9 points of damage"
re_sys_you_crit = re.compile(
    r'Critical hit - Additional damage! You inflicted (\d+\.\d+) points of damage')
# Example: "You have gained 0.0310 experience in your Laser Weaponry Technology skill"
re_sys_skill_1 = re.compile(
    r'You have gained (\d+\.\d+) experience in your (.*) skill')
# Example: "You have gained 0.2739 Serendipity"
re_sys_skill_2 = re.compile(r'You have gained (\d+\.\d+) (.*)')
# Example "You Evaded the attack"
re_sys_you_evade = re.compile(r'You Evaded the attack')
# Example "You Dodged the attack"
re_sys_you_dodge = re.compile(r'You Dodged the attack')
# Example "You missed"
re_sys_you_missed = re.compile(r'You missed')
# Example "Damage deflected"
re_sys_you_deflect = re.compile(r'Damage deflected!')
# Example "You were killed by the unrelenting Vanguard Coordinator
re_sys_you_deaths = re.compile(r'You were killed by the ([^\s]+) (.*)')
# Example "Reduced 4.8 points of armor piercing damage"
re_sys_you_reduced_pierce = re.compile(
    r'Reduced (\d+\.\d+) points of armor piercing damage')
# Example "Reduced 5.2 points of critical damage"
re_sys_you_reduced_crit = re.compile(
    r'Reduced (\d+\.\d+) points of critical damage')
## Loot
re_loot = re.compile(r'You received (.*) x \((\d+)\) Value: (\d+\.\d+) PED')

## Enhancers)
# Example: "Your enhancer Weapon Damage Enhancer 1 on your ArMatrix LP-50 (L) broke. You have 18 enhancers remaining on the item. You received 0.8000 PED Shrapnel."
re_sys_enhancer = re.compile(
    r'Your enhancer (.*) on your (.*) broke. You have (\d+) enhancers remaining on the item. You received (\d+\.\d+) PED Shrapnel.')


## Target
# Example: "Critical hit - Armor penetration! You took 48.1 points of damage"
re_sys_target_pierce = re.compile(
    r'Critical hit - Armor penetration! You took (\d+\.\d+) points of damage')
# Example: "Critical hit - Additional damage! You took 131.7 points of damage"
re_sys_target_crit = re.compile(
    r'Critical hit - Additional damage! You took (\d+\.\d+) points of damage')
# Example: "The attack missed you"
re_sys_target_missed = re.compile(r'The attack missed you')
# Example: "The target Evaded your attack"
re_sys_target_evade = re.compile(r'The target Evaded your attack')
# Example: "The target Dodged your attack"
re_sys_target_dodge = re.compile(r'The target Dodged your attack')
# Example: "You took 5.5 points of damage"
re_sys_target_inflict = re.compile(r'You took (\d+\.\d+) points of damage')

## Team
# Example: "Alli Golden received Shrapnel (9373)"
re_team_loot = re.compile(r'(.*) received (.*) \((\d+)\)')
# Example: "Alli Golden received a Thunderbird Shin Guards (M,L)"
re_team_loot_single = re.compile(r'(.*) received a (.*)')


def handle_system(data, message):
    # Skills
    result = re.match(re_sys_skill_1, message)
    if not result:
        skill_result = re.match(re_sys_skill_2, message)

    if result:
        skill_points = result.group(1)
        skill_name = result.group(2)
        #print(f"Skill: {skill_name}: {skill_points}")
        data['skills'][skill_name] = data['skills'].get(
            skill_name, 0) + float(skill_points)
        return

    # Combat "you"
    result = re.match(re_sys_you_inflict, message)
    if result:
        data['combat']['you']['hits'] += 1
        data['combat']['you']['damage'] += float(result.group(1))
        return

    result = re.match(re_sys_you_crit, message)
    if result:
        data['combat']['you']['critical-hits'] += 1
        data['combat']['you']['critical-damage'] += float(result.group(1))
        return

    result = re.match(re_sys_you_heal, message)
    if result:
        data['combat']['you']['heals'] += 1
        data['combat']['you']['heal-points'] += float(result.group(1))
        return

    result = re.match(re_sys_you_evade, message)
    if result:
        data['combat']['you']['evades'] += 1
        return

    result = re.match(re_sys_you_dodge, message)
    if result:
        data['combat']['you']['dodges'] += 1
        return

    result = re.match(re_sys_you_missed, message)
    if result:
        data['combat']['you']['misses'] += 1
        return

    result = re.match(re_sys_you_deflect, message)
    if result:
        data['combat']['you']['deflects'] += 1
        return

    result = re.match(re_sys_you_deaths, message)
    if result:
        #print(f"Killed by: {result.group(2)} ({result.group(1)})")
        data['combat']['you']['deaths'] += 1
        return

    result = re.match(re_sys_you_reduced_crit, message)
    if result:
        data['combat']['you']['critical-reduced'] += float(result.group(1))
        return

    result = re.match(re_sys_you_reduced_pierce, message)
    if result:
        data['combat']['you']['critical-reduced-pierce'] += float(
            result.group(1))
        return

    # Combat "target"
    result = re.match(re_sys_target_inflict, message)
    if result:
        data['combat']['target']['hits'] += 1
        data['combat']['target']['damage'] += float(result.group(1))
        return

    result = re.match(re_sys_target_missed, message)
    if result:
        data['combat']['target']['misses'] += 1
        return

    result = re.match(re_sys_target_evade, message)
    if result:
        data['combat']['target']['evades'] += 1
        return

    result = re.match(re_sys_target_dodge, message)
    if result:
        data['combat']['target']['dodges'] += 1
        return

    result = re.match(re_sys_target_crit, message)
    if result:
        data['combat']['target']['critical-hits'] += 1
        data['combat']['target']['critical-damage'] += float(result.group(1))
        return

    result = re.match(re_sys_target_pierce, message)
    if result:
        data['combat']['target']['critical-pierce'] += 1
        data['combat']['target']['critical-pierce-damage'] += float(
            result.group(1))
        return

    # Enhancer
    result = re.match(re_sys_enhancer, message)
    if result:
        enhancer = result.group(1)
        item = result.group(2)
        left = result.group(3)
        tt = result.group(4)
        data['enhancers'][enhancer] = data['enhancers'].get(enhancer, 0) + 1
        return

    # Loot
    result = re.match(re_loot, message)
    if result:
        item = result.group(1)
        count = int(result.group(2))
        value = float(result.group(3))

        # Special handling to calculate value of Shrapnel since
        # to avoid rounding errors.
        if item == "Shrapnel":
            value = count / 10000

        if item not in data['loot']['items']:
            data['loot']['items'][item] = {}
            data['loot']['items'][item]['count'] = 0
            data['loot']['items'][item]['value'] = 0.0

        data['loot']['items'][item]['value'] += value
        data['loot']['items'][item]['count'] += count

        data['loot']['total'] += value

    return


def handle_team(data, message):
    # Team

    # First match multpile items
    result = re.match(re_team_loot, message)
    # Then single item
    if result:
        count = result.group(3)
    else:
        count = 1
        result = re.match(re_team_loot_single, message)

    if result:
        avatar = result.group(1)
        if avatar not in data['team']['avatars']:
            data['team']['avatars'][avatar] = {}
        item = result.group(2)
            
        data['team']['avatars'][avatar][item] = \
            data['team']['avatars'][avatar].get(item, 0) + int(count)
        #print(f"{avatar} {item} {count}")
        return

def main():
    parser = argparse.ArgumentParser(
        description='Aggregate information from chat log')
    parser.add_argument('--file', '-f', default=None, type=argparse.FileType('r'),
                        help='chat.log', required=True)

    args = parser.parse_args()

    # TODO: Add options for what to parse (skills/team/combat/etc)
    # TODO: Add ranges, like from/to timestamp, last 1 hour and so on

    data = {}
    data['skills'] = {}
    data['team'] = {}
    data['team']['avatars'] = {}
    data['combat'] = {}
    data['enhancers'] = {}
    data['tiering'] = {}
    data['globals'] = {}
    data['loot'] = {}
    data['loot']['items'] = {}
    data['loot']['total'] = 0.0

    data['combat']['you'] = {}
    data['combat']['you']['heals'] = 0
    data['combat']['you']['heal-points'] = 0
    data['combat']['you']['hits'] = 0
    data['combat']['you']['critical-hits'] = 0
    data['combat']['you']['critical-damage'] = 0
    data['combat']['you']['misses'] = 0
    data['combat']['you']['evades'] = 0
    data['combat']['you']['dodges'] = 0
    data['combat']['you']['deflects'] = 0
    data['combat']['you']['damage'] = 0
    data['combat']['you']['critical-reduced'] = 0
    data['combat']['you']['critical-reduced-pierce'] = 0
    data['combat']['you']['deaths'] = 0

    data['combat']['target'] = {}
    data['combat']['target']['hits'] = 0
    data['combat']['target']['evades'] = 0
    data['combat']['target']['dodges'] = 0
    data['combat']['target']['critical-hits'] = 0
    data['combat']['target']['critical-damage'] = 0
    data['combat']['target']['critical-pierce'] = 0
    data['combat']['target']['critical-pierce-damage'] = 0
    data['combat']['target']['misses'] = 0
    data['combat']['target']['damage'] = 0

    with open(args.file.name, "r", encoding="utf8") as log:
        regex = re.compile(r'(.*?) \[(.*?)\] \[(.*?)\] (.*)')

        for line in log.readlines():
            result = re.match(regex, line)
            time_stamp = result.group(1)
            channel = result.group(2)
            user = result.group(3)
            message = result.group(4)

            if channel == "System":
                #print(f"{message}")
                handle_system(data, message)
            elif channel == "Team":
                #print(f"{message}")
                handle_team(data, message)


    print(yaml.dump(data))

if __name__ == "__main__":
    main()
