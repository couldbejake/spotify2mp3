from pytube import YouTube
from pytube import Playlist
import os
import moviepy.editor as mp
from moviepy.editor import *
import re
import json
import requests
from youtube_search import YoutubeSearch
from pathlib import Path
import os

def write_to_file(jsondata):
    with open("temptest.json", "w") as twitter_data_file:
        json.dump(jsondata, twitter_data_file, indent=4, sort_keys=True)


def get_new_token():
    #url = ('https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M')
    #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    #response = requests.get(url, headers=headers)

    #return 'BQDJk9Gr9vlAu7bBlSDA5STkw7nQ-ounNoxZpy8bZhWYfI1f4rwyyiW3qqo3d6LQ2CgqdCkOUYNZb0jn6QQ'

    return input('Enter bearer token: ')

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
            print('Loading songs from Spotfiy [Limit-' + str(limit) + ',offset-' + str(offset) +',total-' + str(total) +  ']')
            if(offset < total):
                offset_counter += limit
            else:
                print('Done!')
                done = True
            for song in data['items']:
                song_name = song['track']['name']
                artist_name = song['track']['artists'][0]['name']
                #print(song_name + ' - ' + artist_name)
                tracks.append({'name' : song_name, 'artist' : artist_name})
        else:
            print('Oh no, playlist is empty :(')
            done = True
    return tracks


def download_playlist(spotify_playlist_id):
    songs = get_song_names(spotify_playlist_id)

    Path('downloads/' + str(spotify_playlist_id)).mkdir(parents=True, exist_ok=True)
    
    for song in songs:
        song_name = song['name']
        artist = song['artist']
        search_query = song_name + ' ' + artist
        

        item_loc = 'downloads/' + str(spotify_playlist_id) +'/'+   ((search_query + '.mp3').replace('"', '').replace("'", '').replace('\\', '').replace('/', ''))


        out_file_err = ''

        if(os.path.isfile(item_loc)):
            print(search_query)
            print('\nAlready exists! Skipping!\n')
        else:
            try:
                results = YoutubeSearch(search_query, max_results=1).to_json()
                result = json.loads(results)['videos'][0]
                ytid = result['id']
                title = result['title']
                count = result['views']
                print('\n\n===\nDownloading...')
                url = "https://www.youtube.com/watch?v=" + ytid
                print(url)
                yt = YouTube(url)
                video = yt.streams.get_highest_resolution()
                out_file = video.download(output_path='temp')
                out_file_err = out_file
                clip = mp.VideoFileClip(out_file)
                clip.audio.write_audiofile(item_loc)
            except Exception as e:
                print(e)
                print('Failed to convert ' + str(search_query))
                print('Try doing it manually!')
                f = open('failed_log.txt', 'a')
                f.write(search_query)
                f.close()


        print('===')

    
download_playlist('7rutb883T7WE7k6qZ1LjwU')
    

