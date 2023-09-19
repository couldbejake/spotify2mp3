from exceptions import ConfigVideoLowViewCount, ConfigVideoMaxLength, YoutubeItemNotFound
from pytube import YouTube as pytubeYouTube
from pytube import Playlist as pytubePlaylist
from youtube_search import YoutubeSearch
import json

import re


class YouTube:
    def __init__(self):
        pass

    # TODO: Make videos to search configurable via parameter
    def search(self, search_query, max_length, min_view_count, search_count = 3):
        youtube_results = YoutubeSearch(search_query, max_results=search_count).to_json()

        if len(json.loads(youtube_results)['videos']) < 1:
            raise YoutubeItemNotFound('Skipped song -- Could not load from YouTube')

        youtube_videos = json.loads(youtube_results)['videos']
        videos_meta = []

        for video in youtube_videos:
            youtube_video_duration = video['duration'].split(':')
            youtube_video_duration_seconds = int(youtube_video_duration[0]) * 60  + int(youtube_video_duration[1])

            youtube_video_views = re.sub('[^0-9]','', video['views'])
            youtube_video_viewcount_safe = int(youtube_video_views) if str(youtube_video_views).isdigit() else 0

            videos_meta.append((video, youtube_video_duration_seconds, youtube_video_viewcount_safe))

        sorted_videos = sorted(videos_meta, key=lambda vid: vid[2], reverse=True) # Find top N videos with the most views
        chosen_video = sorted_videos[0][0]

        youtube_video_link = "https://www.youtube.com" + chosen_video['url_suffix']

        if(youtube_video_duration_seconds >= max_length):
            raise ConfigVideoMaxLength(f'Skipped song due to MAX_LENGTH value in script {youtube_video_link}')

        if(youtube_video_viewcount_safe <= min_view_count):
            raise ConfigVideoLowViewCount(f'Skipped song due to MIN_VIEW_COUNT value in script {youtube_video_link}')
    
        return youtube_video_link
    
    def download(self, url, audio_bitrate):
        youtube_video = pytubeYouTube(url)
        if youtube_video.age_restricted:
            youtube_video.bypass_age_gate()
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