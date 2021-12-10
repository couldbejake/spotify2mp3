from pytube import YouTube
from pytube import Playlist
import os
import moviepy.editor as mp
from moviepy.editor import *
import re
import json
import requests
from youtube_search import YoutubeSearch

def write_to_file(jsondata):
    with open("temptest.json", "w") as twitter_data_file:
        json.dump(jsondata, twitter_data_file, indent=4, sort_keys=True)
"""
playlist = Playlist("https://www.youtube.com/playlist?list=PLmWRgWFuj2LSDuV_T8ZaE9kCq1L8oL0ni")

for url in playlist:
    print(YouTube(url))
    a = YouTube(url).streams.get_highest_resolution().download('downloads')
    videoclip = VideoFileClip(a)
    audioclip = videoclip.audio
    audioclip.write_audiofile('test.mp3')
"""

def get_tracks(playlist_id, offset, limit):
    url = "https://api.spotify.com/v1/playlists/" + str(playlist_id) + "/tracks?offset=" + str(offset) + "&limit=" + str(limit) + "&market=GB"
    payload={}
    headers = {
      'authorization': 'Bearer BQCxnA9qJUeb2x2ppN2ABygbuL6UOnMTOIhehxkhvCtHXBye637BpUDZF88PeOzPrp2aU5p8uywLFur6qA4',
      'Sec-Fetch-Dest': 'empty',
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)

def get_song_names(playlist_id):
    done = False
    offset_counter = 0
    tracks = []
    while not done:
        data = get_tracks(playlist_id, offset_counter, 100)
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

songs = get_song_names('7rutb883T7WE7k6qZ1LjwU')

for song in songs:
    song_name = song['name']
    artist = song['artist']
    search_query = song_name + ' ' + artist
    results = YoutubeSearch(search_query, max_results=1).to_json()
    result = json.loads(results)['videos'][0]

    print(result)

    ytid = result['id']
    title = result['title']
    count = result['views']

    print('\n\n===\nDownloading...')
    url = "https://www.youtube.com/watch?v=" + ytid
    print(url)
    print('===')
    

