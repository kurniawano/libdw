# Race track driver, an example program for the Finch
# Watch the Finch navigate a square race track

from finch import Finch
from time import sleep

#Main function for the race track driver example program."""
    
#Initialize the finch
finch = Finch()
    
#Set both wheels to one-half forward throttle for 1.5s
finch.wheels(0.5,0.5)
finch.led(0, 255, 255)
sleep(1.5)

# Now set the left wheel at half throttle, right wheel off to turn
finch.wheels(0.5,0)
finch.led(0, 255, 0)
sleep(1.28)


finch.wheels(0.5,0.5)
finch.led(0, 255, 255)
sleep(1.5)


finch.wheels(0.5,0)
finch.led(0, 255, 0)
sleep(1.28)


finch.wheels(0.5,0.5)
finch.led(0, 255, 255)
sleep(1.5)


finch.wheels(0.5,0)
finch.led(0, 255, 0)
sleep(1.28)


finch.wheels(0.5,0.5)
finch.led(0, 255, 255)
sleep(1.5)


finch.wheels(0.5,0)
finch.led(0, 255, 0)
sleep(1.28)
   

#Close the connection with Finch
finch.close()
