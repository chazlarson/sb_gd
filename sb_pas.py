from __future__ import print_function

from pathlib import Path
import json
import shutil

from config import prefix
from config import drive_data
from config import sa_file

if prefix == 'aZaSjsklaj':
    print("\n\nIt doesn't look like you've edited the default config for the script before this one.")
    print("\nWhich means that the environment this script is assuming does not exist.")
    print("\nThese scripts are dependent on one another and cannot be run seperately.")
    print("\nEach one relies on tasks performed by the previous one.")
    exit()

PAS_PATH = "/opt/plex_autoscan/config/"

p = Path(sa_file)

CONFIG_PATH = f"{PAS_PATH}config.json"
path = Path(CONFIG_PATH)

if not path.is_file():
    print(f"\n\nThere is no {CONFIG_PATH} here.")
    print(f"\nThis most likely means you have no reason to run this script,")
    print(f"\nsince plex_autoscan is not installed in the expected location.")
    exit()

SECRET_PATH = "client_secrets.json"
path = Path(SECRET_PATH)

if not path.is_file():
    print(f"\n\nThere is no {SECRET_PATH} here.")
    exit()

with open(SECRET_PATH, 'r') as f:
    secret_data = json.load(f)

google_client_id = secret_data['installed']['client_id']
google_client_secret = secret_data['installed']['client_secret']

with open(CONFIG_PATH, 'r') as f:
    data = json.load(f)

google = data['GOOGLE']
control_files = []
path_mappings = data['SERVER_PATH_MAPPINGS']

if len(path_mappings) > 1:
    print("\\n\\nThis doesn't seem like a stock PAS config.")
    exit()

path_map = list(path_mappings.items())[0]
path_map_key = path_map[0]
path_map_list = path_map[1]
path_map_list.pop(-1)
path_map = {}

teamdrives = google['TEAMDRIVES']
filepaths = google['ALLOWED']['FILE_PATHS']

for td in teamdrives:
    if prefix in td:
        print("\\n\\nLooks like this script has already been run.")
        print(f"\nThere's a teamdrive [{td}] defined, which contains the prefix [{prefix}].")
        exit()

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

data['GOOGLE']['CLIENT_ID'] = google_client_id
data['GOOGLE']['CLIENT_SECRET'] = google_client_secret

shutil.copyfile(CONFIG_PATH, f"{CONFIG_PATH}.old")

with open(CONFIG_PATH, 'w') as json_file:
    json.dump(data, json_file, indent=4)
