import os
import tekore as tk
from flask import Flask, request, redirect
import threading
import webbrowser
import uuid

spotify = tk.Spotify()

userToken = None  # User token
cred = None  # credentials object for doing token ops
auths = {}  # Auth attempts. Stores data across spotify login

cfg_filename = 'tekore_cfg.ini'
app_host = "localhost"
app_port = 5000
app_url = f'http://{app_host}:{app_port}'
login_redirect_url = f'{app_url}/callback'

spotify_app_link = 'https://developer.spotify.com/dashboard/create'
spotify_app_prompt = f"""
To access spotify, you need to create a developer 'application' associated with your spotify account.
<br>Open <a target="_blank" href="https://accounts.spotify.com">spotify</a> in your browser and login.
<br>Then click <a target="_blank" href="{spotify_app_link}">here</a> to create an application (only do this once).
<br>For the 'Redirect Uri' supply the string "{login_redirect_url}"
<br>
<br>After the client is created, click on "Settings" to find the "Client ID" and "Client Secret"
<br>Paste those two fields below and click Grant Permission to allow this tool access to the client you just created.
<br><br>
<form action="/submit_creds">
  <label for="cid">Client ID:</label>
  <input type="text" id="cid" name="cid"><br><br>
  <label for="csec">Client Secret:</label>
  <input type="password" id="csec" name="csec"><br><br>
  <input type="submit" value="Grant Permission">
</form> 
"""
login_prompt = 'Grant permission to access spotify by clicking <a href="/login">here</a> or click <a href="/logout">here</a> to start over.'
complete_prompt = '<br><br>You may now close this screen. Or click <a href="/logout">here</a> to start over'


def does_config_exist():
    return os.path.exists(cfg_filename)


def get_stored_creds():
    global userToken, cred
    (spotifyClientId, spotifyClientSecret, spotifyReturnUri,
     refreshToken) = tk.config_from_file('tekore_cfg.ini', return_refresh=True)
    cred = tk.Credentials(
        spotifyClientId, spotifyClientSecret, spotifyReturnUri)

    # Refresh token available
    if refreshToken is not None and refreshToken != '':
        userToken = cred.refresh_user_token(refreshToken)


def app_factory() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = uuid.uuid4()

    @app.route('/', methods=['GET'])
    def main():
        global userToken

        # Setup prompt
        if not does_config_exist():
            return spotify_app_prompt

        # Try to get clientid/clientsecret/refreshtoken
        get_stored_creds()

        # Get user to login to retrieve refresh token
        if userToken is None:
            return login_prompt

        if userToken.is_expiring:
            userToken = cred.refresh(userToken)

        # Test that token works
        try:
            with spotify.token_as(userToken):
                topTracks = spotify.current_user_top_tracks()

            item = topTracks.items[0]
            page = f'It worked! Your Top Track is: {item.name} by {item.artists[0].name}'
        except tk.HTTPError:
            page = '<br>Error retrieving user information!'

        return page + complete_prompt

    @app.route('/submit_creds', methods=['GET'])
    def submit_creds():
        args = request.args
        if len(args) == 0 or args['cid'] == '' or args['csec'] == '':
            return 'Invalid information entered. Click <a href="/">here</a> to try again.'

        # Store clientId, clientSecret, and redirectUri
        new_conf = (args['cid'], args['csec'], login_redirect_url, None)
        tk.config_to_file(cfg_filename, new_conf)

        # Retrieve those creds
        get_stored_creds()

        return redirect('/login', 307)

    @app.route('/login', methods=['GET'])
    def login():
        scope = tk.scope.every
        auth = tk.UserAuth(cred, scope)
        auths[auth.state] = auth
        return redirect(auth.url, 307)

    @app.route('/logout', methods=['GET'])
    def logout():
        global userToken

        # Erase config
        os.remove(cfg_filename)

        # Logout
        userToken = None

        return redirect('/', 307)

    @app.route('/callback', methods=['GET'])
    def login_callback():
        global userToken

        code = request.args.get('code', None)
        state = request.args.get('state', None)
        auth = auths.pop(state, None)

        if auth is None:
            return 'Invalid login state!', 400

        userToken = auth.request_token(code, state)

        # Store refresh token
        new_conf = (None, None, None, userToken.refresh_token)
        tk.config_to_file(cfg_filename, new_conf)

        return redirect('/', 307)

    return app


if __name__ == '__main__':
    application = app_factory()
    threading.Timer(1.25, lambda: webbrowser.open(app_url)).start()
    application.run(app_host, app_port)
