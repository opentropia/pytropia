import re

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

## Base regex to extract: timestamp, channel, user and message
re_base = re.compile(r'(.*?) \[(.*?)\] \[(.*?)\] (.*)')

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
# Example: "The target Jammed your attack"
re_sys_target_jammed = re.compile(r'The target Jammed your attack')
# Example: "You took 5.5 points of damage"
re_sys_target_inflict = re.compile(r'You took (\d+\.\d+) points of damage')

## Team
# Example: "Alli Golden received Shrapnel (9373)"
re_team_loot = re.compile(r'(.*) received (.*) \((\d+)\)')
# Example: "Alli Golden received a Thunderbird Shin Guards (M,L)"
re_team_loot_single = re.compile(r'(.*) received a (.*)')
