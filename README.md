<div align="center">

  <img src="assets/logo.png" alt="logo" width="200" height="auto" />
  <h1>Spotify2mp3</h1>
  
  <p>
    Simple free and unlimited Spotify MP3 playlist downloads
  </p>
  
  
<!-- Badges -->
<p>
  <a href="https://github.com/couldbejake/spotify2mp3/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/couldbejake/spotify2mp3" alt="contributors" />
  </a>
  
  <a href="">
    <img src="https://img.shields.io/github/last-commit/couldbejake/spotify2mp3" alt="last update" />
  </a>
  
  <a href="https://github.com/couldbejake/spotify2mp3/network/members">
    <img src="https://img.shields.io/github/forks/couldbejake/spotify2mp3" alt="forks" />
  </a>
  
  <a href="https://github.com/couldbejake/spotify2mp3/stargazers">
    <img src="https://img.shields.io/github/stars/couldbejake/spotify2mp3" alt="stars" />
  </a>
  
  <a href="https://github.com/couldbejake/spotify2mp3/issues/">
    <img src="https://img.shields.io/github/issues/couldbejake/spotify2mp3" alt="open issues" />
  </a>
  
  <!--
  <a href="https://github.com/couldbejake/awesome-readme-template/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/couldbejake/awesome-readme-template.svg" alt="license" />
  </a>-->
</p>
   
<h4>
    <a href="https://github.com/couldbejake/spotify2mp3/wiki">Documentation</a>
  <span> · </span>
    <a href="https://github.com/couldbejake/spotify2mp3/issues">Report Bug</a>
  <span> · </span>
    <a href="https://github.com/couldbejake/spotify2mp3/issues/new">Request Feature</a>
  </h4>
</div>

<!-- Getting Started -->
## 	:toolbox: Getting Started

<!-- Prerequisites -->
### :bangbang: Prerequisites

Ideally use **Python 3.8.0** but works down to Python 3.1.0

<!-- Run Locally -->
### :running: Run Locally

Clone the project

`$ git clone https://github.com/couldbejake/spotify2mp3.git`

<!-- Installation -->
### :gear: Installation

Go to the project directory

`$ cd spotify2mp3 `

Install desired packages using PIP 3.8

`$ pip3.8 install -r requirements.txt`

Run the script

`$ python3.8 run.py`


## Extra configuration

Inside `run.py` you can modify several variables to change how the script operates:

- `MIN_VIEW_COUNT`: The variable that indicates how many views a video has to have before it can be used, defaults to  5000 (meaning songs with less than 5000 views will be ignored and the song will be skipped)
- `MAX_LENGTH`: The maximum length a song can be and still be downloaded, defaults to  600 seconds or 10 minutes (meaning only songs shorter than 10 mins will be downloaded)
- `FAILURE_THRESHOLD`: The number of songs that need to fail before prompting to re-run with a lower view count, defaults to 5 (meaning 5 songs or more must fail for user to be prompted)

## Getting spotify playlist URL

When prompted for a spotify URL link you will want to go to the [spotify web player](https://open.spotify.com/) and navigate to your playlist. The URL will be in the form `https://open.spotify.com/playlist/<URL Link>` you have two options:

1. Copy-paste the entire URL
2. Copy **just** the URL link (should just be letters and numbers), and paste that into the prompt


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=couldbejake/spotify2mp3&type=Date)](https://github.com/couldbejake/spotify2mp3/)

## Troubleshooting

If you get the error 'could not find match for ^\w+\W' install this temporary patch by JazPin;

`pip3 uninstall pytube`

`python3 -m pip install git+https://github.com/JazPin/pytube`
