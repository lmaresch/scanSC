#!/usr/bin/env python3
import glob
import os
import sys
from mp3_tagger import MP3File
import urllib3

wd = os.getcwd()
baseUrl = 'https://soundcloud.com'
searchUrl = "{0}/search?q=".format(baseUrl)
if __name__ == '__main__' and len(sys.argv) > 1:
    wd = sys.argv[1]
print("Working in directory {0}".format(wd))
files = [f for f in glob.glob(os.path.join(wd, '**', '*.mp3'), recursive=True)]
notWorking = []
for f in files:
    print(f)
    mp3 = None
    tags = None
    try:
        mp3 = MP3File(f)
        tags = mp3.get_tags()
    except:
        print("Error opening file {0}".format(f))
        notWorking.append(f)
        continue
    print(tags)
    id3Version = 'ID3TagV2'
    print("V1: {0}".format(len(tags[id3Version])))
    if not id3Version in tags or len(tags[id3Version]) == 0:
        id3Version = 'ID3TagV1'
    print("id3Version: {0}".format(id3Version))
    print("Artist: {0} - song: {1}".format(tags[id3Version]['artist'], tags[id3Version]['song']))
    fullSearchUrl = "{0}{1} {2}".format(searchUrl, tags[id3Version]['artist'], tags[id3Version]['song'])
    print(fullSearchUrl)
    response = urllib3.request('GET', fullSearchUrl)
    print("Status: {0}".format(response.status))
    for line in response.data.decode('utf-8').split("\n"):
        if '<li><h2><a href="' in line:
            print(line)