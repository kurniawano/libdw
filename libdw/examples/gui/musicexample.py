"""
Plays a list of songs. Input a number to choose.
1. Michigan fight song
2. Intro to Sweet Child of Mine
3. Mario Theme Song

Uses notes.py, an add-on library that simplifies buzzer song creation.
Thanks to Justas Sadvecius for the library!

The Finch is a robot for computer science education. Its design is the result
of a four year study at Carnegie Mellon's CREATE lab.

http://www.finchrobot.com
"""

from finch import Finch
from time import sleep
import notes

#Main function for the music player example program"""

#Initialize the finch    
finch = Finch()

songList = ['E5  C D E C D E F  D E F D E F G  A  GE F C D E G E D C ',
                'D D5 A4 G G5 A4 F5# A4 D D5 A4 G G5 A4 F5# A4 '
                'E D5 A4 G G5 A4 F5# A4 E D5 A4 G G5 A4 F5# A4 '
                'G D5 A4 G G5 A4 F5# A4 G D5 A4 G G5 A4 F5# A4 '
                'D D5 A4 G G5 A4 F5# A4 D D5 A4 G G5 A4 F5# A4 ',
                'E5 E  E   C E  G    G4   C5  G4   E   A BBb A  G  '
                'E5  G  A F G  E  C D B4  C5  G4   E   A BBb A  G  '
                'E5  G  A F G  E  C D B4 -  G5 Gb F D#  E G4# A C5 A4 C5 D '
                'G5 Gb F D#  E C6 C6 C6   '
                'G5 Gb F D#  E G4# A C5 A4 C5 D  Eb  D  C    '
                ' G5 Gb F D#  E G4# A C5 A4 C5 D G5 Gb F D#  E C6 C C  ']
timeList = [0.18,0.1,0.1]

song = 1
while song > 0 and song < 4:
    #get which song
    song = int(input("Enter 1 for the Michigan fight song, 2 for Sweet Child of Mine,"
                    "3 for the Mario theme song; any other number to exit."))

    if song >=1 and song <= 3:
        notes.sing(finch, songList[song -1],timeList[song-1])
    else:
        print('Exiting...')


