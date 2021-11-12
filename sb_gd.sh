#!/bin/bash

# Assumptions:
#  1. You have created a google project as described here: https://docs.saltbox.dev/reference/google-project-setup/
#  2. You have the credential JSON to hand
#  3. You have created a google group as described here: https://docs.saltbox.dev/reference/google-group-setup/
#  4. You have that group address to hand
#  5. You have rclone installed
#  6. You are running python 3.8 and have run sudo apt install python3.8-venv -y
#     Probably other python3 works, the assumption is that I can create a venv
#  7. /opt is writeable by you without sudo

# SETTINGS YOU MAY WANT TO ADJUST
# How many projects to create
# 100 SAs will be created in each project
project_count=3
# enter your google group address; if this is left empty you will be prompted for it
google_group=""
# If you have existing service accounts and want them merged in here
# Enter a prefix or prefixes that can be used to identify them
# alternative_prefixes="bing bang boing"
alternative_prefixes=""
# If you have existing groups you want added to the shared drives
# enter them here.
# alternative_prefixes="google-accounts@bing.bang all-sas@bang.boing"
alternative_groups=""
# Should we download the JSON files?
download_json=1
# END USER SERVICEABLE PARTS

# None of these should need to change
# Seriously, leave them alone
saf_dir=safire
target_dir=/opt
union_remote=test-union
rclone_bin=/usr/bin/rclone
# Explicitly targeting user home here
config_file=~/safire/config.py
prefix_file=~/safire/prefix_file
creds_file=~/safire/creds/creds.json
token_file=~/safire/creds/token.pickle
grptoken_file=~/safire/creds/grptoken.pickle

# temp other control files
shared_drive_names=~/safire/drive_file
drive_create_log=~/safire/drive_create_log
drive_ids=~/safire/drive_ids
user_drive_list=~/safire/list_drives
drives_to_create=~/safire/drive_create

function preflight {
   echo "---------- verifying access prereqs"

   if [[ "$(whoami)" != root ]]; then
      echo "You're not root. CHECK"
   else
      echo "Don't run this as root."
      echo "It stores files in the user home dir."
      echo "---------- exiting with problems"
      exit 1
   fi

   if [ -w $target_dir ] ; then 
      echo "$target_dir is writable. CHECK" ; 
   else
      echo "$target_dir is not writable." ; 
      echo "This script is assuming a standard cloudbox or saltbox system after preinstall." ; 
      echo "---------- exiting with problems"
      exit 1
   fi

   if [ -f $rclone_bin ] ; then 
      echo "$rclone_bin is here. CHECK" ; 
   else
      echo "$rclone_bin is not installed." ; 
      echo "---------- exiting with problems"
      exit 1
   fi

}

function first_half {
   # i'm assuming this has been done
   # sudo apt install python3.8-venv -y
   echo "---------- Setting up safire"
   
   cd $target_dir
   
   if [ ! -d $saf_dir ]; then
      git clone https://github.com/chazlarson/safire $saf_dir
   fi
   
   cd $saf_dir/safire
   
   if [ ! -d safire-venv ]; then
      python3 -m venv safire-venv
      find_and_activate_safire
      pip install wheel
      pip install -r $target_dir/$saf_dir/requirements.txt
   fi
   
   mkdir -p $target_dir/sa/all
   # this is explicitly targeted at user home dir
   mkdir -p ~/safire/creds
   
   echo "---------- Checking $prefix_file"

   if [ -f $prefix_file ]; then
      echo "---------- FOUND $prefix_file"
      eval $(cat "$prefix_file")
   else
      echo "---------- File $prefix_file does not exist."
      prefix=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c6 ;)
      echo "export prefix=$prefix" > "$prefix_file"
      eval $(cat "$prefix_file")
   fi
   
   echo "---------- Prefix set to $prefix"
   
   # this is explicitly targeted at user home dir
   sed "s/project_prefix = \"\"/project_prefix = \"$prefix\"/" default_config.py | sed "s/email_prefix = \".*\"/email_prefix = \"$prefix\"/" > ~/safire/config.py

   echo "---------- verifying that safire can run"
   echo "---------- This should display an error about 'Could not consume arg: --test'"
   ./safire.py --test

   echo "---------- next step:"
   echo "---------- copy your credentials JSON to $creds_file"
   echo "---------- then run this script again."

}

function find_and_activate_safire() {
   echo "---------- Changing dir and activating virtualenv "
   cd $target_dir/$saf_dir/safire
   source safire-venv/bin/activate
}

function do_safire_auth() {
   find_and_activate_safire
   echo "---------- Running Google authentication; follow prompts "
   ./safire.py auth all
   echo "---------- Authenticated to Google "
}

function check_auth {
   echo "---------- Checking authentication "
   if [ -f $creds_file ]; then
      find_and_activate_safire
      if [ -f $token_file ]; then
         if [ -f $grptoken_file ]; then
            echo "---------- Both authentication files exist"
         else
            do_safire_auth
         fi
      else
         do_safire_auth
      fi
   else
      echo "---------- You need to copy your Google credentials JSON file to $creds_file"
      exit 1
   fi
}

function second_half {
   check_auth
   eval $(cat "$prefix_file")
   echo "---------- Prefix set to $prefix"

   if [ -z "$google_group" ]
   then
      echo "---------- Enter Your Google Groups email: "
      read google_group
   else
      echo "---------- Using Google Group: $google_group"
   fi

   find_and_activate_safire

   if [ ! -f $user_drive_list ]; then
       echo 'Movies|/Media/Movies
Music|/Media/Music
TV|/Media/TV' > $user_drive_list
   fi

   
   if [ -f $user_drive_list ]; then
	  rm -f $shared_drive_names
 	  while IFS="|" read -r drive dir; do
	      echo "${prefix}_${drive}" >> $shared_drive_names
 	  done < $user_drive_list
   else
      echo "---------- no drive list file"
	  exit 1
   fi

   # get list of existing shared drives
   ./safire.py list drives $prefix
   # Explicitly targeting user home here
   drive_list_file=~/safire/data/drives_list_${prefix}_.csv

   # /home/chaz/safire/data/drives_list_$prefix_.csv
   # now contains a CSV with drives in it there were any.
   echo "---------- checking $drive_list_file"

   if [ -f "$drive_list_file" ]; then
      rm -f $drives_to_create
	  drivenames=()
	  while IFS= read -r line; do
	      # drivenames+=("$line")
  	      OLDIFS=$IFS
  	      IFS=','
		  foundOne=0
 	      while read id driveid name
 	      do
			  if [ "$name" = "$line" ]; then
				  foundOne=1
			  fi
 	      done < $drive_list_file
		  if [ ! "$foundOne" ]; then
			  echo "---------- Need to create $line"
			  echo $line >> $drives_to_create
		  fi
 	      IFS=$OLDIFS
	  done < $shared_drive_names
   else
      echo "---------- NO $drive_list_file"
	  cp $shared_drive_names $drives_to_create
   fi

   echo "---------- Creating Drives "
   
   if [ -f "$drives_to_create" ]; then
	   rm -f $drive_create_log
	   ./safire.py add drives $drives_to_create >> $drive_create_log
   else
	   echo "---------- No drives to create"
   fi
#
#    #Creating fJUV8T-Music
#
#    # Drive ID for fJUV8T-Music is 0AIUbfs4dVRkdUk9PVA
   if [ ! -f  $drive_ids ]; then
	   awk '/Drive ID/{print}' $drive_create_log > interim
	   awk -F' ' '{print $4"|"$6}' interim > $drive_ids
	   rm -f interim
   fi

   # fJUV8T_Movies|0ANLi8MUHFDloUk9PVA
   # fJUV8T_Music|0APXyWYQ5hmmnUk9PVA
   # fJUV8T_TV|0ADMGTvX4xif6Uk9PVA

   echo "---------- Creating Projects "
  ./safire.py add projects $project_count
   echo "---------- Creating Service Accounts "
  ./safire.py add sas $prefix

   echo "---------- Checking element counts "
   ./safire.py list count > ~/safire/counts.tmp
   # Drive count  : 12
   # Project count: 50
   # Group count  : 1
   # JSON count   : 4900  << compare this
   # SA count     : 4900
   # Member count : 4900
   
   dc=$(sed -n 's/^Drive count *: \(.*\)/\1/p' < ~/safire/counts.tmp)
   pc=$(sed -n 's/^Project count *: \(.*\)/\1/p' < ~/safire/counts.tmp)
   gc=$(sed -n 's/^Group count *: \(.*\)/\1/p' < ~/safire/counts.tmp)
   jc=$(sed -n 's/^JSON count *: \(.*\)/\1/p' < ~/safire/counts.tmp)
   sc=$(sed -n 's/^SA count *: \(.*\)/\1/p' < ~/safire/counts.tmp)
   mc=$(sed -n 's/^Member count *: \(.*\)/\1/p' < ~/safire/counts.tmp)

   echo "Drive count  : $dc"
   echo "Project count: $pc"
   echo "Group count  : $gc"
   echo "JSON count   : $jc"
   echo "SA count     : $sc"
   echo "Member count : $mc"

   rm -f ~/safire/counts.tmp

   echo "---------- Adding Service Accounts to $google_group "
  ./safire.py add members $prefix $google_group
   echo "---------- Adding Alternative Service Accounts to $google_group "
   for alt_prefix in $alternative_prefixes; do 
   	  ./safire.py add members $alt_prefix $google_group
   done

   echo "---------- Adding $google_group to Shared Drives "
  ./safire.py add user $google_group $prefix

   echo "---------- Adding alternative groups to Shared Drives "
   for alt_group in $alternative_groups; do 
   	  ./safire.py add user $alt_group $prefix
   done
   echo "---------- Downloading Service Account JSON files "

   if [ "$jc" == "$sc" ]; then
		echo "-------------- All SA JSON files aready downloaded "
	else
      if [ "$download_json" == 1 ]; then
         ./safire.py add jsons
      else
         echo "-------------- Skipping as requested "
      fi
	fi

   echo "---------- Syncing Service Account JSON files to $target_dir/sa/all "
   # Explicitly targeting user home here
   rsync -av ~/safire/svcaccts/ $target_dir/sa/all
   echo "---------- Creating rclone remotes "
 
 sd_names=""

  while IFS="|" read -r sd_name sd_id; do
      rclone config create $sd_name drive scope=drive service_account_file=$target_dir/sa/all/000150.json team_drive=$sd_id
      rclone touch $sd_name:/saltbox-created-$sd_name
      rclone touch $sd_name:/$sd_name-mount.bin
	  sd_names+="$sd_name: " 
   done < $drive_ids

   echo "---------- Creating standard file systems "
   while IFS="|" read -r drive dir; do
	  rclone mkdir ${prefix}_${drive}:$dir
   done < $user_drive_list
   
   echo "---------- Creating rclone union remote "
   rclone config create $union_remote union upstreams="$sd_names"
   rclone lsd $union_remote:
   
   echo "---------- all done, deactivating virtual env "
   deactivate
}

preflight

if [ -f $config_file ]; then
   echo "---------- Doing google tasks"
   second_half
else
   echo "---------- Doing setup tasks"
   first_half
fi
