# Lap Swimmer, an example program for the Finch
# Tell the Finch how many laps to do, set it down on the ground
# Finch goes forward until it sees an obstacle
# Then goes back the same distance. It'll then repeat this lap as many times
# as the user requested

from finch import Finch
from time import sleep, time

# Main function for the lap swimmer example program
    
finch = Finch() # Initialize the finch

finch.led(255, 255, 0)
laps = 0

# Get the number of laps Finch will swim:
    
while laps <= 0:
    laps = int(input('Enter number of laps: '))

    if laps < 0:
        print('Cannot swim a negative number of laps!')
    elif laps == 0:
        print('Zero laps? I want to swim!')

# Move forward until an obstacle is present and measure the time:

start = time()
finch.wheels(0.5, 0.5)
sleep(0.1)
while True:
    left_obstacle, right_obstacle = finch.obstacle()
    if left_obstacle or right_obstacle:
        half_lap_time = time() - start
        finch.wheels(0, 0)
        break

print('Obstacle found, backing up')

# Move backwards for the same amount of time spent moving forward

finch.wheels(-0.5, -0.5)
sleep(half_lap_time)
laps -= 1

# Now lapswim!

while laps > 0:
    finch.wheels(0.5, 0.5)
    sleep(half_lap_time)
    finch.wheels(0, 0)
    sleep(0.1)
    finch.wheels(-0.5, -0.5)
    sleep(half_lap_time)
    laps -= 1
    
finch.close()
