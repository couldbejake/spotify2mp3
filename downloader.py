from apis.spotify import Spotify
from apis.youtube import YouTube

from pathlib import Path

import ssl

ssl._create_default_https_context = ssl._create_stdlib_context

import string
import shutil

import os
import sys

from utils import resave_audio_clip_with_metadata

from apis.spotify import Spotify, SpotifyPlaylist, SpotifyTrack, SpotifyAlbum

from exceptions import InvalidSpotifyURL, SpotifyAlbumNotFound, SpotifyTrackNotFound, SpotifyPlaylistNotFound, ConfigVideoMaxLength, ConfigVideoLowViewCount

from const import colours

# add logging for number of songs skipped


class SpotifyDownloader():
    def __init__(self, audio_quality=1000000, max_length=60*30, min_view_count=10000):
        self.spotify_client = Spotify()
        self.youtube_client = YouTube()
        self.audio_quality = audio_quality
        self.max_length = max_length
        self.min_view_count = min_view_count

    def download_album(self, playlist_url):

        try:

            album = self.spotify_client.album(playlist_url)

            self.prep_folder("downloads/albums/" + album.get_title(True))

            for track in album.get_tracks():

                try:

                    self.download_track(None, track, "downloads/albums/" + album.get_title(True) + "/", True)

                except SpotifyTrackNotFound as e:
                    
                    print(f"\n{colours.WARNING}[!] Skipped a song we could not find.{colours.ENDC} {e}")
                
                except ConfigVideoMaxLength as e:
                    
                    print(f"\n{colours.WARNING}[!] Skipped a song - The found song was longer than the configured max song length, {colours.ENDC}(use the command line to increase this).{colours.ENDC}\n")
                
                except ConfigVideoLowViewCount as e:
                    
                    print(f"\n{colours.WARNING}[!] Skipped a song - The found song had less views than the minimum view count, {colours.ENDC}(use the command line to increase this).\n")


        except SpotifyAlbumNotFound as e:
            print(f"\n{colours.FAIL}Error: {colours.ENDC}{colours.WARNING}It's probably that this album does not exist {colours.ENDC} (e: {e}).{colours.ENDC}\n")
            sys.exit(1)
            
            return False

    def download_playlist(self, playlist_url):

        skipped_songs = 0

        try:
            playlist = self.spotify_client.playlist(playlist_url)

            self.prep_folder("downloads/playlists/" + playlist.get_title(True))

            for track in playlist.get_tracks():
                
                try:

                    self.download_track(None, track, "downloads/playlists/" + playlist.get_title(True) + "/", True)

                except SpotifyTrackNotFound as e:
                    
                    print(f"\n{colours.WARNING}[!] Skipped a song we could not find.{colours.ENDC} {e}")

                    skipped_songs += 1
                
                except ConfigVideoMaxLength as e:
                    
                    print(f"\n{colours.WARNING}[!] Skipped a song - The found song was longer than the configured max song length, {colours.ENDC}(use the command line to increase this).{colours.ENDC}\n")

                    skipped_songs += 1
                
                except ConfigVideoLowViewCount as e:
                    
                    print(f"\n{colours.WARNING}[!] Skipped a song - The found song had less views than the minimum view count, {colours.ENDC}(use the command line to increase this).\n")

                    skipped_songs += 1

            if(skipped_songs > 0):

                print(f"\n{colours.WARNING}[!] Skipped {skipped_songs} songs.{colours.ENDC}\n")

            return True
        
        except SpotifyPlaylistNotFound as e:
            print(f"\n{colours.FAIL}Error: {colours.ENDC}{colours.WARNING}It's probably that this playlist is private or does not exist {colours.ENDC} (e: {e}).{colours.ENDC}\n")
            sys.exit(1)
            return False
            

    def download_track(self, track_url = None, track = None, output_path = None, as_sub_function = False):

        try:

            output_path = output_path if output_path else "downloads/tracks/"

            if track_url:
                track = self.spotify_client.track(track_url)
            else:
                if(track is None):
                    print("No Track was supplied to download track!")
                    raise Exception("No Track was supplied to download track!")
                
            if(track):
                print(f"\n{colours.OKGREEN}Searching for song{colours.ENDC}: {track.get_title(True)} by {track.get_artist()}")

            self.prep_folder(output_path)
            
            searchable_name = track.get_searchable_title()

            # hardcoded for now max_length, min_view_count

            youtube_link = self.youtube_client.search( searchable_name, self.max_length, self.min_view_count )

            print(f"{colours.ENDC}   - Downloading the song, please wait{colours.ENDC}")

            video_downloaded_path, self.audio_quality = self.youtube_client.download(youtube_link, self.audio_quality)

            # consider updating searchable name to something nicer for the end user

            print(f"{colours.ENDC}   - Converting the song and adding metadata{colours.ENDC}")

            resave_audio_clip_with_metadata(video_downloaded_path, track.get_metadata(), output_path + track.get_title(True) + ".mp3", self.audio_quality)

            print(f"{colours.ENDC}   - Done!")

            return True

        except SpotifyTrackNotFound as e:

            if(not as_sub_function):
                print(f"\n{colours.FAIL}Error: {colours.ENDC}We could not find this particular song online {colours.ENDC} (e: {e}).{colours.ENDC}\n")
                return False
            else:
                raise e
            
        except ConfigVideoMaxLength as e:
            if(not as_sub_function):
                print(f"\n{colours.FAIL}Error: {colours.ENDC}The found song was longer than the configured max song length (use the command line to increase this) {colours.ENDC} (e: {e}).{colours.ENDC}\n")
                return False
            else:
                raise e

        except ConfigVideoLowViewCount as e:
            if(not as_sub_function):
                print(f"\n{colours.FAIL}Error: {colours.ENDC}The found song had less views than the minimum view count (use the command line to increase this){colours.ENDC} (e: {e}).{colours.ENDC}\n")
                return False
            else:
                raise e


    def prep_folder(self, folder_name):
        Path(str(folder_name)).mkdir(parents=True, exist_ok=True)
        Path('temp/').mkdir(parents=True, exist_ok=True)

    def rm_tmp_folder(self):
        shutil.rmtree('./temp')

if __name__ == "__main__":
    pass
