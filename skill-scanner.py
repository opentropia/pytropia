#!/usr/bin/env python3

from __future__ import print_function
from PIL.Image import EXTENT
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pytropia
import yaml
import math
import argparse
import os
import sys
import sys
import time
import signal


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

    args = parser.parse_args()

    expected_num_skills = 125

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
        while not DONE:
            ## TODO stop when total skills == all skills
            ## TODO stop when expected num skills == num skills
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

    if expected_num_skills != len(all_skills['skills']):
        raise Exception(
            f"Expected '{expected_num_skills}' skills, got '{len(all_skills['skills'])}'")

    # eprint(len(all_skills['skills']))

    return 1


if __name__ == "__main__":
    main()

