# Car alarm
# The finch sounds an alarm, alternating high pitch sounds and
# flashing red abd blue lights, until its nose is turned up

from time import sleep
from finch import Finch

finch = Finch()
x = 0
while x > -0.5:
    x, y, z, tap, shake = finch.acceleration()

    finch.led("#FF0000") # set the led to red
    finch.buzzer(1.0, 250)
    sleep(1.05)
    finch.led("#0000FF") # set the led to blue
    finch.buzzer(1.0, 400)
    sleep(1.05)

finch.halt()
finch.close()
    
