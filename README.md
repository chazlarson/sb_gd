# sb_gd
Script to set up Google Drive stuff for saltbox/cloudbox

## Assumptions:
 1. You have created a google project as described here: https://docs.saltbox.dev/reference/google-project-setup/
 2. You have the credential JSON to hand
 3. You have created a google group as described here: https://docs.saltbox.dev/reference/google-group-setup/
 4. You have that group address to hand
 5. You have rclone installed
 6. You are running python 3.8 and have run `sudo apt install python3.8-venv -y`.
    Probably other python3 works [this was built on a new saltbox install, so the version is whatever that left me with].  The assumption is that I can create a Python virtual env
 7. `/opt` is owned by you and writeable without sudo

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
