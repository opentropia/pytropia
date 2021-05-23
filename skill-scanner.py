#!/usr/bin/env python3

from __future__ import print_function

import argparse
import math
import os
import signal
import sys
import time

import pyautogui
import yaml
from PIL.Image import EXTENT
from screeninfo import get_monitors
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import pytropia

# This somehow automagically fixes so that multi monitor support works as
# expected when monitors get negative coordinates.
for m in get_monitors():
    pass
    #print(str(m))

REMOVE_SKILLS = ["Promoter Rating", "Reputation"]


def float_representer(dumper, value):
    text = '{0:.4f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)


yaml.add_representer(float, float_representer)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


DONE = False


def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Done')
    global DONE
    DONE = True


class ImagesEventHandler(FileSystemEventHandler):
    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.skills = {}
        self.files = []

    def on_created(self, event):
        self.files.append(event.src_path)

    def queue_len(self):
        return len(self.files)

    def get_file(self):
        if len(self.files) == 0:
            return None

        return self.files.pop()


def main():
    parser = argparse.ArgumentParser(
        description='Scan skill points. TODO: more')
    parser.add_argument('--file', '-f', default=None, type=argparse.FileType('r'),
                        help='Scan a single file')
    parser.add_argument('--directory', '-d', default=None,
                        help='Scan all files in directory')
    parser.add_argument('--watch', '-w', default=None,
                        help='Scan newly created files in folder')
    parser.add_argument('--semi-auto', '-a', default=None, type=int,
                        help='Automatically press next page after screenshot. '
                             'The argument is the number of pages to scan. Use together with watch.')
    parser.add_argument('--auto-remove', '-r', action='store_true',
                        help='Automatically remove parsed screenshot. Use together with watch.')

    args = parser.parse_args()

    all_skills = {}
    all_skills['skills'] = {}
    all_skills['sum'] = 0
    all_skills['sum-int'] = 0
    all_skills['total-skills'] = 0
    all_skills['num-skills'] = 0

    if args.file:
        skill_data = pytropia.ocr_skills.from_image(args.file.name)
        all_skills['skills'] = skill_data['skills']
        all_skills['total-skills'] = int(skill_data['total-skills'])
    elif args.watch:
        signal.signal(signal.SIGINT, signal_handler)
        event_handler = ImagesEventHandler(args.watch)
        observer = Observer()
        observer.schedule(event_handler, args.watch, recursive=False)
        observer.start()

        if args.semi_auto:
            pages_left = args.semi_auto
            eprint("Take screen capture to get next page")
            new_file = event_handler.get_file()
            files_to_parse = []


            # TODO: use imagegrab to work with multiple screens
            next_page = pyautogui.locateOnScreen('pytropia/marks/next-page.png')
            eprint(f"Found next page button at {next_page}")
            if not next_page:
                raise Exception("Unable to find next page button in semi auto mode")
            next_page = pyautogui.center(next_page)

            while pages_left > 0 and not DONE:
                new_file = event_handler.get_file()
                if new_file:
                    eprint(f"got {new_file}")
                    files_to_parse.append(new_file)
                    pyautogui.mouseDown(next_page)
                    time.sleep(0.1)
                    pyautogui.mouseUp(next_page)
                    pages_left -= 1
                    eprint(f"Pages left {pages_left}")
                time.sleep(0.1)

            eprint(f"Done with screen shots")
            time.sleep(0.4)  # Give the file some time to rest...

            # Parse all files
            for file in files_to_parse:
                skill_data = pytropia.ocr_skills.from_image(file)
                all_skills['total-skills'] = int(skill_data['total-skills'])
                all_skills['skills'] = {
                    **all_skills['skills'], **skill_data['skills']}
                eprint(f"Parsed {len(skill_data['skills'])} skills from {file}")
                if args.auto_remove:
                    eprint(f"Removing {file}")
                    os.remove(file)
        else:
            while not DONE:
                new_file = event_handler.get_file()
                if new_file:
                    eprint(f"got {new_file}")
                    eprint(f"image queue: {event_handler.queue_len()}")
                    time.sleep(0.4)  # Give the file some time to rest...
                    skill_data = pytropia.ocr_skills.from_image(new_file)
                    all_skills['total-skills'] = int(skill_data['total-skills'])
                    all_skills['skills'] = {
                        **all_skills['skills'], **skill_data['skills']}
                    parsed_skill_points = 0
                    for value in all_skills['skills'].values():
                        parsed_skill_points += math.trunc(value)
                    eprint(f"Parsed {len(skill_data['skills'])} skills")
                    eprint(
                        f"Total skills {parsed_skill_points}/{all_skills['total-skills']}")
                    if args.auto_remove:
                        eprint(f"Removing {new_file}")
                        os.remove(new_file)
                    if parsed_skill_points >= all_skills['total-skills']:
                        break
                time.sleep(0.1)
    elif args.directory:
        for filename in os.listdir(args.directory):
            try:
                skill_data = pytropia.ocr_skills.from_image(
                    os.path.join(args.directory, filename))
                all_skills['total-skills'] = int(skill_data['total-skills'])
                all_skills['skills'] = {
                    **all_skills['skills'], **skill_data['skills']}
                eprint(len(skill_data['skills']))
            except:
                eprint(f"Unable to parse file '{filename}'")

    for key in REMOVE_SKILLS:
        try:
            all_skills['skills'].pop(key)
        except KeyError:
            pass

    all_skills['num-skills'] = len(all_skills['skills'])
    all_skills['sum'] = sum(all_skills['skills'].values())

    for value in all_skills['skills'].values():
        all_skills['sum-int'] += math.trunc(value)

    # eprint(f"Total skills: {all_skills['sum']}")
    # eprint(f"Total whole: {all_skills['sum-int']}")

    print(yaml.dump(all_skills))

    if int(all_skills['sum-int']) != all_skills['total-skills']:
        raise Exception(
            f"Total skills '{all_skills['total-skills']}' different from parsed: '{all_skills['sum-int']}'")

    # eprint(len(all_skills['skills']))

    return 1


if __name__ == "__main__":
    main()
