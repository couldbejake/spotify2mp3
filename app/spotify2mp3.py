from __future__ import unicode_literals


import readline
import urllib.request
import string
import time
import json
import traceback
import requests
import shutil

import json, ssl, re, os

from pathlib import Path
from bs4 import BeautifulSoup

from youtube_search import YoutubeSearch

from pytube import YouTube
from pytube import Playlist

import moviepy.editor as mp
from moviepy.editor import *

import eyed3
from eyed3.id3.frames import ImageFrame

from fuzzywuzzy import fuzz
from fuzzywuzzy import process


ssl._create_default_https_context = ssl._create_stdlib_context

global BEARER_TOKEN
global MIN_VIEW_COUNT
global MAX_LENGTH
global DEBUG

BEARER_TOKEN = ""

### SETTINGS

MIN_VIEW_COUNT = 5000 # 5, 000 views
MAX_LENGTH = 60 * 10   # 10 minutes
FAILURE_THRESHOLD = 5 # The number of songs that need to fail before prompting to re-run
DEBUG = True

##

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CBLACK  = '\33[30m'
    CGREENBG  = '\33[42m'
    CREDBG    = '\33[41m'
    CVIOLETBG2 = '\33[105m'

class ConfigException(Exception):
    pass

def get_new_token():
    r = requests.request("GET", "https://open.spotify.com/")
    r_text = BeautifulSoup(r.content, "html.parser").find("script", {"id": "session"}).get_text()
    return json.loads(r_text)['accessToken']

def get_tracks(playlist_id, offset, limit, token):
    url = "https://api.spotify.com/v1/playlists/" + str(playlist_id) + "/tracks?offset=" + str(offset) + "&limit=" + str(limit) + "&market=GB"
    payload={}
    headers = {
      'authorization': 'Bearer ' + str(token),
      'Sec-Fetch-Dest': 'empty',
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)

def get_song_names(playlist_id):
    done = False
    offset_counter = 0
    tracks = []
    while not done:
        new_token = get_new_token()
        data = get_tracks(playlist_id, offset_counter, 100, new_token)
        if(not 'total' in data):
            print(data)
            exit()
        if(data['total'] > 0):
            limit = data['limit']
            offset = data['offset']
            total = data['total']
            print('\nLoading songs from ' + str(bcolors.OKGREEN) + 'Spotfiy' + str(bcolors.ENDC) + ' [ Limit:' + str(limit) + ', offset:' + str(offset) +', total:' + str(total) +  ' ]')
            if(offset < total):
                offset_counter += limit
            else:
                done = True
            for song in data['items']:
                song_name = song['track']['name']
                artist_name = song['track']['artists'][0]['name']
                song_image = song['track']['album']['images'][0]['url']
                tracks.append({'name' : song_name, 'artist' : artist_name, 'song_image' : song_image})
        else:
            print('Oh no, playlist is empty :(')
            done = True
    return tracks




def download_playlist(spotify_playlist_id, folder_name):
    global MIN_VIEW_COUNT

    legal_path_characters = string.ascii_letters + string.digits+ " ()[]" # Allowed characters in file path
    folder_name = ''.join(current_character for current_character in folder_name if current_character in legal_path_characters)

    songs = get_song_names(spotify_playlist_id)

    Path('downloads/' + str(folder_name)).mkdir(parents=True, exist_ok=True)
    Path('temp/').mkdir(parents=True, exist_ok=True)

    failed_downloads = 0 # Counter for songs that failed to download
    failed_song_names = "" # Stringified list of failed songs in printable format
    skipped_songs = 0 # Counter for songs that are skipped because they already exist

    for index, song in enumerate(songs):

        # Sanatizing song name & Artist name for file path output
        song_name = "".join([current_character for current_character in song["name"] if current_character in legal_path_characters])
        artist = "".join([current_character for current_character in song['artist'] if current_character in legal_path_characters])

        song_image_url = song['song_image']
        search_query = song_name + ' ' + artist
        song_mp3_tmp_loc = "./temp/" + str(search_query) + '.mp3'
        song_image_path = "./temp/" + str(search_query) + '.jpg'
        song_final_dest = "downloads/" + str(artist + " - " + song_name) + '.mp3'

        if os.path.exists(song_final_dest):
            print(f"{bcolors.WARNING}Song {search_query} already available at {song_final_dest} skipping {bcolors.ENDC}")
            skipped_songs += 1
            continue

        print('\n' * 3)
        print(bcolors.CGREENBG + bcolors.CBLACK + f'Downloading song {index}/ {len(songs)} [ ' + str(song_name) + ' - ' + str(artist) + ' ]' + bcolors.ENDC + '\n')
        item_loc = 'downloads/' + ((search_query + '.mp3').replace('"', '').replace("'", '').replace('\\', '').replace('/', ''))

        if(os.path.isfile(item_loc)):
            print(search_query)
            print('\nAlready exists! Skipping!\n')
        else:
            try:
                yt_results = YoutubeSearch(search_query, max_results=1).to_json()
                if len(json.loads(yt_results)['videos']) < 1:
                    raise ConfigException('Skipped song -- Could not load from YouTube')
                yt_data = json.loads(yt_results)['videos'][0]

                print('View Count: ' + bcolors.UNDERLINE + yt_data['views'] + bcolors.ENDC)
                print('Duration: ' + bcolors.UNDERLINE + yt_data['duration'] + bcolors.ENDC + '\n')

                sd_data = yt_data['duration'].split(':')
                song_duration = int(sd_data[0]) * 60  + int(sd_data[1])

                song_viewcount = int(re.sub('[^0-9]','', yt_data['views']))

                song_link = "https://www.youtube.com" + yt_data['url_suffix']
                song_albumc_link = yt_data['thumbnails'][0]

                if(song_duration >= MAX_LENGTH):
                    print(bcolors.CREDBG + bcolors.CBLACK + 'Skipped - Song is longer than set max song length.' + bcolors.ENDC)
                    print(bcolors.CVIOLETBG2 + bcolors.CBLACK  + 'Change MAX_LENGTH in the script to prevent skipping' + bcolors.ENDC)
                    raise ConfigException('Skipped song due to MAX_LENGTH value in script')

                if(song_viewcount <= MIN_VIEW_COUNT):
                    print(bcolors.CREDBG + bcolors.CBLACK + 'Skipped - Top song has low view count.' + bcolors.ENDC)
                    print(bcolors.CVIOLETBG2 + bcolors.CBLACK  + 'Change MIN_VIEW_COUNT in the script to prevent skipping' + bcolors.ENDC)
                    raise ConfigException('Skipped song due to MIN_VIEW_COUNT value in script')

                yt_dl_obj = YouTube(song_link)
                yt_vid_obj = yt_dl_obj.streams.filter(only_audio=True).first()
                yt_tmp_out = yt_vid_obj.download(output_path="./temp/")

                print(bcolors.OKCYAN + ">   Downloaded mp4 without frames to " + yt_tmp_out + bcolors.ENDC + '\n')

                urllib.request.urlretrieve(song_image_url, song_image_path)

                print(bcolors.OKCYAN + ">   Downloaded image album cover to " + yt_tmp_out + bcolors.ENDC + '\n')

                print(bcolors.OKCYAN)
                clip = AudioFileClip(yt_tmp_out)
                clip.write_audiofile(song_mp3_tmp_loc)
                print(bcolors.ENDC)

                audiofile = eyed3.load(song_mp3_tmp_loc)
                if (audiofile.tag == None):
                    audiofile.initTag()
                audiofile.tag.images.set(ImageFrame.FRONT_COVER, open(song_image_path, 'rb').read(), 'image/jpeg')
                audiofile.tag.artist = artist
                audiofile.tag.title = song_name
                audiofile.tag.save()

                shutil.copy(song_mp3_tmp_loc, song_final_dest)

                print(bcolors.OKGREEN + "Saved final file to " + song_final_dest + bcolors.ENDC + '\n')
            except Exception as e:
                # TODO: implement other exception
                if(DEBUG):
                    print(bcolors.FAIL + str(e) + bcolors.ENDC)
                if(isinstance(e, KeyError)):
                    f = open('failed_log.txt', 'a')
                    f.write(search_query + '\n' + str(e))
                    f.write('\n' + traceback.format_exc() + '\n')
                    f.close()
                    print(f"{bcolors.WARNING}Failed to convert {search_query} due to error.{bcolors.ENDC}. \nVideo may be age restricted.")
                    failed_downloads += 1
                    failed_song_names = failed_song_names + "\t• " + song_name + " - " + artist + f" | Fail reason: {e}" + "\n"
                elif(not isinstance(e, ConfigException)):
                    f = open('failed_log.txt', 'a')
                    f.write(search_query + '\n' + str(e))
                    f.write('\n' + traceback.format_exc() + '\n')
                    f.close()
                    print(f"{bcolors.WARNING}Failed to convert {search_query} due to error.{bcolors.ENDC}. See failed_log.txt for more information.")
                    failed_downloads += 1
                    failed_song_names = failed_song_names + "\t• " + song_name + " - " + artist + f" | Fail reason: {e}" + "\n"
                    print('Please report this at https://github.com/couldbejake/spotify2mp3' + bcolors.ENDC)
                    quit()
                else:
                    f = open('failed_log.txt', 'a')
                    f.write(search_query + '\n' + str(e))
                    f.write('\n' + traceback.format_exc() + '\n')
                    f.close()
                    print(f"{bcolors.WARNING}Failed to convert {search_query} due to config error.{bcolors.ENDC}. See failed_log.txt for more information.")
                    failed_downloads += 1
                    failed_song_names = failed_song_names + "\t• " + song_name + " - " + artist + f" | Fail reason: {e}" + "\n"
                continue

    print(f"{bcolors.OKGREEN}Successfully downloaded {len(songs) - failed_downloads - skipped_songs}/{len(songs)} songs ({skipped_songs} skipped) to {folder_name}{bcolors.ENDC}\n")

    if failed_downloads >= FAILURE_THRESHOLD:
        if "y" in input(f"\n\nThere were more than {FAILURE_THRESHOLD} failed downloads:\n{failed_song_names} \n\nWould you like to retry with minimum view count halfed ({MIN_VIEW_COUNT//2})? (y/n) "):
            MIN_VIEW_COUNT //= 2
            download_playlist(spotify_playlist_id, folder_name)
            exit()

    if failed_downloads:
        f = open('failed_log.txt', 'a')
        f.write(f"\nFailed downloads for {folder_name}:\n{failed_song_names}\n")
        f.close()

    shutil.rmtree('./temp')
    print(f"{bcolors.FAIL}Failed downloads:\n{failed_song_names}{bcolors.ENDC}\n")

def main(spotify_url_link=None):

    #playlist_name = input('Enter playlist name (leave blank and hit enter to pull name from spotify): ') #"Maya's Party"

    playlist_name = False

    if spotify_url_link == None:
        spotify_url_link = input('\nEnter the spotify URL link: ') #'7rutb883T7WE7k6qZ1LjwU'

    if('playlist/' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('playlist/')[1]
    if('?' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('?')[0]

    if not playlist_name: # Dynamically determine playlist name
        from lxml import html
        page = requests.get(f"https://open.spotify.com/playlist/{spotify_url_link}")
        if not page:
            if len(spotify_url_link) > 8:
                print(bcolors.WARNING + f"\nCould not find a Spotify playlist with the ID '{spotify_url_link[0:8]}..'" + bcolors.ENDC)
            else:
                print(bcolors.WARNING + f"\nCould not find a Spotify playlist with the ID '{spotify_url_link}'" + bcolors.ENDC)
            print(bcolors.FAIL + "Please enter a valid Spotify playlist ID or URL" + bcolors.ENDC)
            main()
            exit()
        playlist_name = html.fromstring(page.content).xpath('/html/body/div/div/div/div/div[1]/div/div[2]/h1')[0].text_content().strip()
        if not playlist_name: # If a playlist name still couldn't be determined recursively call function with same URL
            print(bcolors.WARNING + '\nCould not find playlist name please provide a name\n\n'+ bcolors.ENDC)
            main(spotify_url_link)
            exit()
        print(bcolors.WARNING + f"\nContinuing with: {playlist_name=}" + bcolors.ENDC)

    print(bcolors.WARNING + '\nDownloading from: ' + spotify_url_link + bcolors.ENDC)

    download_playlist(spotify_url_link, playlist_name)

    # Example Usage:
    # download_playlist('7rutb883T7WE7k6qZ1LjwU', "Maya's Party")

if __name__ == "__main__":
    main()
