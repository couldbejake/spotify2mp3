from exceptions import ConfigVideoLowViewCount, ConfigVideoMaxLength, YoutubeItemNotFound
from pytube import YouTube as pytubeYouTube
from pytube import Playlist as pytubePlaylist
from youtube_search import YoutubeSearch
import json

import re


class YouTube:
    def __init__(self):
        pass

    def search(self, search_query, max_length, min_view_count):
        youtube_results = YoutubeSearch(search_query, max_results=1).to_json()

        if len(json.loads(youtube_results)['videos']) < 1:
            raise YoutubeItemNotFound('Skipped song -- Could not load from YouTube')

        youtube_first_video = json.loads(youtube_results)['videos'][0]

        youtube_video_duration = youtube_first_video['duration'].split(':')
        youtube_video_duration_seconds = int(youtube_video_duration[0]) * 60  + int(youtube_video_duration[1])

        youtube_video_views = re.sub('[^0-9]','', youtube_first_video['views'])
        youtube_video_viewcount_safe = int(youtube_video_views) if str(youtube_video_views).isdigit() else 0

        youtube_video_link = "https://www.youtube.com" + youtube_first_video['url_suffix']

        if(youtube_video_duration_seconds >= max_length):
            raise ConfigVideoMaxLength('Skipped song due to MAX_LENGTH value in script')

        if(youtube_video_viewcount_safe <= min_view_count):
            raise ConfigVideoLowViewCount('Skipped song due to MIN_VIEW_COUNT value in script')
    
        return youtube_video_link
    
    def download(self, url, audio_bitrate):

        youtube_video = pytubeYouTube(url)
        youtube_video_streams = youtube_video.streams.filter(only_audio=True, file_extension='mp4')

        correctIndex = 0

        selected_bitrate_normalised = audio_bitrate / 1000

        for i,vid in enumerate(youtube_video_streams):
            currKbps = int(re.sub("[^0-9]", "", vid.abr))
            if currKbps < selected_bitrate_normalised:
                correctIndex = i

        video_stream = youtube_video_streams[correctIndex]

        yt_tmp_out = video_stream.download(output_path="./temp/")

        return yt_tmp_out