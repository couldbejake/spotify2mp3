class AppOptions:
    def __init__(self, authtype=None, playlist=None, song=None, album=None, private_playlist=False, liked=False, quality=None, min_views=None, max_length=None, disable_threading=False):
        self.authtype = authtype
        self.playlist = playlist
        self.song = song
        self.album = album
        self.private_playlist = private_playlist
        self.liked = liked
        self.quality = quality
        self.min_views = min_views
        self.max_length = max_length
        self.disable_threading = disable_threading