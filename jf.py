#!/usr/bin/python
from jellyfin_apiclient_python import JellyfinClient
from pick import pick
import sys
import os
import tempfile
import json

debug = 0
authfile = "~/.config/jf/auth.json"

serverUrl = 'https://.../jellyfin'
username_ = ''
password_ = ''


def play_album(id):
    #IndexNumber = song number, ParentIndexNumber = disc number
    songs = client.jellyfin.get_items_by_letter(parent_id=id, media="Audio")['Items']
    songs_sorted = sorted(songs, key=lambda k: (k['ParentIndexNumber'], k['IndexNumber']))

    m3u = "#EXTM3U\n\n"
    m3u += "#PLAYLIST:" + str(songs_sorted[0]['AlbumArtist']) + " - " + str(songs_sorted[0]['Album']) + "\n\n"
    for song in songs_sorted:
        m3u += "#EXTINF:" + str(song['RunTimeTicks'] // 10 ** 7) + "," + str(song['AlbumArtist']) + " - " + str(song['ParentIndexNumber']) + ":" + str(song['IndexNumber']) + " " + song['Name'] + "\n"
        m3u += client.jellyfin.download_url(song['Id']) + "\n"

    with tempfile.NamedTemporaryFile(suffix='.m3u') as tmp:
        print(tmp.name)
        tmp.write(bytes(m3u, 'utf-8'))
        tmp.flush()
        os.system("mpv " + tmp.name)

index = 0

client = JellyfinClient()

client.config.app('your_brilliant_app', '0.0.1', 'PC_1', 'unique_id_2')
client.config.data["auth.ssl"] = True


# auth
authfile = os.path.expanduser(authfile)

dir = os.path.dirname(authfile)
dir = os.path.abspath(dir)
os.makedirs(dir, exist_ok=True)

try:
    server = json.loads(open(authfile, "r").read())
    client.authenticate({"Servers": [server]}, discover=False)
except:
    server = None

if server is None:
    print("logging in")
    client.auth.connect_to_address(serverUrl)
    client.auth.login(serverUrl, username_, password_)
    credentials = client.auth.credentials.get_credentials()
    server = credentials["Servers"][0]
    server["username"] = username_

    f = open(authfile, "w")
    f.write(json.dumps(server))
    f.close()


items = client.jellyfin.search_media_items(term=sys.argv[1], limit=None)["Items"]

possible_types = []
for item in items:
    if item['Type'] not in possible_types:
        possible_types.append(item['Type'])

if len(possible_types) == 0:
    print("Nothing found")
    exit(0)

if debug:
    index = 1
else:
    selectedLib, index = pick(possible_types, "Select", indicator='->')

items = [item for item in items if item['Type'] == possible_types[index]]


# Series
if items[0]['Type'] == "Series":
    if debug:
        index = 0
    else:
        selectedLib, index = pick([item['Name'] for item in items], "Select", indicator='->')
    item = items[index]
    seasons = client.jellyfin.get_seasons(item['Id'])['Items']
    selectedLib, index = pick([season['Name'] for season in seasons], "Select Season", indicator='->')
    episodes = client.jellyfin.get_season(item['Id'], season_id=seasons[index]['Id'])['Items']

    m3u = "#EXTM3U\n\n"
    m3u += "#PLAYLIST:" + str(item['Name']) + " - " + str(seasons[index]['Name']) + "\n\n"
    for episode in episodes:
        try:
            m3u += "#EXTINF:" + str(episode['RunTimeTicks'] // 10 ** 7) + "," + str(item['Name']) + " - " + str(
                seasons[index]['Name']) + " - " + str(episode['IndexNumber']) + ". " + episode['Name'] + "\n"
        except:
            m3u += "#EXTINF:" + "," + str(item['Name']) + " - " + str(
                seasons[index]['Name']) + " - " + str(episode['IndexNumber']) + ". " + episode['Name'] + "\n"
        m3u += client.jellyfin.download_url(episode['Id']) + "\n"

    with open("/tmp/" + str(item['Name']) + " - " + str(seasons[index]['Name']) + ".m3u", "wb") as playlistfile:
        print(playlistfile.name)
        playlistfile.write(bytes(m3u, 'utf-8'))
        playlistfile.flush()
        os.system("mpv " + "\"" + playlistfile.name + "\"")


# Movies
elif items[0]['Type'] == "Movie":
    selectedLib, index = pick([item['Name'] for item in items], "Select", indicator='->')
    os.system("mpv " + client.jellyfin.download_url(items[index]['Id']))


# Songs
elif items[0]['Type'] == "Audio":
    if debug:
        index = 0
    else:
        selectedLib, index = pick([item['AlbumArtist'] + " - " + item['Album'] + " - " + item['Name'] for item in items], "Select", indicator='->')

    item = items[index]
    print(item['AlbumArtist'] + " - " + item['Album'] + " - " + item['Name'])
    os.system("mpv " + client.jellyfin.download_url(items[index]['Id']))


# MusicAlbum
elif items[0]['Type'] == "MusicAlbum":
    if debug:
        index = 0
    else:
        selectedLib, index = pick([item['AlbumArtist'] +" - " + item['Name'] for item in items], "Select", indicator='->')

    item = items[index]
    play_album(item['Id'])




elif items[0]['Type'] == "MusicArtist":
    if debug:
        index = 0
    else:
        selectedLib, index = pick([item['Name'] for item in items], "Select", indicator='->')

    item = items[index]
    albums = client.jellyfin.get_items_by_letter(parent_id=item['Id'], media="MusicAlbum")['Items']

    if debug:
        index = 0
    else:
        selectedLib, index = pick([item['AlbumArtist'] + " - " + item['Name'] for item in albums], "Select", indicator='->')

    play_album(albums[index]['Id'])

