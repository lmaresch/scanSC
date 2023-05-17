#!/usr/bin/env python3
import glob
import json
import os
import sys
import eyed3
import urllib3
import xmltodict

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
        mp3 = eyed3.load(f)
    except:
        print("Error opening file {0}".format(f))
        notWorking.append(f)
        continue
    print("Artist: {0} - song: {1}".format(mp3.tag.artist, mp3.tag.title))
    print("Cover: {0}".format(mp3.tag.images))
    fullSearchUrl = "{0}{1} {2}".format(searchUrl, mp3.tag.artist, mp3.tag.title)
    print(fullSearchUrl)
    response = urllib3.request('GET', fullSearchUrl)
    print("Status: {0}".format(response.status))
    print("Select entry:")
    i = 0
    entries = []
    for line in response.data.decode('utf-8').split("\n"):
        if '<li><h2><a href="' in line:
            xmldict = xmltodict.parse(line, xml_attribs = True)
            link = xmldict['li']['h2']['a']['@href']
            song = xmldict['li']['h2']['a']['#text']
            entries.append(dict(url = link, song = song))
            print("{0}: {1}".format(i, song))
            i += 1
    selectedEntry = -1
    print(str(mp3.tag))
    while True:
        selection = input('Enter number between 0 and {0} or \'q\' to quit: '.format(len(entries) - 1))
        if selection == 'q':
            print('User selected \'q\' - exiting')
            quit()
        try:
            selectedEntry = int(selection)
            break
        except:
            print("{0} is not a valid value.".format(selection))
    print(entries[selectedEntry])
    fullSearchUrl = "{0}{1}".format(baseUrl, entries[selectedEntry]['url'])
    print(fullSearchUrl)
    response = urllib3.request('GET', fullSearchUrl)
    print("Status: {0}".format(response.status))
    cover = None
    jsonString = None
    for line in response.data.decode('utf-8').split('\n'):
        if '<script>window.__sc_hydration = ' in line:
            jsonString = line.replace('<script>window.__sc_hydration = ', '').replace(';</script>', '')
    #print('JSON: {0}'.format(jsonString))
    jsonObj = json.loads(jsonString)
    for entry in  jsonObj:
        if entry['hydratable'] == 'sound':
            data = entry['data']
            for tagName in data.keys():
                if tagName == 'artwork_url':
                    print(data[tagName])
                    mp3.tag.images.set(3, None, 'image/png', img_url = data[tagName])
                    mp3.tag.save()
                elif tagName == 'created_at':
                    print(data[tagName])
                    mp3.tag.release_date = data[tagName][0:4]
                    mp3.tag.save()
                elif tagName == 'genre':
                    print(data[tagName])
                    mp3.tag.genre = data[tagName]
                    mp3.tag.save()
                elif tagName == 'label_name':
                    print(data[tagName])