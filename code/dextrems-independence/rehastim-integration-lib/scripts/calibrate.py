# HOW TO RUN
# python calibrate.py /dev/cu.usbserial-HMYID101

# PARAMETERS
# start with following:
# ems.write(singlepulse.generate(1,300,7)) #channel number (1-8), pulse width (200-450) in microseconds, intensity (0-100mA, limited 32mA)

# ELECTRODES
# channel 1: TRICEP

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
        channel = 1
        pulse_width = 300
        intensity = 7
        pulse_count = 40

        ems = SerialThingy.SerialThingy(FAKE_SERIAL)
        if len(sys.argv) > 1:
                ems.open_port(str(sys.argv[1]),serial_response_active) # pass the port via the command line, as an argument
        else:
                ems.open_port(serial_response_active)

        while 1:
            print("current intensity (0-100mA, limited 32mA): ")
            print(intensity)
            user_input = input('set intensity (enter to repeat current one, done to finish): ')
            if user_input == "done":
                print("calibration done")
                print("intensity for you: ")
                print(intensity)
                break
            elif user_input != "":
                intensity = int(user_input)
            for i in range(pulse_count):
                ems.write(singlepulse.generate(channel, pulse_width, intensity))
                #ems.write(singlepulse.generate(channel+1, pulse_width, intensity-5))
                #channel number (1-8), pulse width (200-450) in microseconds, intensity (0-100mA, limited 32mA)
                time.sleep(0.01)
if __name__ == "__main__":
    main()
