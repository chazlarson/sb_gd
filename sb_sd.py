import time
import uuid
import os
import socket
import sys
import threading

from apiclient import discovery
from httplib2 import Http
from oauth2client import file
from pathlib import Path
from oauth2client import client

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from http.server import HTTPServer


if (input("Have you verified drive permissions on your google account? [y/n] ") == ("y") and
    input("Have you created the required base project? [y/n] ") == ("y") and
    input("Have you created the required Google Group? [y/n] ") == ("y") and
    input("Have you installed the gcloud SDK tools? [y/n] ") == ("y") and
    input("Have you created the expected projects and service accounts? [y/n] ") == ("y")):
        print ("well done, continuing...\n\n")
else:
    print("\n\nSee details here and come back when steps 1-5 are completed")
    print("https://docs.saltbox.dev/reference/rclone-manual/")
    exit()

from config import prefix
from config import group_email
from config import drive_data
from config import sa_file

if prefix == 'aZaSjsklaj':
    print("\n\nIt doesn't look like you've edited the default config.")
    print("See step 4 on this page:")
    print("https://docs.saltbox.dev/reference/google-shared-drives/")
    exit()

path = Path('client_secrets.json')

if not path.is_file():
    print("\n\nThere is no client_secrets.json here.")
    print("See step 5 on this page:")
    print("https://docs.saltbox.dev/reference/google-shared-drives/")
    exit()

# Python3 code to display hostname and
# IP address

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)

class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '|/-\\': yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False

from urllib.parse import parse_qs

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # self.path = '/oauth2callback?code=4%2F0AX4XfWhMAtdElAuVTIaMhMsNgYVmuXLdTwm-DEsVdfZ6hdjbmAtGj5k5OKFpdiZrhuHiVQ&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive'
        s = self.path
        values = parse_qs(s[2:]) # prints {'other': ['some'], 'parameter': ['value']}
        if 'code' in values:
            auth_code = values['code'][0]
            creds = flow.step2_exchange(auth_code)
            store.put(creds)
            self.send_response(200)
            self.end_headers()


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass

# server = ThreadingSimpleServer(('0.0.0.0', 8000), Handler)
# server.serve_forever()

def start_server(path, port=8000):
    '''Start a simple webserver serving path on port'''
    httpd = HTTPServer((host_ip, port), Handler)
    httpd.serve_forever()

# Start the server in a new thread
port = 8000
daemon = threading.Thread(name='daemon_server',
                          target=start_server,
                          args=('.', port))
daemon.setDaemon(True)
daemon.start()

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
SOURCE_FILE = 'empty_file.bin'
DRIVE_LOG = 'drive_create_log'
BIN_MIME = "application/octet-stream"
ACCEPTABLE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUYVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'

SCOPES = 'https://www.googleapis.com/auth/drive'
SERVICE_ACCOUNT_FILE = 'service-account.json'
storage_path = Path('storage.json')

store = file.Storage('storage.json')
creds = None

if storage_path.is_file():
    creds = store.get()
else:
    print("No storage.json here.")

if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets(
        'client_secrets.json',
        scope=SCOPES,
        redirect_uri=f"http://{host_ip}:8000/")
    auth_uri = flow.step1_get_authorize_url()
    print('Please go to this URL and sign in: {}'.format(auth_uri))

    with Spinner():
        while not storage_path.is_file():
            time.sleep(1)

    creds = store.get()

DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

Path(SOURCE_FILE).touch()

def create_td(td_name):
    request_id = str(uuid.uuid4())  # random unique UUID string
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


def create_media_dirs(root_id, mediapath):
    fld_id = root_id
    path_list = mediapath.split('/')
    for folder in path_list:
        if len(folder) != 0:
            q = "'" + fld_id + "' in parents and name='" + folder + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if files := DRIVE.files().list(q=q).execute().get('files'):
                fld_id = files[0].get('id')
            else:
                fld_id = create_folder(fld_id, folder)
                print(f"** Folder {folder} created, ID {fld_id}")


def create_bin_file_on_root(folder_id, fn, name):
    body = {'name': name, 'mimeType': BIN_MIME, 'parents': [folder_id]}
    return DRIVE.files().create(body=body, media_body=fn,
                                supportsTeamDrives=True, fields='id').execute().get('id')


def create_rclone_remote(drive_id, name):
    rc_cmd = f"rclone config create {name} drive scope=drive service_account_file={sa_file} team_drive={drive_id}"
    print(rc_cmd)
    drive_res = os.system(rc_cmd)
    print(drive_res)


remote_list = ""

for dn, mediapath in drive_data.items():
    page_token = None
    drivename = f"{prefix}-{dn}"
    response = DRIVE.drives().list(
        q=f"name contains '{drivename}'",
        fields='nextPageToken, drives(id, name)',
        pageToken=page_token).execute()
    # if this drive doesn't exist
    # then we can continue
    if len(response.get('drives')) == 0:
        td_id = create_td(drivename)
        print(f"** Team Drive {drivename} created, ID: {td_id}")
        with open(DRIVE_LOG, 'a') as f:
            f.write(f"{drivename}|{td_id}\n")
        for key in user_emails_with_roles:
            role = user_emails_with_roles[key]
            perm_id = add_user(td_id, key, role)
            print(f"** user {key} created as {role}, ID: {perm_id}")

        folder_name = f"-- {drivename} Shared --"
        folder_id = create_folder(td_id, folder_name)
        print(f"** Folder {folder_name} created, ID {folder_id}")
        mountfile = drivename.lower().replace(' ', '_') + "_mounted.bin"
        file_id = create_bin_file_on_root(td_id, SOURCE_FILE, mountfile)
        print(f"** bin file created on root, ID {file_id}")

        create_media_dirs(td_id, mediapath)

        create_rclone_remote(td_id, drivename)

        remote_list += f"{drivename}:/ "
    else:
        for drive in response.get('drives', []):
            print(f"Found shared drive: {drive.get('name')} ({drive.get('id')})")
            remote_list += f"{drivename}:/ "

if len(remote_list) > 0:
    rc_cmd = f"rclone config create google union upstreams \"{remote_list}\""
    print(rc_cmd)
    os.system(rc_cmd)
