# spotify2mp3
Simple free and unlimited spotify playlist downloads

![An image showing the Spotify To MP3 script Running](https://i.imgur.com/bxGQCt6.png)

HOWTO:

- Install the packages required by the application using `$ pip3 install -r requirements.txt`
- Enter your playlist ID at the bottom of the script
- Run the script using `python3 run.py`

How does it work?

- We first search the playlist and download a list of songs
- We then look up each song on Youtube, download it as an mp4, then convert it to an mp3 and store it in a folder!
