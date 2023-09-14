import tekore as tk
from your_secrets import spotify_clientid, spotify_clientsecret
from flask import Flask, request, redirect, session
from pprint import pprint

(cid, csec, ruri) = tk.config_from_file('tekore_cfg.ini', return_refresh=False)
cred = tk.Credentials(cid, csec, ruri)
spotify = tk.Spotify()

auths = {}  # Ongoing authorisations: state -> UserAuth
users = {}  # User tokens: state -> token (use state as a user ID)

in_link = '<a href="/login">login</a>'
out_link = '<a href="/logout">logout</a>'
login_msg = f'You can {in_link} or {out_link}'

def app_factory() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'aliens'

    @app.route('/', methods=['GET'])
    def main():
        user = session.get('user', None)
        token = users.get(user, None)

        # Return early if no login or old session
        if user is None or token is None:
            session.pop('user', None)
            return f'User ID: None<br>{login_msg}'

        page = f'User ID: {user}<br>{login_msg}'
        if token.is_expiring:
            token = cred.refresh(token)
            users[user] = token

        try:
            with spotify.token_as(token):
                playback = spotify.playback_currently_playing()

            item = playback.item.name if playback else None
            page += f'<br>Now playing: {item}'
        except tk.HTTPError:
            page += '<br>Error in retrieving now playing!'

        return page

    @app.route('/login', methods=['GET'])
    def login():
        if 'user' in session:
            return redirect('/', 307)

        scope = tk.scope.every
        auth = tk.UserAuth(cred, scope)
        auths[auth.state] = auth
        return redirect(auth.url, 307)

    @app.route('/logout', methods=['GET'])
    def logout():
        uid = session.pop('user', None)
        if uid is not None:
            users.pop(uid, None)
        return redirect('/', 307)
    
    @app.route('/callback', methods=['GET'])
    def login_callback():
        code = request.args.get('code', None)
        state = request.args.get('state', None)
        auth = auths.pop(state, None)

        if auth is None:
            return 'Invalid state!', 400

        token = auth.request_token(code, state)
        session['user'] = state
        users[state] = token

        # new_conf = (None, None, None, token.refresh_token)
        # tk.config_to_file('tekore_cfg.ini', new_conf)    

        return redirect('/', 307)
    
    @app.route('/album/<album_id>', methods=['GET'])
    def get_album(album_id):
        user = session.get('user', None)
        token = users.get(user, None)

        # Return early if no login or old session
        if user is None or token is None:
            session.pop('user', None)
            return f'User ID: None<br>{login_msg}'

        if token.is_expiring:
            token = cred.refresh(token)
            users[user] = token

        try:
            with spotify.token_as(token):
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
    
    @app.route('/playlist/<playlist_id>', methods=['GET'])
    def get_playlist(playlist_id):
        user = session.get('user', None)
        token = users.get(user, None)

        # Return early if no login or old session
        if user is None or token is None:
            session.pop('user', None)
            return f'User ID: None<br>{login_msg}'

        if token.is_expiring:
            token = cred.refresh(token)
            users[user] = token

        try:
            with spotify.token_as(token):
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
        
    
    @app.route('/playlist/liked', methods=['GET'])
    def get_liked_playlist():
        user = session.get('user', None)
        token = users.get(user, None)

        # Return early if no login or old session
        if user is None or token is None:
            session.pop('user', None)
            return f'User ID: None<br>{login_msg}'

        if token.is_expiring:
            token = cred.refresh(token)
            users[user] = token

        try:
            with spotify.token_as(token):
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

    return app


if __name__ == '__main__':
    application = app_factory()
    application.run('127.0.0.1', 5000)
