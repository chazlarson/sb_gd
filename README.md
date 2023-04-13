# sb_gd
Script to set up Google Drive stuff for saltbox/cloudbox

## Assumptions:
 1. You have verified Google account permissions as described here: https://docs.saltbox.dev/reference/google-account-perms/
 1. You have created a Google project as described here: https://docs.saltbox.dev/reference/google-project-setup/
 1. You have the credential JSON to hand
 1. You have created a Google group as described here: https://docs.saltbox.dev/reference/google-group-setup/
 1. You have that group address to hand
 1. You have rclone installed
 1. You are running python 3.8 and have run `sudo apt install python3.8-venv -y`.
    Probably other python3 works [this was built on a new saltbox install, so the version is whatever that left me with].  The assumption is that I can create a Python virtual env
 1. `/opt` is owned by you and writeable without sudo

## direnv support

There's en `.envrc` that will set up the environment for you if you are using `direnv`.

## Python versions
The python version usage is described in the saltbox docs: https://docs.saltbox.dev/reference/google-shared-drives/

`sb_sd.py` - Saltbox setup for Google Shared drives

`sb_cp.py` - adjusts stock Cloudplow config files for these shared drives and service accounts.

`sb_pas.py` - adjusts stock Plex Autoscan config file for these shared drives.

## what does sb_sd.py do?

  1. Asks some questions to make sure you've done the required stuff

     It's pointless to lie here since the script will just error later.

  1. Read config.py

     Gets prefix and various other pieces.

  1. Grabs union remote name from settings

  1. Makes sure that any remote by that name looks like it came from this script

  1. Creates shared drives with expected file systems

  1. Add service accounts to the google group you specify

  1. Add Google group to shared drives as Manager

  1. Create rclone remotes for the shared drives

     These are authenticated with a service account file, all using `/opt/sa/all/150.json`

  1. Create or update rclone union remote combining the shared drives

  1. Zip up all work product and upload to one of the shared drives for backup.

## sb_gd.sh

NOTE: the sh version of this script is described below and is not currently used by saltbox because while it always worked on my machine, it never worked on some others' machines.

This script is a two-stage thing.

First run will clone and set up `safire`.

Second run will authenticate `safire`, then:

  1. Create shared drives if needed

     Default is three, "Movies", "Music", "TV"

  1. Create projects

     Default is three.

  1. Create service accounts

     Default is 100 per project

  1. Add service accounts to the google group you specify

  1. Add Google group to shared drives as Manager

  1. Download service account JSON files

  1. Sync service account JSON files to /opt/sa/all

  1. Create rclone remotes for the shared drives

     These are authenticated with a service account file, all using `/opt/sa/all/000150.json`

  1. Create standard file systems on the shared drives

     ```
          Media
          ├── Movies
          ├── Music
          └── TV
     ```

  1. Create rclone union remote combining the shared drives

## Notes

The script generates and uses a random six-character prefix to use with all the stuff it creates, so for example the default shared drives will be something like:
```
MWxlw9_Movies
MWxlw9_Music
MWxlw9_TV
```
This means everything is away from stuff you created and can be cleaned up easily if need be.

That prefix is saved in `~/safire/prefix_file`

If you want to define the shared drives and paths for yourself, create a file `~/safire/list_drives` where each line is `DRIVENAME|PATH`.  The default used in the absence of that file is:
```
Movies|/Media/Movies
Music|/Media/Music
TV|/Media/TV
```
