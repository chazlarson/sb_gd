from __future__ import print_function

from pathlib import Path

import json
import shutil

from config import prefix
from config import drive_data
from config import sa_file

if prefix == 'aZaSjsklaj':
    print("\n\nIt doesn't look like you've edited the default config, which means")
    print("you apparently didn't run the sb_sd.py script before this one.")
    print("This means that the environment this script is assuming does not exist.")
    print("These scripts are dependent on one another and cannot be run separately.")
    print("Each one relies on tasks performed by the previous one.")
    exit()

CLOUDPLOW_PATH = "/opt/cloudplow/"

p = Path(sa_file)

CONFIG_PATH = f"{CLOUDPLOW_PATH}config.json"
path = Path(CONFIG_PATH)

if not path.is_file():
    print(f"\n\nThere is no {CONFIG_PATH} here.")
    exit()

with open(CONFIG_PATH, 'r') as f:
    data = json.load(f)

# data is now a dict
remotes = data['remotes']
uploaders = data['uploader']

first_key = list(remotes.keys())[0]
first_remote = list(remotes.values())[0]

first_uploader = list(uploaders.values())[0]

if len(remotes) > 1:
    if prefix in first_key:
        print("\n\nLooks like this script has already been run.")
        print(f"\nThe first remote key is: [{first_key}], which contains the prefix [{prefix}].")
        exit()
    print("\n\nThis doesn't seem like a stock cloudplow config.")
    print("There is more than one remote already defined.")
    exit()

if first_key != 'google':
    print("\n\nThis doesn't seem like a stock cloudplow config.")
    print("The first defined remote is not named 'google'.")
    exit()

data['remotes'] = {}
data['uploader'] = {}

page_token = None
for dn, mediapath in drive_data.items():
    drivename = f"{prefix}-{dn}"

    newRemote = first_remote.copy()
    newRemote['hidden_remote'] = ""
    newRemote['sync_remote'] = f"{drivename}:{mediapath}"
    newRemote['upload_folder'] = f"/mnt/local{mediapath}"
    newRemote['upload_remote'] = f"{drivename}:{mediapath}"

    newUploader = first_uploader.copy()

    sa_folder = str(p.parent)

    newUploader['service_account_path'] = sa_folder

    data['remotes'][drivename] = newRemote
    data['uploader'][drivename] = newUploader

shutil.copyfile(CONFIG_PATH, f"{CONFIG_PATH}.old")

with open(CONFIG_PATH, 'w') as json_file:
    json.dump(data, json_file, indent=4)
