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

from pythonosc import osc_server
from pythonosc import dispatcher
from typing import List, Any

ems_device = False
FAKE_SERIAL = True 
serial_response_active = False

# OSC server
# ======================================================= #
ip = "0.0.0.0" # local
# ip = "192.168.0.17" # cross device
port = 5006
# ======================================================= #

# EMS parameters
# ======================================================= #
channel = 1
pulse_width = 300
intensity = 7
pulse_count = 80
delay = 0.0098 # 9,800 uS
# ======================================================= #


def ems_init():
        ems = SerialThingy.SerialThingy(FAKE_SERIAL)
        if len(sys.argv) > 1:
                ems.open_port(str(sys.argv[1]),serial_response_active) # pass the port via the command line, as an argument
        else:
                ems.open_port(serial_response_active)

        # while 1:
        #     print("current intensity (0-100mA, limited 32mA): ")
        #     print(intensity)
        #     user_input = raw_input('set intensity (enter to repeat current one, done to finish): ')
        #     user_channel = raw_input('set channel: ')

        #     if user_input != "":
        #         intensity = int(user_input)

        #     if user_channel != "":
        #         channel = int(user_channel)

        #     for i in range(pulse_count):
        #         ems.write(singlepulse.generate(channel, pulse_width, intensity))
        #         #ems.write(singlepulse.generate(2, pulse_width, intensity))
        #         #ems.write(singlepulse.generate(channel+1, pulse_width, intensity-5))
        #         #channel number (1-8), pulse width (200-450) in microseconds, intensity (0-100mA, limited 32mA)
        #         time.sleep(0.01)


def send_pulse(address, *args: List[Any]):
    global channel, pulse_width, intensity, pulse_count, delay
    channel = args[0]
    intensity = args[1]
    pulse_count = args[2]
    pulse_width = args[3]    
    delay = args[4]

    if ems_device:
        for i in range(pulse_count):
            #channel number (1-8), pulse width (200-450) in microseconds, intensity (0-100mA, limited 32mA)
            ems.write(singlepulse.generate(channel, pulse_width, intensity))
            time.sleep(delay)

    print("Sending pulse at CH " + str(channel) + " intensity " + str(intensity) + 
        " pulse count " + str(pulse_count) + " pulse width " + str(pulse_width) + 
        " delay " + str(delay) )

if __name__ == "__main__":
    # First connect to EMS hardware
    if ems_device: ems_init()

    # Defining OSC dispatecher
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/ems", send_pulse)

    # Start OSC server and run forever
    server = osc_server.ThreadingOSCUDPServer(
      (ip, port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
