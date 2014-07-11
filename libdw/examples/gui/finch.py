# Functions to control Finch robot.

# The Finch is a robot for computer science education. Its design is the result
# of a four year study at Carnegie Mellon's CREATE lab.

# http://www.finchrobot.com
# See included examples and documentation for how to use the API

import time
import finchconnection

class Finch():

    def __init__(self):
        self.connection = finchconnection.ThreadedFinchConnection()
        self.connection.open()
        
    def led(self, *args):
        """Control three LEDs (orbs).
       
          - hex triplet string: led('#00FF8B') or 
            0-255 RGB values: led(0, 255, 139)
        """
        if len(args) == 3:
            r, g, b = [int(x) % 256 for x in args]
        elif (len(args) == 1 and isinstance(args[0], str)):
            color = args[0].strip()
            if len(color) == 7 and color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
        else:
            return
        self.connection.send(b'O', [r, g, b])

    def buzzer(self, duration, frequency):
        """ Outputs sound. Does not wait until a note is done beeping.

        duration - duration to beep, in seconds (s).
        frequency - integer frequency, in hertz (HZ).
        """
        millisec = int(duration * 1000)
        self.connection.send(b'B',
                [(millisec & 0xff00) >> 8, millisec & 0x00ff,
                 (frequency & 0xff00) >> 8, frequency & 0x00ff])

    def buzzer_with_delay(self, duration, frequency):
        """ Outputs sound. Waits until a note is done beeping.

        duration - duration to beep, in seconds (s).
        frequency - integer frequency, in hertz (HZ).
        """
        millisec = int(duration * 1000)
        self.connection.send(b'B',
                [(millisec & 0xff00) >> 8, millisec & 0x00ff,
                 (frequency & 0xff00) >> 8, frequency & 0x00ff])
        time.sleep(duration*1.05)

    def light(self):
        """ Get light sensor readings. The values ranges from 0.0 to 1.0.

            returns - a tuple(left, right) of two real values
         """
        self.connection.send(b'L')
        data = self.connection.receive()
        if data is not None:
            left = data[0] / 255.0
            right = data[1] / 255.0
            return left, right

    def obstacle(self):
        """Get obstacle sensor readings.

        returns - a tuple(left,right) of two boolean values
        """
        self.connection.send(b'I')
        data = self.connection.receive()
        if data is not None:
            left = data[0] != 0
            right = data[1] != 0
            return left, right 

    def temperature(self):
        """ Returns temperature in degrees Celcius. """
        
        self.connection.send(b'T')
        data = self.connection.receive()
        if data is not None:
            return (data[0] - 127) / 2.4 + 25;

    def convert_raw_accel(self, a):
        """Converts the raw acceleration obtained from the hardware into G's"""
        
        if a > 31:
            a -= 64
        return a * 1.6 / 32.0

    def acceleration(self):
        """ Returns the (x, y, z, tap, shake).  x, y, and z, are
            the acceleration readings in units of G's, and range
            from -1.5 to 1.5.
            When the finch is horisontal, z is close to 1, x, y close to 0.
            When the finch stands on its tail, y, z are close to 0,
            x is close to -1.
            When the finch is held with its left wing down, x, z are close to 0,
            y is close to 1.
            tap, shake are boolean values -- true if the correspondig event has
            happened.
        """
        
        self.connection.send(b'A')
        data = self.connection.receive()
        if data is not None:
            x = self.convert_raw_accel(data[1])
            y = self.convert_raw_accel(data[2])
            z = self.convert_raw_accel(data[3])
            tap = (data[4] & 0x20) != 0
            shake = (data[4] & 0x80) != 0
            return (x, y, z, tap, shake)

    def wheels(self, left, right):
        """ Controls the left and right wheels.

        Values must range from -1.0 (full throttle reverse) to
        1.0 (full throttle forward).
        use left = right = 0.0 to stop.
        """
        
        dir_left = int(left < 0)
        dir_right = int(right < 0)
        left = min(abs(int(left * 255)), 255)
        right = min(abs(int(right * 255)), 255)
        self.connection.send(b'M', [dir_left, left, dir_right, right])

    def halt(self):
        """ Set all motors and LEDs to off. """
        self.connection.send(b'X', [0])

    def close(self):
        self.connection.close()
