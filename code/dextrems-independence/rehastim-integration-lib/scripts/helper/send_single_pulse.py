import sys
sys.path.append('../ems_interface/modules/')
sys.path.append('../ems_interface/tools-and-abstractions/')
import singlepulse
import SerialThingy
import time
import serial

FAKE_SERIAL = False 
serial_response_active = False

def main():
        ems = SerialThingy.SerialThingy(FAKE_SERIAL)
        if len(sys.argv) > 1:
                ems.open_port(str(sys.argv[1]),serial_response_active) # pass the port via the command line, as an argument
        else:
                ems.open_port(serial_response_active)

        while 1:
            #a = raw_input('Wait this')
            ems.write(singlepulse.generate(1,300,7)) #channel number (1-8), pulse width (200-450) in microseconds, intensity (0-100mA, limited 32mA)
            time.sleep(0.001)
if __name__ == "__main__":
    main()
