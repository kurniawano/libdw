# This module implements connection of a Finch robot via USB. It is used by
# finch.py to send and receive commands from the Finch.
# The Finch is a robot for computer science education. Its design is the result
# of a four year study at Carnegie Mellon's CREATE lab.
# http://www.finchrobot.com

import atexit 
import os
import ctypes
import threading
import time
import platform
import sys

VENDOR_ID = 0x2354
DEVICE_ID = 0x1111

HIDAPI_LIBRARY_PATH = os.environ.get('HIDAPI_LIB_PATH', './')
PING_FREQUENCY_SECONDS = 2.0 # seconds

# Detect which operating system is present and load corresponding library

system = platform.system()

if system == 'Windows':
    if sys.maxsize > 2**32:
        hid_api = ctypes.CDLL(os.path.join(HIDAPI_LIBRARY_PATH, "hidapi64.dll"))
    else:
        hid_api = ctypes.CDLL(os.path.join(HIDAPI_LIBRARY_PATH, "hidapi32.dll"))
        
elif system == 'Linux':
    if sys.maxsize > 2**32:
        hid_api = ctypes.CDLL(os.path.join(HIDAPI_LIBRARY_PATH, "libhidapi64.so"))
    else:
        hid_api = ctypes.CDLL(os.path.join(HIDAPI_LIBRARY_PATH, "libhidapi32.so"
                                           ))
elif system == 'Darwin':
    hid_api = ctypes.CDLL(os.path.join(HIDAPI_LIBRARY_PATH, "libhidapi.dylib"))
else:
    hid_api = ctypes.CDLL(os.path.join(HIDAPI_LIBRARY_PATH, "libhidapipi.so"))
    
def _inherit_docstring(cls):
    def doc_setter(method):
        parent = getattr(cls, method.__name__)
        method.__doc__ = parent.__doc__
        return method
    return doc_setter

class FinchConnection:
    """ USB connection to the Finch robot. Uses the HID API
        to read and write from the robot. """

    c_finch_handle = ctypes.c_void_p(None)
    c_io_buffer = ctypes.c_char_p(None)
    cmd_id = 0

    def is_open(self):
        """Returns True if connected to the robot."""
        return bool(self.c_finch_handle)

    def open(self):
        """ Connect to the robot.

        This method looks for a USB port the Finch is connceted to. """
        
        _before_new_finch_connection(self)
        if self.is_open():
            self.close()
        try:
            hid_api.hid_open.restype = ctypes.c_void_p
            self.c_finch_handle = hid_api.hid_open(
                ctypes.c_ushort(VENDOR_ID),
                ctypes.c_ushort(DEVICE_ID),
                ctypes.c_void_p(None))
            self.c_io_buffer = ctypes.create_string_buffer(9)
            _new_finch_connected(self)
            self.cmd_id = self.read_cmd_id()
        except:
            raise Exception("Failed to connect to the Finch robot.")

    def close(self):
        """ Disconnect the robot. """
        
        if self.c_finch_handle:
            self.send(b'R', [0]) # exit to idle (rest) mode
            hid_api.hid_close.argtypes = [ctypes.c_void_p]
            hid_api.hid_close(self.c_finch_handle)
        self.c_finch_handle = ctypes.c_void_p(None)
        self.c_io_buffer = ctypes.c_char_p(None)
        
        global _open_finches
        if self in _open_finches:
            _open_finches.remove(self)

    def read_cmd_id(self):
        """ Read the robot's internal command counter. """
        
        #self.send('z', receive = True)
        self.send(b'z')
        data = self.receive()
        return data[0]

    def send(self, command, payload=()):
        """Send a command to the robot (internal).

        command: The command ASCII character
        payload: a list of up to 6 bytes of additional command info
        """
        
        if not self.is_open():
            raise Exception("Connection to Finch was closed.")
        
        # Format the buffer to contain the contents of the payload.
        for i in range(7):
            self.c_io_buffer[i] = b'\x00'
        self.c_io_buffer[1] = command[0]

        python_version = sys.version_info[0]

        if payload:
            for i in range(len(payload)):
                if python_version >= 3:
                    self.c_io_buffer[i+2] = payload[i]
                else:
                    self.c_io_buffer[i+2] = bytes(chr(payload[i]))
        # Make sure command id is incremented if this is a receive case
        else:
            self.cmd_id = (self.cmd_id + 1) % 256

        # Make sure the command id is incremented so that two calls to obstacle() don't cause the system to hang
        #self.cmd_id = (self.cmd_id + 1) % 256
        #if self.cmd_id == 0:
        #    self.cmd_id = 1
                
        if python_version >= 3:
            self.c_io_buffer[8] = self.cmd_id
        else:
            self.c_io_buffer[8] = bytes(chr(self.cmd_id))
        
        # Write to the Finch bufffer
        res = 0
        while not res:
            hid_api.hid_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
            res = hid_api.hid_write(self.c_finch_handle,
                                    self.c_io_buffer,
                                    ctypes.c_size_t(9))
       
    def receive(self):
        """ Read the data from the Finch buffer. """
        
        res = 9
        while res > 0:
            hid_api.hid_read.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
            res = hid_api.hid_read(self.c_finch_handle,
                                    self.c_io_buffer,
                                    ctypes.c_size_t(9))
            if self.cmd_id == ord(self.c_io_buffer[8]):
                break
        return [ord(self.c_io_buffer[i]) for i in range(9)]
    
class ThreadedFinchConnection(FinchConnection):
    """Threaded implementation of Finch Connection"""
    
    lock = None
    thread = None
    main_thread = None
    last_cmd_sent = None

    @_inherit_docstring(FinchConnection)
    def open(self):
        FinchConnection.open(self)
        if not self.is_open():
            return
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.__class__._pinger, args=(self, ))
        self.main_thread = threading.current_thread()
        self.thread.start()

    @_inherit_docstring(FinchConnection)
    def send(self, command, payload=(), receive=False):
        try:
            if self.lock is not None:
                self.lock.acquire()
            #FinchConnection.send(self, command, payload=payload, receive=receive)
            FinchConnection.send(self, command, payload=payload)
        finally:
            if self.lock is not None:
                self.lock.release()

    @_inherit_docstring(FinchConnection)
    def receive(self):
        try:
            if self.lock is not None:
                self.lock.acquire()
            data = FinchConnection.receive(self)
        finally:
            if self.lock is not None:
                self.lock.release()
        return data
    
    def _pinger(self):
        """ Sends keep-alive commands every few secconds of inactivity. """

        while True:
            if not self.lock:
                break
            if not self.c_finch_handle:
                break
            if not self.main_thread.isAlive():
                break
            try:
                self.lock.acquire()
                now = time.time()
                if self.last_cmd_sent:
                    delta = now - self.last_cmd_sent
                else:
                    delta = PING_FREQUENCY_SECONDS
                if delta >= PING_FREQUENCY_SECONDS:
                    FinchConnection.send(self, b'z')
                    FinchConnection.receive(self)
                    self.last_cmd_sent = now
            finally:
                self.lock.release()
            time.sleep(0.1)

    @_inherit_docstring(FinchConnection)
    def close(self):
        FinchConnection.close(self)
        self.thread.join()
        self.lock = None
        self.thread = None

# Functions that handle the list of open finches

_open_finches = []

def _before_new_finch_connection(finch):
    global _open_finches
    # close other connections
    for robot in _open_finches:
        if robot.is_open():
            robot.close()


def _new_finch_connected(finch):
    global _open_finches
    if finch not in _open_finches:
        _open_finches.append(finch)


def _close_all_finches():
    global _open_finches
    if not _open_finches:
        return
    for finch in _open_finches:
        if finch.is_open():
            finch.close()

atexit.register(_close_all_finches)



    
