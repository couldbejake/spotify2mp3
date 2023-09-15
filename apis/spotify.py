import re
import requests
import json
import os
import sys

from bs4 import BeautifulSoup

# Add the parent directory to sys.path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import const
from const import colours

from exceptions import InvalidSpotifyURL, SpotifyAlbumNotFound, SpotifyTrackNotFound, SpotifyPlaylistNotFound


class Spotify:

    # Can switch to OAuth2 or another suitable authentication method

    def get_new_token(self):
        try:
            r = requests.request("GET", "https://open.spotify.com/")
            r_text = (
                BeautifulSoup(r.content, "html.parser")
                .find("script", {"id": "session"})
                .get_text()
            )
        except Exception as e:
            print(f"{colours.FAIL}Error: It looks like Spotify has automatically temporarily blocked you..{colours.ENDC}")
            sys.exit(0)

        return json.loads(r_text)["accessToken"]

    def __init__(self):
        self.base_url = "https://api.spotify.com/v1/"
        self.bearer_token = self.get_new_token()



    def make_request(self, endpoint):

        response = requests.get(
            self.base_url + endpoint,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "Spotify2mp3",
            },
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request to {self.base_url + endpoint} failed with status code {response.status_code}")
            return None

    def is_valid_resource(self, resource_url):
        response = requests.get(resource_url)
        return response.status_code == 200

    def playlist(self, playlist_url):
        if not re.match(
            r"https://open\.spotify\.com/playlist/[A-Za-z0-9?=\-]+", playlist_url
        ):
            raise InvalidSpotifyURL(f"Invalid Spotify Playlist URL: {playlist_url}")
        return SpotifyPlaylist(self.bearer_token, playlist_url)

    def track(self, track_url):
        if not re.match(
            r"https://open\.spotify\.com/track/[A-Za-z0-9?=\-]+", track_url
        ):
            raise InvalidSpotifyURL(f"Invalid Spotify Track URL: {track_url}")
        return SpotifyTrack(self.bearer_token, track_url)

    def album(self, album_url):
        if not re.match(
            r"https://open\.spotify\.com/album/[A-Za-z0-9?=\-]+", album_url
        ):
            raise InvalidSpotifyURL(f"Invalid Spotify Album URL: {album_url}")
        return SpotifyAlbum(self.bearer_token, album_url)


class SpotifyPlaylist(Spotify):
    def __init__(self, bearer_token, resource_url):
        super().__init__()
        self.bearer_token = bearer_token
        self.resource_url = resource_url
        self.playlist_id_match = re.search(
            r"/playlist/([a-zA-Z0-9]+)", self.resource_url
        )
        self.playlist_metadata = []

    def is_valid(self):
        if not self.is_valid_resource(self.resource_url):
            return False
        return True

    def load_metadata(self):

        endpoint = f"playlists/{self.playlist_id_match.group(1)}"
        playlist_data = super().make_request(endpoint)

        if playlist_data:

            tracks = []

            for track in playlist_data.get("tracks", {}).get("items", []):
                external_urls = track.get("external_urls", {})

                this_track = SpotifyTrack(self.bearer_token, external_urls.get("spotify", ""))
                this_track.load_metadata(track["track"])
                tracks.append(this_track)

            if len(tracks) == 0:
                raise SpotifyPlaylistNotFound("Failed to fetch playlist data from Spotify API.")

            self.playlist_metadata = {
                "title": playlist_data.get("name", ""),
                "image_url": playlist_data.get("images", const.UNKNOWN_ALBUM_COVER_URL)[0]["url"],
                "tracks": tracks,
            }

            return self.playlist_metadata

        else:
            raise SpotifyPlaylistNotFound("Failed to fetch playlist data from Spotify API.")

    def get_title(self, sanitize=False):

        if not self.playlist_metadata:
            self.load_metadata()

        playlist_title = self.playlist_metadata.get("title", "Unknown Playlist Name")

        if not sanitize:
            return playlist_title
        else:
            return "".join(
                [
                    current_character
                    for current_character in playlist_title
                    if current_character in const.LEGAL_PATH_CHARACTERS
                ]
            )

    

    def get_cover_art_url(self):

        if not self.playlist_metadata:
            self.load_metadata()

        cover_art_url = self.playlist_metadata.get("image_url", const.UNKNOWN_ALBUM_COVER_URL)

        return cover_art_url

    def get_tracks(self):

        if not self.playlist_metadata:
            self.load_metadata()

        return self.playlist_metadata.get("tracks", [])

    def get_metadata(self):

        if not self.playlist_metadata:
            self.load_metadata()

        return self.playlist_metadata


class SpotifyAlbum(Spotify):
    def __init__(self, bearer_token, resource_url):
        super().__init__()
        self.bearer_token = bearer_token
        self.resource_url = resource_url
        self.album_id_match = re.search(r"/album/([a-zA-Z0-9]+)", self.resource_url)
        self.album_metadata = []

    def is_valid(self):
        if not self.is_valid_resource(self.resource_url):
            return False
        return True

    def load_metadata(self):

        endpoint = f"albums/{self.album_id_match.group(1)}"
        album_data = super().make_request(endpoint)

        if album_data:

            tracks = []

            for track in album_data.get("tracks", {}).get("items", []):
                external_urls = track.get("external_urls", {})

                this_track = SpotifyTrack(self.bearer_token, external_urls.get("spotify", ""))

                this_track.load_metadata(track)
                this_track.update_metadata("image_url", album_data.get("images", const.UNKNOWN_ALBUM_COVER_URL)[0]["url"])

                tracks.append(this_track)

            if len(tracks) == 0:
                raise SpotifyAlbumNotFound("Failed to fetch album data from Spotify API.")

            self.album_metadata = {
                "title": album_data.get("name", ""),
                "image_url": album_data.get("images", const.UNKNOWN_ALBUM_COVER_URL)[0]["url"],
                "tracks": tracks,
            }

            return self.album_metadata

        else:
            raise SpotifyAlbumNotFound("Failed to fetch album data from Spotify API.")

    def get_title(self, sanitize=False):

        if not self.album_metadata:
            self.load_metadata()

        album_title = self.album_metadata.get("title", "Unknown Album Name")

        if not sanitize:
            return album_title
        else:
            return "".join(
                [
                    current_character
                    for current_character in album_title
                    if current_character in const.LEGAL_PATH_CHARACTERS
                ]
            )

    def get_cover_art_url(self):

        if not self.album_metadata:
            self.load_metadata()

        cover_art_url = self.album_metadata.get("image_url", const.UNKNOWN_ALBUM_COVER_URL)

        return cover_art_url

    def get_tracks(self):

        if not self.album_metadata:
            self.load_metadata()

        return self.album_metadata.get("tracks", [])

    def get_metadata(self):

        if not self.album_metadata:
            self.load_metadata()

        return self.album_metadata


class SpotifyTrack(Spotify):
    def __init__(self, bearer_token, resource_url):
        super().__init__()
        self.bearer_token = bearer_token
        self.resource_url = resource_url
        self.track_id_match = re.search(r"/track/([a-zA-Z0-9]+)", self.resource_url)
        self.track_metadata = []


    def is_valid(self):
        if not self.is_valid_resource(self.resource_url):
            return False
        return True

    def load_metadata(self, track_data=None):

        if track_data == None:
            endpoint = f"tracks/{self.track_id_match.group(1)}"
            track_data = super().make_request(endpoint)

        if track_data:

            album_data = track_data.get("album", {})
            artists_data = track_data.get("artists", [{}])
            external_urls = track_data.get("external_urls", {})
            album_images = album_data.get("images", [{}])

            self.track_metadata = {
                "title": track_data.get("name", ""),
                "artist": [artist.get("name", "") for artist in artists_data],
                "album": album_data.get("name", ""),
                "release_date": album_data.get("release_date", ""),
                "track_num": track_data.get("track_number", 0),
                "disc_num": track_data.get("disc_number", 0),
                "isrc": track_data.get("external_ids", {}).get("isrc", False),
                "comments": {
                    "Spotify Track URL": external_urls.get("spotify", ""),
                    "Spotify Album URL": album_data.get("external_urls", {}).get("spotify", ""),
                    "Spotify Artist URL": artists_data[0].get("external_urls", {}).get("spotify", ""),
                    "Duration (ms)": str(track_data.get("duration_ms", "")),
                    "Album Type": album_data.get("album_type", ""),
                },
                "image_url": album_images[0].get("url", const.UNKNOWN_ALBUM_COVER_URL),
            }

        else:
            raise SpotifyTrackNotFound("Failed to fetch album data from Spotify API.")

    def update_metadata(self, key, value):
        self.track_metadata[key] = value

    def get_title(self, sanitize=False):

        if not self.track_metadata:
            self.load_metadata()

        track_title = self.track_metadata.get("title", "Unknown Title")

        if not sanitize:
            return track_title
        else:
            return "".join(
                [
                    current_character
                    for current_character in track_title
                    if current_character in const.LEGAL_PATH_CHARACTERS
                ]
            )
    
    def get_artist(self, sanitize=False):

        if not self.track_metadata:
            self.load_metadata()

        artist_name = " ".join(self.track_metadata.get("artist", "Unknown artist"))

        if not sanitize:
            return artist_name
        
        else:
            return "".join(
                [
                    current_character
                    for current_character in artist_name
                    if current_character in const.LEGAL_PATH_CHARACTERS
                ]
            )

    def get_searchable_title(self):

        if not self.track_metadata:
            self.load_metadata()

        searchable_title = (
            self.track_metadata.get("title", "Unknown Title")
            + " - "
            + " ".join(self.track_metadata.get("artist"))
        )

        return searchable_title

    def get_cover_art_url(self):

        if not self.track_metadata:
            self.load_metadata()

        cover_art_url = self.track_metadata.get("image_url", const.UNKNOWN_ALBUM_COVER_URL)

        return cover_art_url

    def get_metadata(self):

        if not self.track_metadata:
            self.load_metadata()

        return self.track_metadata


if __name__ == "__main__":
    pass
