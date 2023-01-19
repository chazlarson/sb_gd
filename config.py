prefix = 'aZaSjsklaj'

group_email = "all-sa@bing.bang"

sa_file = "/opt/sa/all/150.json"

backup_drive = "automatic"
# If this is set  to "automatic", files will be backed up to
# the last shared drive that the script processes.
# If you want to put them on a specific drive, enter one of
# the names from the table below: "Anime", "Books", etc.
# set it to anything else to disable this.

# `drive name`: '/directory/on/this/drive`
drive_data = {
    'Anime': '/Media/Anime',
    'Books': '/Media/Books',
    'Movies': '/Media/Movies',
    'Movies-4K': '/Media/Movies-4K',
    'Music': '/Media/Music',
    'TV': '/Media/TV',
    'TV-4K': '/Media/TV-4K'
}
# Notes on drive naming; this default file uses "Movies", "Music", "TV" just for clarity.
# The name is totally arbitrary.  The script is going to concatenate the prefix and the name,
# then use 'aZaSjsklaj-Movies' as the name of the shared drive and the name of the rclone remote.
# You should not use spaces in these names, as various other tool smay not be exp[ecting to have
# to escape the name of the rclone remote.  These are a behind-the-scenes implementation detail
# that should not matter to anyone. If you are seeking to add more:
# drive_data = {
#     'Movies': '/Media/Movies',
#     'Music': '/Media/Music',
#     'TV': '/Media/TV'
#     'KidsMovies': '/Media/KidsMovies',
#     '4KMovies': '/Media/4KMovies',
#     'BadMovies': '/Media/BadMovies',
# }
# or the like.  You could also do:
# drive_data = {
#     '001': '/Media/Movies',
#     '002': '/Media/Music',
#     '003': '/Media/TV'
#     '004': '/Media/KidsMovies',
#     '005': '/Media/4KMovies',
#     '006': '/Media/BadMovies',
# }

# if you changed this value in /srv/git/saltbox/settings.yml                                                                             in zsh at 17:36:03
# rclone:
#   version: latest
#   remote: google     <<<<<< THIS ONE HERE
# change this value to match if you are not running on the saltbox machine
union_remote = 'google'