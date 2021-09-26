# HOW TO RUN
# python send_arduino.py /dev/cu.usbserial-HMYID101 /dev/cu.usbserial-14110

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
        pulse_count = 80
        delay = 0.0098 # 9,800 uS

        ems = SerialThingy.SerialThingy(FAKE_SERIAL)
        if len(sys.argv) > 2:
                ems.open_port(str(sys.argv[1]),serial_response_active) # pass the port via the command line, as an argument
                arduino = serial.Serial(sys.argv[2])
        else:
                ems.open_port(serial_response_active)

        intensity = int(raw_input('set intensity (0-100mA, limited 32mA): '))
            
        while 1:
            # tune how long ems before braking
            #pulse_count = int(raw_input('set pulse count: '))

            # unlock fingers and disengage motors
            arduino.write('l0')
            time.sleep(.5
)            arduino.write('e0')

            # set params
            intensity = int(raw_input('Set intensity:'))
            if user_input != "":
                intensity = int(user_input)

            finger_unlock = int(raw_input('unlock finger --> 0-none, 1-index, 2-middle, 3-ring, 4-pinky'))
            joint_unlock = int(raw_input('unlock joint --> 0-none, 1-MCP, 2-PIP, 3-both: '))

            ard_unlock_cmd = "u" + finger_unlock + joint_unlock + "1"

            # enable motors
            arduino.write('e1')

            # lock fingers
            raw_input("Press to lock...")
            arduino.write('l1')
            arduino.write(ard_unlock_cmd)

            # send EMS signal
            raw_input("EMS ready...")

            for i in range(pulse_count):
                time.sleep(delay)
                ems.write(singlepulse.generate(channel, pulse_width, intensity))
                #ems.write(singlepulse.generate(2, pulse_width, intensity))
                #ems.write(singlepulse.generate(channel+1, pulse_width, intensity-5))
                #channel number (1-8), pulse width (200-450) in microseconds, intensity (0-100mA, limited 32mA)
                
            # prompt to continue
            raw_input("Done... Releasing")

if __name__ == "__main__":
    main()
