from __future__ import print_function
import uuid
import argparse

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from pathlib import Path
import os
import json
import shutil

from config import prefix
from config import group_email
from config import drive_data
from config import sa_file

PAS_PATH = "/opt/plex_autoscan/config/"

p = Path(sa_file)

CONFIG_PATH = f"{PAS_PATH}config.json"
path = Path(CONFIG_PATH)

if not path.is_file():
    print (f"\n\nThere is no {CONFIG_PATH} here.")
    exit()

with open(CONFIG_PATH, 'r') as f:
    data = json.load(f)

google = data['GOOGLE']
control_files = []
path_mappings = data['SERVER_PATH_MAPPINGS']

if len(path_mappings) > 1:
    print (f"\n\nThis doesn't seem like a stock PAS config.")
    exit()

path_map = list(path_mappings.items())[0]
path_map_key = path_map[0]
path_map_list = path_map[1]
path_map_list.pop(-1)
path_map = {}

teamdrives = google['TEAMDRIVES']
filepaths = google['ALLOWED']['FILE_PATHS']

for drive in drive_data:
    drive_name = f"{prefix}-{drive}"
    path = Path(drive_data[drive])
    dir_root = path.parent.absolute()

    control_file = "/mnt/unionfs/" + drive_name.lower().replace(' ', '_') + "_mounted.bin"
    path_map_entry = f"{drive_name}{dir_root}/"

    teamdrives.append(drive_name)
    control_files.append(control_file)
    filepaths.append(f"{drive_name}{drive_data[drive]}")
    path_map_list.append(path_map_entry)

path_map[path_map_key] = path_map_list

data['SERVER_PATH_MAPPINGS'] = path_map
data['GOOGLE']['TEAMDRIVES'] = teamdrives
data['GOOGLE']['TEAMDRIVE'] = True
data['GOOGLE']['ENABLED'] = True
data['GOOGLE']['ALLOWED']['FILE_PATHS'] = filepaths
data['PLEX_EMPTY_TRASH_CONTROL_FILES'] = control_files

shutil.copyfile(CONFIG_PATH, f"{CONFIG_PATH}.old")

with open(CONFIG_PATH, 'w') as json_file:
    json.dump(data, json_file, indent=4)
