from __future__ import print_function
import uuid

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

# ##############################################################
# You need to install the Google API stuff
# There's a link on the page where I cribbed this:
# https://wescpy.blogspot.com/2017/06/managing-team-drives-with-python-and.html
# ##############################################################

# ##############################################################
# You'll need the usual "client_secrets.json" file next to this
# On first run you will be authenticated
# Oh, and 'touch empty_file.bin' before running
# ##############################################################

# ##############################################################
# WARNING: THERE IS NO CHECKING WHETHER THESE TEAMDRIVES EXIST
# THE SCRIPT WILL HAPPILY CREATE DUPLICATES EVERY TIME YOU RUN IT
# ##############################################################
drivenames = [
    'Movies',
    'TV'
]

# ##############################################################
# Creates MEDIA_DIR, then creates the others underneath that
# ##############################################################
MEDIA_DIR = 'Media'
mediadirs = [
    'Movies',
    'TV',
]

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
    'group@domain.com': 'organizer',
    'thatguyfromthebar@whatever.com': 'reader'
}

FOLDER_MIME = 'application/vnd.google-apps.folder'
SOURCE_FILE = 'empty_file.bin'
BIN_MIME = "application/octet-stream"

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
    creds = tools.run_flow(flow, store)
DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

def create_td(td_name):
    request_id = str(uuid.uuid4()) # random unique UUID string
    body = {'name': td_name}
    return DRIVE.teamdrives().create(body=body,
            requestId=request_id, fields='id').execute().get('id')

def add_user(td_id, user, role='organizer'):
    body = {'type': 'user', 'role': role, 'emailAddress': user}
    return DRIVE.permissions().create(body=body, fileId=td_id,
            supportsTeamDrives=True, fields='id').execute().get('id')

def create_folder(root_id, folder):
    body = {'name': folder, 'mimeType': FOLDER_MIME, 'parents': [root_id]}
    return DRIVE.files().create(body=body,
            supportsTeamDrives=True, fields='id').execute().get('id')

def create_media_dirs(root_id):
    f_id = create_folder(root_id, MEDIA_DIR)
    print(f"** Folder {MEDIA_DIR} created, ID {f_id}")
    for fn in mediadirs:
        f1_id = create_folder(f_id, fn)
        print(f"** Folder {fn} created, ID {f1_id}")


def create_bin_file_on_root(folder_id, fn, name):
    body = {'name': name, 'mimeType': BIN_MIME, 'parents': [folder_id]}
    return DRIVE.files().create(body=body, media_body=fn,
            supportsTeamDrives=True, fields='id').execute().get('id')

for dn in drivenames:
    td_id = create_td(dn)
    print(f"** Team Drive {dn} created, ID: {td_id}")
    for key in user_emails_with_roles:
        role = user_emails_with_roles[key]
        perm_id = add_user(td_id, key, role)
        print(f"** user {key} created as {role}, ID: {perm_id}")

    folder_name = f"-- {dn} Shared --"
    folder_id = create_folder(td_id, folder_name)
    print(f"** Folder {folder_name} created, ID {folder_id}")
    mountfile = dn.lower().replace(' ', '_') + "_mounted.bin"
    file_id = create_bin_file_on_root(td_id, SOURCE_FILE, mountfile)
    print(f"** bin file created on root, ID {file_id}")
    
    create_media_dirs(td_id)
