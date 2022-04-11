import eyed3
from eyed3.id3.frames import ImageFrame


audiofile = eyed3.load('temp/All Because of You Bill Withers.mp3')
if (audiofile.tag == None):
    audiofile.initTag()
audiofile.tag.images.set(ImageFrame.FRONT_COVER, open('temp/All Because of You Bill Withers.jpg', 'rb').read(), 'image/jpg')
audiofile.tag.save()
