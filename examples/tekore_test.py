import tekore as tk

spotify = tk.Spotify()

userToken = None # User token

def get_stored_creds():
    global userToken
    (spotifyClientId, spotifyClientSecret, spotifyReturnUri, refreshToken) = tk.config_from_file('tekore_cfg.ini', return_refresh=True)
    cred = tk.Credentials(spotifyClientId, spotifyClientSecret, spotifyReturnUri)

    # Refresh token available
    if refreshToken is None or refreshToken == '':
        raise ValueError('RefreshToken not available in tekore_cfg.ini. Run login.py first.')
    userToken = cred.refresh_user_token(refreshToken)
    
def get_album(album_id):
    # Return early if no login
    if userToken is None:
        raise RuntimeError("Not logged in. Run login.py first")

    try:
        with spotify.token_as(userToken):
            album = spotify.album(album_id)

        return {
            "tracks": [
                {
                    "name": track.name
                }
            for track in album.tracks.items]
        }
    except tk.HTTPError:
        return "Error in retrieving album!", 400
    
def get_playlist(playlist_id):
    # Return early if no login
    if userToken is None:
        raise RuntimeError("Not logged in. Run login.py first")

    try:
        with spotify.token_as(userToken):
            pages = spotify.playlist_items(playlist_id, limit=100)
            playlist = spotify.all_items(pages)
            
            return {
                "tracks": [
                    {
                        "name": item.track.name,
                        "artists": ','.join([artist.name for artist in item.track.artists]),
                    }
                for item in playlist]
            }
    except tk.HTTPError:
        return "Error in retrieving playlist!", 400
        
def get_liked_playlist():
    # Return early if no login
    if userToken is None:
        raise RuntimeError("Not logged in. Run login.py first")

    try:
        with spotify.token_as(userToken):
            pages = spotify.saved_tracks('from_token', limit=50)
            playlist = spotify.all_items(pages)
            
            return {
                "tracks": [
                    {
                        "name": item.track.name,
                        "artists": ','.join([artist.name for artist in item.track.artists]),
                    }
                for item in playlist]
            }
    except tk.HTTPError:
        return "Error in retrieving playlist!", 400

def main():
    global userToken

    get_stored_creds()
    
    # Supposedly this doesn't happen
    # if userToken.is_expiring:
    #     userToken = cred.refresh(userToken)

    playlist = get_liked_playlist()
    print(playlist)


if __name__ == '__main__':
    main()
