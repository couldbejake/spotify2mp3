# Dockify2mp3

A dockerized service helping with downloads of mp3 files from spotify

## Building the image

Build can last quite some time... Be patient.

```
git clone https://github.com/davidgiesemann/dockify2mp3.git
cd dockify2mp3
docker build . -t dockify2mp3
```

## Using the image

```
docker run -it -v C:/downloads:/downloads dockify2mp3 sh
python spotify2mp3.run
```
