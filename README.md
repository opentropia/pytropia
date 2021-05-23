# pytropia

## Requirements

* Python 3.6 (or newer) (https://www.python.org/downloads/)

## Installation

Install python requirements with:
```
pip install -r requirements.txt
```

To use the skill scanner the tesseract executable needs to be installed separately.
Instructions can be found under "INSTALLATION" https://pypi.org/project/pytesseract/.

Pre-built binaries for Windows can be found here: https://github.com/UB-Mannheim/tesseract/wiki


## Tools

### item-diff

A tool that can compare two different files from:
https://account.entropiauniverse.com/account/my-account/my-items/json.xml

Can for example be used to evaluate the outcome from a hunt.

Example:  
`& ./item-diff.py -a hunt-start.json -b hunt-end.json --container-filter carried`
```
Shrapnel: 212.90 PED (2129036)
Animal Eye Oil: 132.75 PED (2655)
Wool: 9.40 PED (47)
Iron Stone: 8.58 PED (66)
...
Gremlin Arm Guards (F): -1.07 PED (0)
Gremlin Harness (F): -1.45 PED (0)
ArMatrix Extender P20 (L): -6.25 PED (0)
ArMatrix SB-20 (L): -24.88 PED (0)
Weapon Cells: -153.00 PED (-1530000)
Universal Ammo: -230.45 PED (-2304495)

Cost, Return, Delta
421.37  379.59  -41.78  90.08%
```

### aggregate-log

TODO: instructions on how to enable chat logging to file

Example:  
`./aggregate-log.py -f ~/Documents/Entropia\ Universe/chat.log`
```yaml
combat:
  target:
    critical-damage: 0
    critical-hits: 0
    critical-pierce: 0
    critical-pierce-damage: 0
    damage: 2725.7000
    dodges: 224
    evades: 0
    hits: 66
    misses: 71
  you:
    critical-damage: 10214.1000
    critical-hits: 40
    critical-reduced: 0
    critical-reduced-pierce: 0
    damage: 239145.6000
    deaths: 0
    deflects: 1
    dodges: 0
    evades: 8
    heal-points: 1501.9000
    heals: 48
    hits: 2171
    misses: 6
enhancers:
  Weapon Damage Enhancer 1: 1
  Weapon Damage Enhancer 2: 1
globals: {}
skills:
  Aim: 4.2504
  Anatomy: 3.3643
  ...
  Weapons Handling: 3.0724
  Wounding: 8.3571
team:
  avatars:
    Alli Golden:
      Animal Eye Oil: 78
      Animal Hide: 102
      Animal Muscle Oil: 100
      ...
      Soft Hide: 31
      Surface Hardener Component: 2
    Avatar 2:
      Animal Eye Oil: 42
      Animal Hide: 91
      Animal Muscle Oil: 330
      ...
      Shrapnel: 5121740
      Socket 3 Component: 1
      Soft Hide: 10
tiering: {}
```

### skill-scanner

TODO: instructions

Scan single file:  
`./skill-scanner.py -f skills.png`
```yaml
num-skills: 7
skills:
  Agility: 73.3023
  Aim: 3976.0078
  Alertness: 1928.0542
  Analysis: 121.4340
  Anatomy: 6446.6743
  Animal Lore: 36.6200
  Animal Taming: 21.1938
sum: 12603.2863
sum-int: 12601
total-skills: 119113
```

Semi auto mode:  
`./skill-scanner.py -w /c/ProgramData/entropia\ universe/public_users_data/screenshots/ --semi-auto 19 --remove | tee skills.yaml`

Press print screen 19 times. Result:

skills.yaml
```yaml
num-skills: 125
skills:
  Agility: 74.6278
  Aim: 4009.5580
  Alertness: 2153.8525
  Analysis: 123.0387
  Anatomy: 6496.9765
  ...
  Whip: 1.0000
  Wood Carving: 1.0000
  Wood Processing: 1.0000
  Wounding: 3963.4262
  Zoology: 237.5503
sum: 122249.0820
sum-int: 122205
total-skills: 122205
```

