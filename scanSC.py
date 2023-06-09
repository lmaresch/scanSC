#!/usr/bin/env python3
import glob
import json
import os
import sys
import eyed3
import urllib
import urllib3
import xmltodict
import re

wd = os.getcwd()
baseUrl = 'https://soundcloud.com'
searchUrl = "{0}/search?q=".format(baseUrl)
overrideCover = False
print(sys.argv)
if __name__ == '__main__' and len(sys.argv) > 1:
    for arg in sys.argv:
        if arg.startswith('-'):
            if arg == '-O':
                overrideCover = True
        elif arg == sys.argv[0]:
            continue
        else:
            wd = arg
            break
print("Working in directory {0}".format(wd))
files = [f for f in glob.glob(os.path.join(wd, '**', '*.mp3'), recursive=True)]
notWorking = []
for f in files:
    if '/._' in f:
        continue
    print('-------------------------------------------------------')
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
    print("Cover: {0}".format(len(mp3.tag.images)))
    if not overrideCover and len(mp3.tag.images) > 0:
        print('Cover already exists, proceeding to next file')
        continue
    fullSearchUrl = ''
    if len(mp3.tag.comments) > 0 and 'http' in mp3.tag.comments[0].text and 'soundcloud' in mp3.tag.comments[0].text:
        print("Comments: {0}".format(mp3.tag.comments[0].text))
        fullSearchUrl = mp3.tag.comments[0].text
    else:
        httpSearch = urllib.parse.quote("{0} {1}".format(mp3.tag.artist, re.sub(" [\[\(].*[\]\)]", "", mp3.tag.title)))
        fullSearchUrl = "{0}{1}".format(searchUrl, httpSearch)
        print(fullSearchUrl)
        response = urllib3.request('GET', fullSearchUrl)
        print("Status: {0}".format(response.status))
        print("Select entry:")
        i = 0
        entries = []
        for line in response.data.decode('utf-8').split("\n"):
            if '<li><h2><a href="' in line:
                xmldict = None
                try:
                    xmldict = xmltodict.parse(line, xml_attribs = True)
                except:
                    continue
                link = xmldict['li']['h2']['a']['@href']
                song = xmldict['li']['h2']['a']['#text']
                entries.append(dict(url = link, song = song))
                print("{0}: {1} -- {2}".format(i, song, link))
                i += 1
        selectedEntry = -1
        if len(entries) < 1:
            input('Search didn\'t find anything, proceeding with next file. Press Enter to continue.')
            continue
        next = False
        while True:
            selection = input('Enter number between 0 and {0}, \'n\' for next or \'q\' to quit: '.format(len(entries) - 1))
            if selection == 'q':
                print(*notWorking, sep='\n')
                print('User selected \'q\' - exiting')
                quit()
            if selection == 'n':
                next = True
                break
            try:
                selectedEntry = int(selection)
                break
            except:
                print("{0} is not a valid value.".format(selection))
        if next:
            continue
        print(entries[selectedEntry])
        fullSearchUrl = "{0}{1}".format(baseUrl, entries[selectedEntry]['url'])
    print(fullSearchUrl)
    response = urllib3.request('GET', fullSearchUrl)
    print("Status: {0}".format(response.status))
    if not response.status == 200:
        print('Could not retrieve page, continue with next file')
        continue
    cover = None
    jsonString = None
    bigPicUrl = ''
    smallPicUrl = ''
    for line in response.data.decode('utf-8').split('\n'):
        if '<img src="' in line:
            bigPicUrl = re.sub('".*', '', line.strip().replace('<img src="', ''))
            print('Big picture: {0}'.format(bigPicUrl))
        if '<script>window.__sc_hydration = ' in line:
            jsonString = line.replace('<script>window.__sc_hydration = ', '').replace(';</script>', '')
    jsonObj = json.loads(jsonString)
    for entry in  jsonObj:
        if entry['hydratable'] == 'sound':
            data = entry['data']
            for tagName in data.keys():
                if tagName == 'artwork_url' and data[tagName] is not None:
                    smallPicUrl = data[tagName]
                    print('Small picture: {0}'.format(smallPicUrl))
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
    picUrl = ''
    if len(bigPicUrl) > 0:
        picUrl = bigPicUrl
        print('Using big picture')
    elif len(smallPicUrl) > 0:
        picUrl = smallPicUrl
        print('Using small picture')
    if len(picUrl) > 0:
        mimeType = 'jpeg'
        if '.png' in picUrl:
            mimeType = 'png'
        http = urllib3.PoolManager()
        r = http.request(method = 'GET', url = picUrl)
        mp3.tag.images.set(3, r.data, 'image/{0}'.format(mimeType))
        mp3.tag.save()
print(*notWorking, sep='\n')