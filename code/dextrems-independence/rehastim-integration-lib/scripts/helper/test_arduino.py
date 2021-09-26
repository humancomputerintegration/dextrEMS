import sys
import serial

arduino = serial.Serial(sys.argv[1], 9600)

while True:
    cmd = raw_input('send to arduino: ')
    arduino.write(cmd)
    print(arduino.readline())
