#!/usr/local/bin/python

# 13 Aug 17 version
# Merging with afplay version
# 5 Aug 17 version
# Modified to run on Raspberry Pi using omxplayer instead of afplay
# Found bug - cannot cope with brackets in file names - FIXED!
# - cannot cope with ampersands either! - FIXED
# - make titles longer - FIXED
# - add support for .OGG audio files - FIXED

# If using GUI change clock display to show seconds with %X format.

# PyPlay radio playout script by Giles Booth @blogmwiki
# Written in Python2. Should not require any other modules to be installed.
# Requires audio files in same directory as this script.
# Original version ran on Mac using afplay. Written in Python2 to run on 
# MacOS X without installing Python3
# In OS X as uses afplay to play audio files
# In Linux we use the omxplayer.

# V 4.1 has horrible kludge to cope with multiple backslashes in array
# Version 4 fixes bugs replacing escaped spaces in display names and
# copes with filenames with apostrophes.
# Version 3 fixes bug playing files with spaces in file names
# makes an M3U file from audio files in directory if no playlist.m3u file found
# also fixes a bug with out time when crossing hour.

import os
import os.path
import time
import subprocess
import re
import datetime
import sys

playlist = ""

# \033[7m is code for inverse video
# \033[0m is normal video
# \033[31m is red video

# function to display tracks, durations, playing status & out time
def showTracks():
    os.system('clear')
    t = str(datetime.datetime.now().time())
    t = t[0:8]
    print '\033[37;44mWelcome to PyPlay!     \t\t\tUpdated ',t,'\033[0m'
    print ''
    print '\033[0;30;47m  # File name                           Length  Status  Out time \033[0m'
    for z in range(len(trackList)):
        highlightOn = ""
        highlightOff = ""
        if "PLAYING" in trackList[z][4]:
            highlightOn = "\033[31;103m"
            highlightOff = "\033[0m"
        print highlightOn, leadingSpace(str(z+1)), trackList[z][1], "\t", timeLeadingSpace(trackList[z][3]), "\t", trackList[z][4], highlightOff
    
# function to display the user commands
def showUI():
    if sys.platform.startswith('linux'):
        # Linux platform
        print '\033[97;42m    KEYS:    q stop | - + vol | space pause | arrows seek        \033[0m'
    elif sys.platform == 'darwin':
        # Mac OSX platform
        print '\033[0,34mPress ctrl+c to stop playing, q to quit\033[0m'
    else:
        # Unsupported platform
        raise RuntimeError('Sorry the {0} platform is not supported by PyPlay'.format(sys.platform))

# returns duration of track in seconds
def getTrackLength(thing):
    bumf = ""
    bumfList = []
    trackLength = ""
    snog = trackArray[thing]
    #foo = "omxplayer -i " + snog

    if sys.platform.startswith('linux'):
            # Linux platform
            foo = "no_omxplayer -i " + snog
            try:
                bumf = subprocess.check_output(foo, shell=True, stderr=subprocess.STDOUT)
            except OSError:
                print "%s not found on path" % foo
                trackSecs = 0
            except Exception, e:
                bumf = str(e.output) # horrible kludge to get round exceptions but capture text
                bumfList = bumf.split('\n')

                for line in bumfList:
                    #        print line # debug line
                    if line.startswith('  Duration'):
                        line_mins = int(line[15:17])
                        line_secs = int(line[18:20])
                        trackSecs = line_secs + (line_mins*60)
    elif sys.platform == 'darwin':
            # Mac OSX platform
            foo = "afinfo " + snog

            bumf = subprocess.check_output(foo, shell=True)
            bumfList = bumf.split('\n')
            for line in bumfList:
                if line.startswith('estimated duration'):
                    duration = line
                    trackLength = re.findall(r"[-+]?\d*\.\d+|\d+", duration)
                    trackSecs = float(trackLength[0])
    else:
            # Unsupported platform
            raise RuntimeError('Sorry the {0} platform is not supported by PyPlay'.format(sys.platform))
    return trackSecs

# returns string with out time in HH:MM:SS format
def getEndTime(tk):
    tkDuration = trackList[tk-1][2]
    timeNow = str(datetime.datetime.now().time())
    timeHour = timeNow[0:2]
    timeMin = timeNow[3:5]
    timeSec = timeNow[6:8]
    tH = int(timeHour)
    tM = int(timeMin)
    tS = int(timeSec)
    tkS = tkDuration % 60
    tkM = (tkDuration - tkS) / 60
    endSec = int(round(tS+tkS, 0))
    endMin = int(tM + tkM)
    endHour = int(tH)
    if endSec > 59:
        endMin += 1
        endSec = endSec % 60
    if endMin > 59:
        endHour += 1
        endMin = endMin % 60
    endHourString = leadingZero(str(endHour))
    endMinString = leadingZero(str(endMin))
    endSecString = leadingZero(str(endSec))
    endTime = endHourString + ":" + endMinString + ":" + endSecString
    return str(endTime)

# adds a leading 0 to single character strings
def leadingZero(n):
    if len(n) == 1:
            n = '0' + n
    return n

# adds a leading space to single character strings
def leadingSpace(n):
    if len(n) == 1:
            n = ' ' + n
    return n

# adds a leading space to times shorter than 10 minutes
def timeLeadingSpace(n):
    if len(n) == 4:
            n = ' ' + n
    return n

# makes strings a fixed length
def colform(txt, width):
    if len(txt) > width:
        txt = txt[:width]
    elif len(txt) < width:
        txt = txt + (" " * (width - len(txt)))
    return txt

# returns the track length in a string M:SS format
def displayDuration(s):
    disTime = int(s)
    sec = disTime % 60
    m = (disTime - sec)/60
    secString = leadingZero(str(sec))
    t = str(m) + ":" + secString
    return t

# sets playing status for all tracks to empty string
def clearStatus():
    for y in range(len(trackList)):
        trackList[y][4] = ''

# plays the track using OS X afplay command or omxplayer on Linux/Raspberry Pi
# You could try VLC or MPD if using Linux
def playTrack(track):
    song = trackArray[track-1]
    if sys.platform.startswith('linux'):
            # Linux platform
            trackString = "omxplayer " + song + " > /dev/null"  # stop omxplayer output appearing on screen whilst playing
    elif sys.platform == 'darwin':
            # Mac OSX platform
            trackString = "afplay " + song + " > /dev/null"  # stop afplay output appearing on screen whilst playing
    else:
            # Unsupported platform
            raise RuntimeError('Sorry the {0} platform is not supported by PyPlay'.format(sys.platform))

    os.system(trackString)

# if no playlist.m3u file found, make one from audio files found in directory
# edit audioFileTypes list to add more file types as needed (but don't add 'aif' because reasons)
if not os.path.exists('playlist.m3u'):
    # audioFileTypes should be set accordint to the play cmd but this way the .m3u file is not missing ogg music
    audioFileTypes = ['.mp3','.MP3','.wav','.WAV','.m4a','.M4A','.aiff','.AIFF','.ogg','.OGG']
    # TODO: check if the player can play the file type.
    os.system('clear')
    print "No playlist.m3u file found so I am making you one with these files:"
    print
    dirList = os.listdir(".")
    newDir = []
    for x in range(len(dirList)):
        for q in audioFileTypes:
            if q in dirList[x]:
                print(dirList[x])
                newDir.append(dirList[x])
    fo = open("playlist.m3u", "w")
    fo.write("#EXTM3U\n\n")
    for item in newDir:
#        print item
        fo.write("%s\n" % item)
    fo.close()
    time.sleep(2)

#open the playlist file and read its contents into a list
playlist = open('playlist.m3u')
trackArray = playlist.readlines()

# clean up the track list array of metadata and \n characters
# iterate over list in reverse order as deleting items from list as we go
for i in range(len(trackArray)-1,-1,-1):
    if trackArray[i].startswith('\n') or trackArray[i].startswith('#'):
        trackArray.pop(i)
    repl = {" ": "\ ", "\'": "\\'","&": "\&","(": "\(",")": "\)"} # define desired replacements here
    # use these three lines to do the replacement
    repl = dict((re.escape(k), v) for k, v in repl.iteritems())
    pattern = re.compile("|".join(repl.keys()))
    newArrayName = pattern.sub(lambda m: repl[re.escape(m.group(0))], trackArray[i])
    trackArray[i] = newArrayName
    temp = trackArray[i].strip()
    trackArray[i] = temp

# horrible kludge to strip out multiple backslashes
for i in range(len(trackArray)-1,-1,-1):
    repl = {"\\\\\\": "\\"} # define desired replacements here
    # use these three lines to do the replacement
    repl = dict((re.escape(k), v) for k, v in repl.iteritems())
    pattern = re.compile("|".join(repl.keys()))
    newArrayName = pattern.sub(lambda m: repl[re.escape(m.group(0))], trackArray[i])
    trackArray[i] = newArrayName

# read tracks into array to hold track info in format:
# filename - display name - duration as float - display duration - track status
print '\nScanning audio files to calculate durations:'
trackList = []
for a in range(len(trackArray)):
    rep = {"\ ": " ", "\\'": "\'", "\&": "&","\(": "(","\)": ")"} # define desired replacements here
    # use these three lines to do the replacement
    rep = dict((re.escape(k), v) for k, v in rep.iteritems())
    pattern = re.compile("|".join(rep.keys()))
    newName = pattern.sub(lambda m: rep[re.escape(m.group(0))], trackArray[a])
    print a+1,newName
    thisTrackLength = getTrackLength(a)
    trackList.append([trackArray[a],colform(newName,30),thisTrackLength,displayDuration(thisTrackLength),"status"])

# the main program loop
while True:
    clearStatus()
    showTracks()
    showUI()
    trackNo = raw_input('\nWhich track # would you like to play? q to quit ')
    if trackNo == 'q':
        break
    elif trackNo == "":
        print 'You must enter a track number or q to quit'
        time.sleep(2)
    elif trackNo.isalpha():
        print 'Must be a number'
        time.sleep(2)
    elif int(trackNo) <1 or int(trackNo) > len(trackArray):
        print 'Not a valid track number'
        time.sleep(2)
    else:
        eT = getEndTime(int(trackNo))
        trackList[int(trackNo)-1][4] = 'PLAYING ' + eT
        showTracks()
        showUI()
        playTrack(int(trackNo))
