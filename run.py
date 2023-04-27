from __future__ import unicode_literals
from asyncio.windows_events import NULL


import urllib.request
import string
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

# from fuzzywuzzy import fuzz
# from fuzzywuzzy import process

from config import *

ssl._create_default_https_context = ssl._create_stdlib_context

BEARER_TOKEN = ""

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


    
#funzioni simpatiche per passare dall'id al codice utilizzato --> id è un base 62, lo devo trasformare in un base hex
BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def decode(string, alphabet=BASE62):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for decoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


def encode(num, alphabet=BASE62):
    """Encode a positive number into Base X and return the string.

    Arguments:
    - `num`: The number to encode
    - `alphabet`: The alphabet to use for encoding
    """
    if num == 0:
        return alphabet[0]
    arr = []
    arr_append = arr.append  # Extract bound-method for faster access.
    _divmod = divmod  # Access to locals is faster.
    base = len(alphabet)
    while num:
        num, rem = _divmod(num, base)
        arr_append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def getActualId(id):
    songId=id
    encodedIdBase10 = decode(songId)
    encodedIdBase16 = encode(encodedIdBase10, '0123456789abcdef')
    return encodedIdBase16

def getActualIdFromEncoded(id):
    encodedIdBase10 = decode(id, '0123456789abcdef')
    encodedIdBase62 = encode(encodedIdBase10)
    # Aggiunge uno 0 all'inizio se la lunghezza della stringa risultante è dispari
    if len(encodedIdBase62) % 2 != 0:
        encodedIdBase62 = '0' + encodedIdBase62
    return encodedIdBase62



def get_tracks(playlist_id, offset, limit, token, linkAdd):
    headers = {
        'authorization': 'Bearer ' + str(token),
        'Sec-Fetch-Dest': 'empty',
        }
    
    if linkAdd == 'album':
        albumId = playlist_id
        
        #song metadata
        query='{"uri":"spotify:album:' +albumId+ '","locale":""}&extensions={"persistedQuery":{"version":1,"sha256Hash":"411f31a2759bcb644bf85c58d2f227ca33a06d30fbb0b49d0f6f264fda05ecd8"}}'
        encoded = urllib.parse.quote(query).replace("%20", "").replace("%26", "&").replace("%3D", "=")
        link = "https://api-partner.spotify.com/pathfinder/v1/query?operationName=getAlbumMetadata&variables="+encoded
        response =  json.loads(requests.request("GET", link, headers=headers).text)
        song_image = response['data']['albumUnion']['coverArt']['sources'][2]['url']
        
        #song name and artist
        query='{"uri":"spotify:album:' +albumId+ '","offset":0,"limit":300}&extensions={"persistedQuery":{"version":1,"sha256Hash":"f387592b8a1d259b833237a51ed9b23d7d8ac83da78c6f4be3e6a08edef83d5b"}}'
        encoded = urllib.parse.quote(query).replace("%20", "").replace("%26", "&").replace("%3D", "=")
        link = "https://api-partner.spotify.com/pathfinder/v1/query?operationName=queryAlbumTracks&variables="+encoded

        response =  json.loads(requests.request("GET", link, headers=headers).text)
        items = response['data']['albumUnion']['tracks']['items']
        
        compiled_data=[]
        for item in items:
            name = item['track']['name']
            
            artist=''
            artists = item['track']['artists']['items']
            for currArtist in artists:
                artist += currArtist['profile']['name'] + " "
        
            compiled_data.append(
                {
                'name': name,
                'artist': artist,
                'song_image': song_image,
                }
            )
            
        return compiled_data
    
    elif linkAdd == 'track':
        headers = {
            'authorization': 'Bearer ' + str(token),
            'Sec-Fetch-Dest': 'empty',
            'accept' : 'application/json',
            'accept-encoding' : 'gzip, deflate, br',
            'accept-language' : 'it',
            'app-platform' : 'WebPlayer',
            'content-type' : 'application/json;charset=UTF-8',
            'origin' : 'https://open.spotify.com',
            'referer' : 'https://open.spotify.com/',
            'sec-ch-ua' : '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile' : '?0',
            'sec-ch-ua-platform' : '"Windows"',
            'sec-fetch-dest' : 'empty',
            'sec-fetch-mode' : 'cors',
            'sec-fetch-site' : 'same-site',
            'spotify-app-version' : '1.2.2.107.gd5d28b77',
            'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        songId = getActualId(playlist_id)  
        trackMetaData = json.loads(requests.get(f'https://spclient.wg.spotify.com/metadata/4/track/{songId}?market=from_token', headers=headers).text)
        albumId = getActualIdFromEncoded(trackMetaData['album']['gid'])

        #song metadata
        query='{"uri":"spotify:album:' +albumId+ '","locale":""}&extensions={"persistedQuery":{"version":1,"sha256Hash":"411f31a2759bcb644bf85c58d2f227ca33a06d30fbb0b49d0f6f264fda05ecd8"}}'
        encoded = urllib.parse.quote(query).replace("%20", "").replace("%26", "&").replace("%3D", "=")
        link = "https://api-partner.spotify.com/pathfinder/v1/query?operationName=getAlbumMetadata&variables="+encoded
        responseStr =  requests.request("GET", link, headers=headers).text
        response =  json.loads(responseStr)
        song_image = response['data']['albumUnion']['coverArt']['sources'][2]['url']

        
        name = response['data']['albumUnion']['name']
        artist=''
        artists = response['data']['albumUnion']['artists']['items']
        for currArtist in artists:
            artist += currArtist['profile']['name'] + " "

        compiled_data=[]
        compiled_data.append(
            {
            'name': name,
            'artist': artist,
            'song_image': song_image,
            }
        )
            
        return compiled_data
    else:
        url = "https://api.spotify.com/v1/playlists/" + str(playlist_id) + "/tracks?offset=" + str(offset) + "&limit=" + str(limit) + "&market=GB"
        payload={}
        response = requests.request("GET", url, headers=headers, data=payload)
        
    return json.loads(response.text)

def get_song_names(playlist_id, linkAdd, token):
    done = False
    offset_counter = 0
    tracks = []
    while not done:
        if token == NULL:
            new_token = get_new_token()
        else:
            new_token = token
            
        data = get_tracks(playlist_id, offset_counter, 100, new_token, linkAdd)
        if linkAdd == 'album' or linkAdd == 'track':
            return data

        if(not 'total' in data):
            # print(data)
            exit()
            
        if(data['total'] > 0):
            limit = data['limit']
            offset = data['offset']
            total = data['total']
            # print('\nLoading songs from ' + str(bcolors.OKGREEN) + 'Spotfiy' + str(bcolors.ENDC) + ' [ Limit:' + str(limit) + ', offset:' + str(offset) +', total:' + str(total) +  ' ]')
            if(offset < total):
                offset_counter += limit
            else:
                done = True
            for song in data['items']:
                song_name = song['track']['name']
                artist_name = song['track']['artists'][0]['name']
                song_image = song['track']['album']['images'][0]['url']
                album_name = song['track']['album']['name']
                tracks.append({'name' : song_name, 'artist' : artist_name, 'song_image' : song_image, 'album_name':album_name})
        else:
            # print('Oh no, playlist is empty :(')
            done = True

    return tracks




def download_playlist(spotify_playlist_id, folder_name, linkAdd, token=NULL):
    global MIN_VIEW_COUNT

    legal_path_characters = string.ascii_letters + string.digits+ " ()[]" # Allowed characters in file path
    folder_name = ''.join(current_character for current_character in folder_name if current_character in legal_path_characters)

    songs = get_song_names(spotify_playlist_id, linkAdd, token) # {'name': 'name', 'artist': 'artist', 'song_image': 'song_image'}

    Path('downloads/' + str(folder_name)).mkdir(parents=True, exist_ok=True)
    if len(PATH_TO_JELLYFIN) > 0:
        Path(PATH_TO_JELLYFIN + str(folder_name)).mkdir(parents=True, exist_ok=True)
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
        song_final_dest = "downloads/" + str(folder_name) + "/"+ str(search_query) + '.mp3'

        if os.path.exists(song_final_dest):
            # print(f"{bcolors.WARNING}Song {search_query} already available at {song_final_dest} skipping {bcolors.ENDC}")
            skipped_songs += 1
            continue

        # print('\n' * 3)
        # print(bcolors.CGREENBG + bcolors.CBLACK + f'Downloading song {index}/ {len(songs)} [ ' + str(song_name) + ' - ' + str(artist) + ' ]' + bcolors.ENDC + '\n')
        item_loc = 'downloads/' + str(spotify_playlist_id) +'/'+   ((search_query + '.mp3').replace('"', '').replace("'", '').replace('\\', '').replace('/', ''))

        if(os.path.isfile(item_loc)):
            ''
            # print(search_query)
            # print('\nAlready exists! Skipping!\n')
        else:
            try:
                yt_results = YoutubeSearch(search_query, max_results=1).to_json()
                if len(json.loads(yt_results)['videos']) < 1:
                    raise ConfigException('Skipped song -- Could not load from YouTube')
                yt_data = json.loads(yt_results)['videos'][0]

                # print('View Count: ' + bcolors.UNDERLINE + yt_data['views'] + bcolors.ENDC)
                # print('Duration: ' + bcolors.UNDERLINE + yt_data['duration'] + bcolors.ENDC + '\n')

                sd_data = yt_data['duration'].split(':')
                song_duration = int(sd_data[0]) * 60  + int(sd_data[1])

                viewcount = re.sub('[^0-9]','', yt_data['views'])
                song_viewcount = int(viewcount) if str(viewcount).isdigit() else 0

                song_link = "https://www.youtube.com" + yt_data['url_suffix']
                song_albumc_link = yt_data['thumbnails'][0]

                if(song_duration >= MAX_LENGTH):
                    # print(bcolors.CREDBG + bcolors.CBLACK + 'Skipped - Song is longer than set max song length.' + bcolors.ENDC)
                    # print(bcolors.CVIOLETBG2 + bcolors.CBLACK  + 'Change MAX_LENGTH in the script to prevent skipping' + bcolors.ENDC)
                    raise ConfigException('Skipped song due to MAX_LENGTH value in script')

                if(song_viewcount <= MIN_VIEW_COUNT):
                    # print(bcolors.CREDBG + bcolors.CBLACK + 'Skipped - Top song has low view count.' + bcolors.ENDC)
                    # print(bcolors.CVIOLETBG2 + bcolors.CBLACK  + 'Change MIN_VIEW_COUNT in the script to prevent skipping' + bcolors.ENDC)
                    raise ConfigException('Skipped song due to MIN_VIEW_COUNT value in script')

                yt_dl_obj = YouTube(song_link)
                yt_vid_obj = yt_dl_obj.streams.filter(only_audio=True)
                
                #select the best audio quality
                prevKbps = 0
                correctIndex = 0
                for i,vid in enumerate(yt_vid_obj):
                    currKbps = int(re.sub("[^0-9]", "", vid.abr))
                    if currKbps>prevKbps:
                        correctIndex = i
                
                yt_vid_obj = yt_vid_obj[correctIndex]
                
                yt_tmp_out = yt_vid_obj.download(output_path="./temp/")
                
                

                # print(bcolors.OKCYAN + ">   Downloaded mp4 without frames to " + yt_tmp_out + bcolors.ENDC + '\n')

                urllib.request.urlretrieve(song_image_url, song_image_path)

                # print(bcolors.OKCYAN + ">   Downloaded image album cover to " + yt_tmp_out + bcolors.ENDC + '\n')

                # print(bcolors.OKCYAN)
                clip = AudioFileClip(yt_tmp_out)
                clip.write_audiofile(song_mp3_tmp_loc)
                # print(bcolors.ENDC)

                audiofile = eyed3.load(song_mp3_tmp_loc)
                if (audiofile.tag == None):
                    audiofile.initTag()
                audiofile.tag.images.set(ImageFrame.FRONT_COVER, open(song_image_path, 'rb').read(), 'image/jpeg')
                audiofile.tag.album = song['album_name']
                audiofile.tag.save()

                shutil.copy(song_mp3_tmp_loc, song_final_dest)

                if len(PATH_TO_JELLYFIN) > 0:
                    jfDir = PATH_TO_JELLYFIN + str(folder_name) + "/"+ str(search_query) + '.mp3'
                    shutil.copy(song_mp3_tmp_loc, jfDir)

                # print(bcolors.OKGREEN + "Saved final file to " + song_final_dest + bcolors.ENDC + '\n')
            except Exception as e:
                print(e)
                # TODO: implement other exception
                if(DEBUG):
                    ''
                    # print(bcolors.FAIL + str(e) + bcolors.ENDC)
                if(isinstance(e, KeyError)):
                    f = open('failed_log.txt', 'a')
                    f.write(search_query + '\n' + str(e))
                    f.write('\n' + traceback.format_exc() + '\n')
                    f.close()
                    # print(f"{bcolors.WARNING}Failed to convert {search_query} due to error.{bcolors.ENDC}. \nVideo may be age restricted.")
                    failed_downloads += 1
                    failed_song_names = failed_song_names + "\t• " + song_name + " - " + artist + f" | Fail reason: {e}" + "\n"
                elif(not isinstance(e, ConfigException)):
                    f = open('failed_log.txt', 'a')
                    f.write(search_query + '\n' + str(e))
                    f.write('\n' + traceback.format_exc() + '\n')
                    f.close()
                    # print(f"{bcolors.WARNING}Failed to convert {search_query} due to error.{bcolors.ENDC}. See failed_log.txt for more information.")
                    failed_downloads += 1
                    failed_song_names = failed_song_names + "\t• " + song_name + " - " + artist + f" | Fail reason: {e}" + "\n"
                    # print('Please report this at https://github.com/couldbejake/spotify2mp3' + bcolors.ENDC)
                    quit()
                else:
                    f = open('failed_log.txt', 'a')
                    f.write(search_query + '\n' + str(e))
                    f.write('\n' + traceback.format_exc() + '\n')
                    f.close()
                    # print(f"{bcolors.WARNING}Failed to convert {search_query} due to config error.{bcolors.ENDC}. See failed_log.txt for more information.")
                    failed_downloads += 1
                    failed_song_names = failed_song_names + "\t• " + song_name + " - " + artist + f" | Fail reason: {e}" + "\n"
                continue

    # print(f"{bcolors.OKGREEN}Successfully downloaded {len(songs) - failed_downloads - skipped_songs}/{len(songs)} songs ({skipped_songs} skipped) to {folder_name}{bcolors.ENDC}\n")

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
    # print(f"{bcolors.FAIL}Failed downloads:\n{failed_song_names}{bcolors.ENDC}\n")
    

def main(spotify_url_link=None, is_web_service=False, playlist_name_web=''):
    #playlist_name = input('Enter playlist name (leave blank and hit enter to pull name from spotify): ') #"Maya's Party"
    playlist_name = False
    token=NULL

    if spotify_url_link == None:
        spotify_url_link = input('\nEnter the spotify URL link: ') #'7rutb883T7WE7k6qZ1LjwU'

    if('playlist/' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('playlist/')[1]
        linkAdd = 'playlist'
    if('album/' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('album/')[1]
        linkAdd = 'album'
    if('track/' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('track/')[1]
        linkAdd = 'track'
    if('?' in spotify_url_link):
        spotify_url_link = spotify_url_link.split('?')[0]


    if not playlist_name: # Dynamically determine playlist name
        from lxml import html
        page = requests.get(f"https://open.spotify.com/{linkAdd}/{spotify_url_link}")
        if not page:
            if len(spotify_url_link) > 8:
                # print(bcolors.WARNING + f"\nCould not find a Spotify playlist with the ID '{spotify_url_link[0:8]}..'" + bcolors.ENDC)
                if is_web_service:
                    return f"\nCould not find a Spotify playlist with the ID '{spotify_url_link[0:8]}..'"
            else:
                # print(bcolors.WARNING + f"\nCould not find a Spotify playlist with the ID '{spotify_url_link}'" + bcolors.ENDC)
                if is_web_service:
                    return f"\nCould not find a Spotify playlist with the ID '{spotify_url_link}'"
                
            # print(bcolors.FAIL + "Please enter a valid Spotify playlist ID or URL" + bcolors.ENDC)
            main()
            exit()
            
        enterIf = False
        
        try:
            playlist_name = html.fromstring(page.content).xpath('/html/body/div/div/div/div/div[1]/div/div[2]/h1')[0].text_content().strip()
        except:
            enterIf = True
        if not playlist_name or enterIf: # If a playlist name still couldn't be determined recursively call function with same URL
            if linkAdd == 'album':
                token = get_new_token()
                headers = {
                'authorization': 'Bearer ' + str(token),
                'Sec-Fetch-Dest': 'empty',
                }
                albumId = spotify_url_link
                query='{"uri":"spotify:album:' +albumId+ '","locale":""}&extensions={"persistedQuery":{"version":1,"sha256Hash":"411f31a2759bcb644bf85c58d2f227ca33a06d30fbb0b49d0f6f264fda05ecd8"}}'
                encoded = urllib.parse.quote(query).replace("%20", "").replace("%26", "&").replace("%3D", "=")
                link = "https://api-partner.spotify.com/pathfinder/v1/query?operationName=getAlbumMetadata&variables="+encoded
                response =  json.loads(requests.request("GET", link, headers=headers).text)
                playlist_name = response['data']['albumUnion']['name']
            elif linkAdd == 'track':
                token = get_new_token()
                headers = {
                'authorization': 'Bearer ' + str(token),
                'Sec-Fetch-Dest': 'empty',
                'accept' : 'application/json',
                'accept-encoding' : 'gzip, deflate, br',
                'accept-language' : 'it',
                'app-platform' : 'WebPlayer',
                'content-type' : 'application/json;charset=UTF-8',
                'origin' : 'https://open.spotify.com',
                'referer' : 'https://open.spotify.com/',
                'sec-ch-ua' : '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                'sec-ch-ua-mobile' : '?0',
                'sec-ch-ua-platform' : '"Windows"',
                'sec-fetch-dest' : 'empty',
                'sec-fetch-mode' : 'cors',
                'sec-fetch-site' : 'same-site',
                'spotify-app-version' : '1.2.2.107.gd5d28b77',
                'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
                }
                songId = getActualId(spotify_url_link)  
                trackMetaData = json.loads(requests.get(f'https://spclient.wg.spotify.com/metadata/4/track/{songId}?market=from_token', headers=headers).text)
                playlist_name = trackMetaData['album']['name']
            else: 
                # print(bcolors.WARNING + '\nCould not find playlist name please provide a name\n\n'+ bcolors.ENDC)
                
                if is_web_service:
                    if playlist_name_web == '':
                        return '\nCould not find playlist name please provide a name\n\n'

                    playlist_name = playlist_name_web
                else:
                    playlist_name = input('\nCould not find playlist name please provide a name\n\n')
                    # main(spotify_url_link)
                    # exit()
        # print(bcolors.WARNING + f"\nContinuing with: {playlist_name=}" + bcolors.ENDC)

    # print(bcolors.WARNING + '\nDownloading from: ' + spotify_url_link + bcolors.ENDC)

    download_playlist(spotify_url_link, playlist_name, linkAdd, token)

    # Example Usage:
    # download_playlist('7rutb883T7WE7k6qZ1LjwU', "Maya's Party")

if __name__ == "__main__":
    main()