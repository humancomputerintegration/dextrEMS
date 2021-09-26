import threading
import serial
import time

class SerialThread (threading.Thread):
    def __init__(self,b):
        threading.Thread.__init__(self)
        self.ser = b
        #print self.ser
    def run (self):
        #self.ser = serial.Serial('/dev/tty.usbmodem1421', 9600, timeout=10)
        while 1:
            value = self.ser.readline()
            v = value.decode("utf-8").rstrip('\r\n')
            print(v)
            
arduino = serial.Serial('/dev/tty.usbmodem1421', 9600, timeout=10)
#arduino.setDTR( level=False ) # set the reset signal
#time.sleep(2)             # wait two seconds, an Arduino needs some time to really reset
#arduino.setDTR( level=True )  # remove the reset signal, the Arduino will restart
time.sleep(2)             # wait two seconds, an Arduino needs some time to really reset

SerialThread(arduino).start()

#do stuff
arduino.write('d')
time.sleep(2)
arduino.write('c')
time.sleep(2)
arduino.write('u')
time.sleep(2)
arduino.write('y')
time.sleep(2)

