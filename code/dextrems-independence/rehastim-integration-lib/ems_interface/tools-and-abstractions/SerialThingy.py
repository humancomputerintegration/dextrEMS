import serial
import SerialThread

class SerialThingy(object):
        def __init__(self, fake, writeFakeToConsole = False):
                self.ser = None
                self.fake = fake #i'm wondering ig this should have a default, which is False
                self.writeFakeToConsole = writeFakeToConsole #defaulted to false

        def sendFakeWritesToConsoleOutput(value):
                self.writeFakeToConsole = value

        def open_port(self, port, listening_serial_thread):
                if not self.fake:
                        self.ser = serial.Serial(port, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, 
                                #rtscts=True,
                                write_timeout=0,
                                #xonxoff=True,
                                timeout=0)
                if listening_serial_thread:
                    SerialThread.SerialThread(self.ser).start()
        def write(self, msg):
                if not self.fake:
                        self.ser.write(msg)
                elif self.writeFakeToConsole:
                        print(msg) #writes the EMS serial message to the console / std out
