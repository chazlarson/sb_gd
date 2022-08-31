prefix = 'aZaSjsklaj'

group_email = "all-sa@bing.bang"

sa_file = "/opt/sa/150.json"

# `drive name`: '/directory/on/this/drive`
drive_data = {
    'Movies': '/Media/Movies',
    'Music': '/Media/Music',
    'TV': '/Media/TV'
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
