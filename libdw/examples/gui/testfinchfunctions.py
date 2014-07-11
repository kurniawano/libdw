# testfinchfunctions, an example program for the Finch
# Tests all parts of the Finch: prints all sensor values, changes the led
# moves the wheels and beeps the buzzer.

from time import sleep
from finch import Finch

finch = Finch()
print('Temperature %5.2f' % finch.temperature())
print()

finch.wheels(1.0, -1.0)
sleep(0.5)
finch.wheels(0.0, 0.0)

for count in range(5):

    finch.led(0, 50*count, 0)
    x, y, z, tap, shake = finch.acceleration()
    print ('Acceleration %5.3f, %5.3f %5.3f %s %s' %
              (x, y, z, tap, shake))
    left_light, right_light = finch.light()
    print ('Lights %5.3f, %5.3f' % (left_light, right_light))
    left_obstacle, right_obstacle = finch.obstacle()
    print('Obstacles %s, %s' % (left_obstacle, right_obstacle))
    print()
    finch.buzzer(0.8, 100*count)
    sleep(1)
    
finch.led('#FF0000')
finch.buzzer(5, 440)
sleep(5)    

finch.halt()
finch.close()
