from __future__ import unicode_literals

import os
import json
import string
import time
import requests

from pathlib import Path
from bs4 import BeautifulSoup

from youtube_search import YoutubeSearch

from pytube import YouTube
from pytube import Playlist

import moviepy.editor as mp
from moviepy.editor import *

import eyed3
from eyed3.id3.frames import ImageFrame

import urllib.request
import shutil
import json

global BEARER_TOKEN
global MIN_VIEW_COUNT
global MAX_LENGTH
global DEBUG

BEARER_TOKEN = ""

### SETTINGS

MIN_VIEW_COUNT = 20000 # 20, 000 views
MAX_LENGTH = 60 * 10   # 10 minutes
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
    r_text = BeautifulSoup(r.content, "html.parser").find("script", {"id": "config"}).get_text()
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
    legal_path_characters = string.ascii_letters + string.digits+ " ()[]" # Allowed characters in file path
    folder_name = ''.join(current_character for current_character in folder_name if current_character in legal_path_characters)
    songs = get_song_names(spotify_playlist_id)
    Path('downloads/' + str(folder_name)).mkdir(parents=True, exist_ok=True)
    Path('temp/').mkdir(parents=True, exist_ok=True)
    for song in songs:
        # Sanatizing song name & Artist name for file path output
        song_name = "".join([current_character for current_character in song["name"] if current_character in legal_path_characters])
        artist = "".join([current_character for current_character in song['artist'] if current_character in legal_path_characters])
        song_image_url = song['song_image']
        search_query = song_name + ' ' + artist
        print('\n' * 3)
        print(bcolors.CGREENBG + bcolors.CBLACK + 'Downloading song [ ' + str(song_name) + ' - ' + str(artist) + ' ]' + bcolors.ENDC + '\n')
        item_loc = 'downloads/' + str(spotify_playlist_id) +'/'+   ((search_query + '.mp3').replace('"', '').replace("'", '').replace('\\', '').replace('/', ''))
        if(os.path.isfile(item_loc)):
            print(search_query)
            print('\nAlready exists! Skipping!\n')
        else:
            try:
                yt_results = YoutubeSearch(search_query, max_results=1).to_json()

                yt_data = json.loads(yt_results)['videos'][0]

                print('View Count: ' + bcolors.UNDERLINE + yt_data['views'] + bcolors.ENDC)
                print('Duration: ' + bcolors.UNDERLINE + yt_data['duration'] + bcolors.ENDC + '\n')

                sd_data = yt_data['duration'].split(':')

                song_duration = int(sd_data[0]) * 60  + int(sd_data[1])
                song_viewcount = int(yt_data['views'].split(' ')[0].replace(',', ''))

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

                song_mp3_tmp_loc = "./temp/" + str(search_query) + '.mp3'
                song_image_path = "./temp/" + str(search_query) + '.jpg'
                song_final_dest = "downloads/" + str(folder_name) + "/"+ str(search_query) + '.mp3'

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
                audiofile.tag.save()

                shutil.copy(song_mp3_tmp_loc, song_final_dest)

                print(bcolors.OKGREEN + "Saved final file to " + song_final_dest + bcolors.ENDC + '\n')


            except Exception as e:
                f = open('failed_log.txt', 'a')
                f.write(search_query + '\n')
                f.write(str(e))
                f.write('\n')
                f.close()
                print(bcolors.WARNING +  '\nFailed to convert ' + str(search_query))
                if(DEBUG):
                    print(bcolors.FAIL)
                    print(e)
                    print(bcolors.ENDC)
                if(not isinstance(e, ConfigException)):
                    print('Please report this at https://github.com/couldbejake/spotify2mp3' + bcolors.ENDC)
                    quit()

def main():

    playlist_name = input('Enter the name of the playlist: ') #"Maya's Party"
    spotify_url_link = input('Enter the spotify URL link: ') #'7rutb883T7WE7k6qZ1LjwU'

    if('playlist/' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('playlist/')[1]
    if('?' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('?')[0]

    print(bcolors.WARNING + spotify_url_link + bcolors.ENDC)

    download_playlist(spotify_url_link, playlist_name)

    # Example Usage:
    # download_playlist('7rutb883T7WE7k6qZ1LjwU', "Maya's Party")

if __name__ == "__main__":
    main()
