# TODO:
# - Auto detect song, album, playlist from url in wizard mode
# - Add logging to custom exceptions, and catch them!
# - Have a list of failed songs
# - Patch the front end into the backend
# - Add a progress bar
# - Add multi-threading
import argparse
import sys
import utils
import re
from downloader import SpotifyDownloader

from const import colours, DEFAULT_MIN_VIEWS_FOR_DOWNLOAD, DEFAULT_MAX_LENGTH_FOR_DOWNLOAD

def display_splash():
    utils.print_splash_screen()

def get_bitrate_from_quality(quality):
    if quality == "low":
        return 50000
    elif quality == "medium":
        return 80000
    elif quality == "high":
        return 160000
    else:
        return int(quality)

def validate_quality(quality):
    valid_strings = ['low', 'medium', 'high']
    if quality in valid_strings:
        return quality
    try:
        bitrate = int(quality)
        if 64 <= bitrate <= 320000:  # Typical YouTube bitrate ranges
            return quality
        else:
            raise argparse.ArgumentTypeError(f"Bitrate outside of typical YouTube range (64 kbps to 320 kbps): {quality}")
    except ValueError:
        raise argparse.ArgumentTypeError(f"\nInvalid quality/bitrate: {quality}\n")

def validate_spotify_url(url):
    """Validate the Spotify URL and infer the type."""
    song_pattern = r"https://open\.spotify\.com/track/[A-Za-z0-9?=\-]+"
    playlist_pattern = r"https://open\.spotify\.com/playlist/[A-Za-z0-9?=\-]+"
    album_pattern = r"https://open\.spotify\.com/album/[A-Za-z0-9?=\-]+"

    if re.match(song_pattern, url):
        return 'song'
    elif re.match(playlist_pattern, url):
        return 'playlist'
    elif re.match(album_pattern, url):
        return 'album'
    else:
        print("")
        raise ValueError(f"Invalid Spotify URL: {url}\n")

def get_user_input():
    """Prompt the user for input when no arguments are supplied."""
    url = input(f"{colours.OKGREEN}Please provide a Spotify URL (right click, share, copy link):{colours.ENDC} \n\n> ")

    # Validate and infer the type of content from the URL
    try:
        choice = validate_spotify_url(url)
    except ValueError as e:
        print(f"{colours.FAIL}Error: {e}{colours.ENDC}")
        sys.exit(1)

    quality = input(f"\n{colours.OKGREEN}Which quality would you like?{colours.ENDC} (Options: {colours.HEADER}low{colours.ENDC}, {colours.HEADER}medium{colours.ENDC}, {colours.HEADER}high{colours.ENDC}, or specify bitrate): ").strip()

    # Validate quality input
    while quality not in ['low', 'medium', 'high'] and not quality.isdigit():
        quality = input(f"{colours.OKGREEN}Invalid quality.{colours.ENDC} Please choose between {colours.HEADER}low{colours.ENDC}, {colours.HEADER}medium{colours.ENDC}, {colours.HEADER}high{colours.ENDC}, or provide a specific bitrate: ").strip()

    return choice, url, quality

def main(playlist=None, song=None, album=None, quality=None, min_views=None, max_length=None, disable_threading=False):

    print(f"\n{colours.CVIOLETBG2}Chosen Settings{colours.ENDC}\n")

    if playlist:
        print(f"{colours.OKGREEN}Playlist{colours.ENDC}: {playlist}")

    if song:
        print(f"{colours.OKGREEN}Song{colours.ENDC}: {song}")

    if album:
        print(f"{colours.OKGREEN}Album{colours.ENDC}: {album}")

    if quality:
        bitrate = get_bitrate_from_quality(quality)
        print(f"{colours.OKGREEN}Song quality / bitrate{colours.ENDC}: {quality} / {bitrate} bps")

    if min_views != DEFAULT_MIN_VIEWS_FOR_DOWNLOAD:
        print(f"{colours.OKGREEN}Minimum view count{colours.ENDC}: {min_views}")

    if max_length != DEFAULT_MAX_LENGTH_FOR_DOWNLOAD:
        print(f"{colours.OKGREEN}Maximum video length{colours.ENDC}: {max_length}")
    
    if disable_threading:
        print(f"{colours.WARNING}Threading is disabled. Downloads may be slower.{colours.ENDC}")

    downloader = SpotifyDownloader(get_bitrate_from_quality(quality), max_length, min_views)

    success = False

    if(song):
        success =downloader.download_track(song)
    elif(playlist):
        success =downloader.download_playlist(playlist)  
    elif(album):
        success =downloader.download_album(album)

    downloader.rm_tmp_folder()

    if(success):
        print(f"\n{colours.OKGREEN}Download complete!{colours.ENDC} (check downloads folder)\n\n")
    else:
        print(f"\n{colours.FAIL}Download failed!{colours.ENDC} If you need help, please visit https://github.com/couldbejake/spotify2mp3/issues\n\n")

if __name__ == "__main__":

    if len(sys.argv) > 1:

        parser = argparse.ArgumentParser(description="spotify2mp3: Download songs from Spotify by searching them on YouTube and converting the audio.")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-p", "--playlist", "--list", help="Specify a playlist URL or ID to download", type=str)
        group.add_argument("-s", "--song", "--single", help="Specify a song URL or ID to download", type=str)
        group.add_argument("-a", "--album", help="Specify an album URL or ID to download", type=str)

        parser.add_argument("-q", "--quality", help="Specify the song download quality or bitrate", type=validate_quality, default="high")
        parser.add_argument("--min-views", help="Minimum view count on YouTube", type=int, default=DEFAULT_MIN_VIEWS_FOR_DOWNLOAD)
        parser.add_argument("--max-length", help="Maximum video length on YouTube in minutes", type=int, default=DEFAULT_MAX_LENGTH_FOR_DOWNLOAD)
        parser.add_argument("--disable-threading", help="Disables multiple threads to download songs.", action="store_true")

        args = parser.parse_args()

        # Validate the URL
        try:
            if args.song:
                assert validate_spotify_url(args.song) == 'song'
            if args.playlist:
                assert validate_spotify_url(args.playlist) == 'playlist'
            if args.album:
                assert validate_spotify_url(args.album) == 'album'

        except (AssertionError, ValueError) as e:
            print(f"{colours.FAIL}Error: {e}{colours.ENDC}")
            sys.exit(1)

        if not (args.song or args.playlist or args.album):
            print(f"{colours.FAIL}Error: You must specify a song, playlist, or album to download.{colours.ENDC}")
            parser.print_help()
            sys.exit(1)

        main(playlist=args.playlist, song=args.song, album=args.album, quality=args.quality, min_views=args.min_views, max_length=args.max_length, disable_threading=args.disable_threading)

    else:  # If no command-line arguments are provided, use wizard mode.
        display_splash()
        choice, url, quality = get_user_input()
        if choice == 'song':
            main(song=url, quality=quality, min_views=DEFAULT_MIN_VIEWS_FOR_DOWNLOAD, max_length=DEFAULT_MAX_LENGTH_FOR_DOWNLOAD)
        elif choice == 'playlist':
            main(playlist=url, quality=quality, min_views=DEFAULT_MIN_VIEWS_FOR_DOWNLOAD, max_length=DEFAULT_MAX_LENGTH_FOR_DOWNLOAD)
        else:
            main(album=url, quality=quality, min_views=DEFAULT_MIN_VIEWS_FOR_DOWNLOAD, max_length=DEFAULT_MAX_LENGTH_FOR_DOWNLOAD)
