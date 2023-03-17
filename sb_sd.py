from __future__ import print_function
import uuid
import os
import shutil
import socket
import sys
import threading
import subprocess
import time
from pathlib import Path
import yaml

try:
    from apiclient import discovery
    from apiclient.http import MediaFileUpload
    from httplib2 import Http
    from oauth2client import file
    from oauth2client import client
except ModuleNotFoundError:
    print("Requirements Error: Requirements are not installed")
    sys.exit(0)

def countdown(time_sec):
    while time_sec:
        mins, secs = divmod(time_sec, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        time_sec -= 1

# ##############################################################
# handy helper
# ##############################################################
def _copy(self, target):
    import shutil
    assert self.is_file()
    shutil.copy(str(self), str(target))  # str() only there for Python < (3, 6)

Path.copy = _copy

CONFIG_FILE = 'config.py'
CONFIG_TEMPLATE = 'config.py.example'

config_file = Path(CONFIG_FILE)

if not config_file.is_file():
    print("\n\nThere is no config.py here.")
    template = Path(CONFIG_TEMPLATE)
    print("Creating config file...")
    template.copy(config_file)
    print("Please edit config.py to suit and run this script again.")
    exit()

DRIVE_LOG = 'drive_create_log'

path = Path(DRIVE_LOG)

if path.is_file():
    if (input("ATTENTION: THIS QUESTION HAS CHANGED; PLEASE READ IT. \n\
    This script is intended for users who: \n\n\
    1. Have never used Google Drive in a media server context like this AND/OR\n\
    2. Have no media already on Google Drives that they want to use with Saltbox.  \n\n\
    If this is you, answer 'y'.\n\
    [y/n] ") == "y"):
        print("well done, continuing...\n\n")
    else:
        print("\n\nYou don't want to use this script. Go here and read the 'Existing Rclone Setup' section")
        print("https://docs.saltbox.dev/reference/rclone-manual/#existing-rclone-setup")
        exit()

    if (input("Have you verified drive permissions on your google account? [y/n] ") == "y" and
            input("Have you created the required base project? [y/n] ") == "y" and
            input("Have you created the required Google Group? [y/n] ") == "y" and
            input("Have you installed the gcloud SDK tools? [y/n] ") == "y" and
            input("Have you created the expected projects and service accounts? [y/n] ") == "y"):
        print("well done, continuing...\n\n")
    else:
        print("\n\nSee details here and come back when steps 1-5 are completed")
        print("https://docs.saltbox.dev/reference/rclone-manual/")
        exit()
else:
    print("\n\nIt looks like you have run this script before.")
    print(f"Because of this, the introductory questions were skipped.")
    print(f"Hit control-C in the next few seconds to cancel.")
    countdown(10)
    print(f"Continuing...")

# ##############################################################
# You need to install the Google API stuff
# There's a link on the page where I cribbed this:
# https://wescpy.blogspot.com/2017/06/managing-team-drives-with-python-and.html
# ##############################################################

# ##############################################################
# You'll need the usual "client_secrets.json" file next to this
# On first run you will be authenticated
# ##############################################################

from config import prefix
from config import group_email
from config import drive_data
from config import sa_file
from config import backup_drive
from config import union_remote
SETTINGS_FILE = "/srv/git/saltbox/settings.yml"

path = Path("dev-sa.json")

if path.is_file():
    print(f"\n\nThis is the developer's machine.")
    print(f"Overriding a couple settings.")
    SETTINGS_FILE = "./settings.yml"
    prefix = 'heilung'
    sa_file = "dev-sa.json"
    group_email == 'all-sa@dev.testing'

if prefix == 'aZaSjsklaj':
    print("\n\nIt doesn't look like you've edited the default config.")
    print(f"Prefix is still set to {prefix}")
    prefix = ""
    while len(prefix) == 0:
        prefix = input("Please enter your prefix [or 'q' to quit]: ")
        if prefix == 'q':
            print("See step 4 on this page:")
            print("https://docs.saltbox.dev/reference/google-shared-drives/")
            exit()

if group_email == 'all-sa@bing.bang':
    print("\n\nIt doesn't look like you've edited the default config.")
    print(f"Group email is still set to {group_email}")
    group_email = ""
    while len(group_email) == 0:
        group_email = input("Please enter your group email [or 'q' to quit]: ")
        if group_email == 'q':
            print("See step 4 on this page:")
            print("https://docs.saltbox.dev/reference/google-shared-drives/")
            exit()

path = Path('client_secrets.json')

if not path.is_file():
    print("\n\nThere is no client_secrets.json here.")
    print("See step 5 on this page:")
    print("https://docs.saltbox.dev/reference/google-shared-drives/")
    exit()

path = Path(sa_file)

if not path.is_file():
    print(f"\n\nThere is no {sa_file} present.")
    print("You need to either edit this path in the config or copy one of your SA JSON files to that location.")
    exit()

for dn, mediapath in drive_data.items():
    if len(dn.split()) > 1:
        print(f"\n\nYou've got a drive name defined that contains spaces: [{dn}].")
        print("Spaces are not allowed in drive names in this script.")
        exit()

try:
    with open(SETTINGS_FILE, "r") as settings:
        yaml_content = settings.read()
        settings_obj = yaml.safe_load(yaml_content)
        union_remote = settings_obj['rclone']['remote']
        print(f"Found union remote name: '{union_remote}'")
except:
    print("Can't find saltbox settings file")
    print("Defaulting union remote name to '{union_remote}'")


print(f"rclone '{union_remote}' remote check ====")
rc_cmd = f"rclone config show {union_remote}"
SCRIPTFILE=f"tmp.sh"
with open(SCRIPTFILE, 'w') as f:
    f.write(f"#!/bin/bash\n{rc_cmd}\n")
rc_result = subprocess.run(["bash", f"./{SCRIPTFILE}"], stdout=subprocess.PIPE)
pieces = rc_result.stdout.decode('utf-8').split('\n')
for ln in pieces:
    if 'upstreams' in ln:
        upstreams = ln
try:
    pieces = upstreams.split()
    b = 0
    for ln in pieces:
        if 'upstreams' not in ln and '=' not in ln and prefix not in ln:
            b += 1
    if b > 0:
        print(f"There is an rclone remote called '{union_remote}' that this script did not create.")
        print("[or it has been altered since this script created it]")
        print(f"There are {b} elements that do not contain {prefix}")
        print("This script would overwrite that remote.")
        print("To avoid that, the script is exiting.")
        print("Rename or delete that remote before trying again.")
        print("Perhaps this script is not for you.")
        sys.exit(0)
    else:
        print(f"Existing '{union_remote}' remote was created by this script; continuing...")
except NameError as ex:
    print(f"No existing '{union_remote}' remote; continuing...")

Path(SCRIPTFILE).unlink()

#     organizer = Manager
#     fileOrganizer = Content manager
#     writer = Contributor
#     commenter = Commenter
#     reader = Viewer

# ##############################################################
# The user you authenticate as will be set as "manager" already
# Everyone here is going to get an email for every team drive.
# There doesn't seem to be a way to stop that based on a few
# minutes of research.
# Really Actually Pretty Sorry about that.
# ##############################################################
user_emails_with_roles = {
    group_email: 'organizer'
}

FOLDER_MIME = 'application/vnd.google-apps.folder'
BIN_MIME = "application/octet-stream"
FILE_MIME = 'application/vnd.google-apps.file'
ZIP_MIME = 'application/zip'

SOURCE_FILE = 'empty_file.bin'

SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive.appdata']

store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets(
        'client_secrets.json',
        scope=SCOPES,
        redirect_uri='http://localhost:8000/oauth2callback')
    auth_uri = flow.step1_get_authorize_url()
    print('Please go to this URL: {}'.format(auth_uri))
    entire_URL = input('Enter the entire localhost URL: ')
    items = entire_URL.split('code=')
    auth_code = items[1]
    creds = flow.step2_exchange(auth_code)
    store.put(creds)

http=Http()
http.redirect_codes = http.redirect_codes - {308}
http_auth = creds.authorize(http)

DRIVE = discovery.build('drive', 'v3', http=http_auth)

Path(SOURCE_FILE).touch()

# ##############################################################
# Retrieve current rclone remote list
# ##############################################################
raw_remotes = subprocess.run(['rclone', 'listremotes'], stdout=subprocess.PIPE)
current_remotes = raw_remotes.stdout.decode('utf-8').split('\n')
drive_contents = None

def file_is_here(filename, is_directory=False):
    if is_directory:
        tgt_mimeType = FOLDER_MIME
    else:
        tgt_mimeType = BIN_MIME

    if len(drive_contents) > 0:
        for file in drive_contents['files']:
            if file['name'] == filename and file['mimeType'] == tgt_mimeType:
                return True, file['id']

    return False, ''

def create_td(td_name):
    request_id = str(uuid.uuid4())  # random unique UUID string
    body = {'name': td_name}
    return DRIVE.teamdrives().create(body=body, requestId=request_id, fields='id').execute().get('id')


def add_user(td_id, user, role='organizer'):
    # permissions = DRIVE.permissions().list(fileId=td_id, supportsAllDrives=True).execute()
    # Can't easily get "is this guy already here",
    # but adding him again returns the existing user, so meh.
    body = {'type': 'user', 'role': role, 'emailAddress': user}
    return DRIVE.permissions().create(body=body, fileId=td_id, supportsAllDrives=True, fields='id').execute().get('id')


def create_folder(root_id, folder):
    body = {'name': folder, 'mimeType': FOLDER_MIME, 'parents': [root_id]}
    file_present, file_id = file_is_here(folder, True)
    if file_present:
        return False, file_id
    else:
        return True, DRIVE.files().create(body=body,
                                    supportsAllDrives=True, fields='id').execute().get('id')


def create_media_dirs(root_id, mediapath):
    fld_id = root_id
    path_list = mediapath.split('/')

    for folder in path_list:
        folder_dir_is_here = False
        if len(folder) != 0:
            file_present, file_id = file_is_here(folder, True)
            if file_present:
                fld_id = file_id
                print(f"** Found folder {folder}, ID {fld_id}")
            else:
                file_present, fld_id = create_folder(fld_id, folder)
                print(f"** Created folder {folder}, ID {fld_id}")


def create_bin_file_on_root(folder_id, fn, name):
    body = {'name': name, 'mimeType': BIN_MIME, 'parents': [folder_id]}
    file_present, file_id = file_is_here(name, False)
    if file_present:
        return False, file_id
    else:
        return True, DRIVE.files().create(body=body,
                                media_body=fn,
                                supportsAllDrives=True,
                                fields='id').execute().get('id')


def create_flag_files(drivename, td_id):
    folder_name = f"-- {drivename} Shared --"
    created_it, folder_id = create_folder(td_id, folder_name)
    if created_it:
        print(f"** Created folder {folder_name}, ID {folder_id}")
    else:
        print(f"** Found folder {folder_name}, ID {folder_id}")

    mountfile = drivename.lower().replace(' ', '_') + "_mounted.bin"
    created_it, file_id = create_bin_file_on_root(td_id, SOURCE_FILE, mountfile)
    if created_it:
        print(f"** Created file {folder_name}, ID {file_id}")
    else:
        print(f"** Found file {folder_name}, ID {file_id}")


def add_users(td_id):
    for key in user_emails_with_roles:
        role = user_emails_with_roles[key]
        perm_id = add_user(td_id, key, role)
        print(f"** user {key} set as {role}, ID: {perm_id}")


def create_rclone_remote(drive_id, name):
    if name not in current_remotes:
        rc_cmd = f"rclone config create {name} drive scope=drive service_account_file={sa_file} team_drive={drive_id}"
        print(f"Creating rclone remote: {name}")
        SCRIPTFILE=f"{name}.sh"
        with open(SCRIPTFILE, 'w') as f:
            f.write(f"#!/bin/bash\n{rc_cmd}\n")
        rc_result = subprocess.run(["bash", f"./{SCRIPTFILE}"], stdout=subprocess.PIPE)
        print(f"rclone remote definition ========")
        print(rc_result.stdout.decode('utf-8'))
        Path(SCRIPTFILE).unlink()
    else:
        print(f"Found existing rclone remote: {name}")

remote_list = ""
backup_td_id = ""
backup_td_name = ""

for dn, mediapath in drive_data.items():
    page_token = None
    drivename = f"{prefix}-{dn}"
    td_id = "UNKNOWN"
    response = DRIVE.drives().list(
        q=f"name = '{drivename}'",
        fields='nextPageToken, drives(id, name)',
        pageToken=page_token).execute()

    if len(response.get('drives')) == 0:
        # no teamdrive by this name
        td_id = create_td(drivename)
        print(f"** Team Drive {drivename} created, ID: {td_id}")
        with open(DRIVE_LOG, 'a') as f:
            f.write(f"{drivename}|{td_id}\n")
    else:
        for drive in response.get('drives', []):
            drivename = drive.get('name')
            td_id = drive.get('id')
            print(f"Found shared drive: {drivename} ({td_id})")

    drive_contents = DRIVE.files().list(q="trashed=false", includeItemsFromAllDrives=True, teamDriveId=td_id, corpora='drive', supportsAllDrives=True).execute()

    add_users(td_id)

    create_flag_files(drivename, td_id)

    create_media_dirs(td_id, mediapath)

    create_rclone_remote(td_id, drivename)

    if backup_drive == 'automatic':
        # back up to the last one we see
        backup_td_id = td_id
        backup_td_name = drivename
    else:
        if backup_drive == dn:
            # back up to the last one we see
            backup_td_id = td_id
            backup_td_name = drivename

    remote_list += f"{drivename}:/ "

if len(remote_list) > 0:
    rc_cmd = f"rclone config create google union upstreams \"{remote_list}\""
    print("Creating rclone union remote 'google':")
    print(f"rclone remote definition ========")
    os.system(rc_cmd)
    print(f"\n")

if backup_td_id == "":
    print(f"backup drive {backup_drive} wasn't found.")
    print(f"backup will be skipped.")
else:
    sa_backup = Path('backup/sa')
    if sa_backup.parent.exists():
        print("Deleting previous backup files...")
        shutil.rmtree(sa_backup.parent)

    print("Preparing backup files...")
    # back up the stuff we created
    shutil.copytree(Path('/opt/sa/all/'), sa_backup)
    rclone_conf = Path(f"{Path.home()}/.config/rclone/rclone.conf")
    rclone_conf.copy(sa_backup.parent)
    Path('./client_secrets.json').copy(sa_backup.parent)
    Path('./storage.json').copy(sa_backup.parent)
    Path(DRIVE_LOG).copy(sa_backup.parent)

    print("Creating backup archive...")
    shutil.make_archive("sb_sd_artifacts", 'zip', sa_backup.parent)
    backupzip = Path('sb_sd_artifacts.zip')

    def upload_file(drive_service, filename, mimetype, upload_filename, parent_id, resumable=True, chunksize=262144):
        media = MediaFileUpload(filename, mimetype=mimetype, resumable=resumable, chunksize=chunksize)
        # Add all the writable properties you want the file to have in the body!
        body = {"name": upload_filename, "parents": [parent_id]}
        request = drive_service.files().create(body=body, media_body=media, supportsAllDrives=True).execute()
        print("Upload Complete!")


    folder_id = create_folder(backup_td_id, 'saltbox_sd_backup')

    # Upload file
    print(f"Uploading backup archive to {backup_td_name}/saltbox_sd_backup...")
    upload_file(DRIVE, 'sb_sd_artifacts.zip', ZIP_MIME, 'backup.zip', folder_id)
    backupzip.unlink()


print(f"All done.")
