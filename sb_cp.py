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

CLOUDPLOW_PATH = "/opt/cloudplow/"

p = Path(sa_file)

CONFIG_PATH = f"{CLOUDPLOW_PATH}config.json"
path = Path(CONFIG_PATH)

if not path.is_file():
    print (f"\n\nThere is no {CONFIG_PATH} here.")
    exit()

with open(CONFIG_PATH, 'r') as f:
    data = json.load(f)

# data is now a dict
remotes = data['remotes']
uploaders = data['uploader']

if len(remotes) > 1:
    print (f"\n\nToo many remotes.")
    exit()

first_key = list(remotes.keys())[0]
first_remote = list(remotes.values())[0]

first_uploader = list(uploaders.values())[0]

if first_key != 'google':
    print (f"\n\nDoesn't seem like a stock cloudplow config.")
    exit()

data['remotes'] = {}
data['uploader'] = {}

for dn, mediapath in drive_data.items():
    page_token = None
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
