''' 
DEXTREMS ACCURACY STUDY - measuring ring finger's MCP joint using Optitrack

    hardware:
    - Optitrack
    - arduino with dextrEMS exo for braking
    - rehastim for EMS
by Romain Nith and Yujie Tao
'''

import os
import serial
import time
import math
import random
import numpy as np
import csv
from datetime import datetime
import sys
import atexit

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from pid_controller import PIDController
from ems_controller import EMSController
from ReadLine import ReadLine

from NatNetClient import NatNetClient

# Serial ports - change the serial port to yours
ard_angle_port  = "COM7"
ard_exo_port    = "COM3"
ems_port        = "COM4"

# Flags
opti_connected      = True   # if no optitrack, use random values
ard_exo_connected   = True   
ems_connected       = True

random_target       = False

debug               = False
debug_opti          = False
debug_filter        = False

show_plot           = False  # plot doesnt work in real time

# EMS calibrations
ems_intensity_flex = 7#8
ems_intensity_ext  = 8#9

# Targets
target_arr = [0, 8, 17, 23, 33, 45, 60, 73] # In degrees, contrained by ratchet resolution
target_index = 5 # Choose target angle
# brake_offset = 0

# PID coefficients - PID condition
PID_P        = 10 
PID_I        = 0.01 
PID_D        = 1
PID_maxOut   = 450 # clamp max pulse width
PID_minOut   = 100 # clamp min pulse width
PID_frequency= 1000  # in Hz, how fast main loop refreshes
target       = target_arr[target_index]   # in degrees
error_margin = 2    # if position is within error margin, consider target reached

# PID with exo: 2, 0.25, 1.25

# PID coefficients - EXO condition
# PID_EXO_P        = 4 
# PID_EXO_I        = 0.01 
# PID_EXO_D        = 1
# PID_EXO_maxOut   = 450 # clamp max pulse width
# PID_EXO_minOut   = 100#100 # clamp min pulse width
# PID_EXO_frequency= 30  # in Hz, how fast main loop refreshes
# error_margin_EXO = 0   # if position is within error margin, consider target reached

#                         P    I   D  minOut  maxOut  freq br_off err_marg
PID_EXO_FLEX_profiles =[[ 4, 0.01, 1,  100,    450,    50,    0,    0], # target = 0 not considered for flex
                        [ 1, 0.01, 1,  100,    450,    30,    0,    1], # target = 8
                        [ 4, 0.01, 1,  150,    450,    50,    0,    0], # target = 17
                        [ 6, 0.01, 1,  150,    450,    50,    0,    0], # target = 23
                        [ 8, 0.01, 1,  150,    450,    30,    0,    0], # target = 33
                        [ 10, 0.01, 1,  200,    450,    30,    0,    0], # target = 45
                        [ 3, 0.01, 1,  100,    450,    30,    0,    0], # target = 60
                        [ 1, 0.01, 1,  100,    450,    30,    0,    0]] # target = 73 not considered for flex

#                         P    I   D  minOut  maxOut  freq  br_off err_marg
PID_EXO_EXT_profiles = [[ 18, 0.01, 1,  200,    450,    50,    0,    5], # target = 0 
                        [ 18, 0.01, 1,  270,    450,    50,    0,    1], # target = 8
                        [ 20, 0.01, 1,  270,    450,    50,    0,    1], # target = 17
                        [ 16, 0.01, 1,  200,    450,    50,    0,    1], # target = 23
                        [ 16, 0.01, 1,  200,    450,    50,    0,    0], # target = 33
                        [ 2, 0.01, 1,  200,    450,    30,    0,    0], # target = 45
                        [ 4, 0.01, 1,  100,    450,    50,    0,    0], # target = 60 not considered for flex
                        [ 4, 0.01, 1,  100,    450,    50,    2,    0]] # target = 73 not considered for flex

# Angle variables
angle               = 0     # in degrees
angular_velocity    = 0     # in degrees/seconds
moving_avg_size     = 10    # filtering over n values
angle_array         = [0] * moving_avg_size
moving_avg_counter  = len(angle_array)
finger_heading_off  = 0
hand_heading_off    = 0

# Create figure for plotting
fig = plt.figure()
ax  = fig.add_subplot(1, 1, 1)
xs  = []
ys  = []

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

log_path = ROOT_DIR + "/datalogging/"

log_filename_PID = datetime.now().strftime('PID-USER1-' + str(target_arr[target_index]) + '-%Y-%m-%d-%H-%M-%S.csv')
log_filename_EXO = datetime.now().strftime('EXO-USER1-' + str(target_arr[target_index]) + '-%Y-%m-%d-%H-%M-%S.csv')

def main():
    global ard_angle    
    global angle
    global prev_angle
    global prev_angle_time
    prev_angle = 0
    prev_angle_time = 0

    global ard_exo
    global brake_state
    global target_index

    study_mode = 0

    # init optitrack
    if (opti_connected):
        streamingClient = NatNetClient()

        # Configure the streaming client to call our rigid body handler on the emulator to send data out.
        streamingClient.newFrameListener = None #receiveNewFrame
        streamingClient.rigidBodyListener = receiveRigidBodyFrame

        # Start up the streaming client now that the callbacks are set up.
        # This will run perpetually, and operate on a separate thread.
        streamingClient.run()

    # init exo arduino
    if (ard_exo_connected):
        try:
            ard_exo = serial.Serial(ard_exo_port, 115200, timeout=10)
        except:
            ard_exo = 0
            print("Please check port for exo arduino")

    # init EMS device - using dummy values for init
    if (ems_connected):
        ems = EMSController(
            ems_port,
            pulse_count = 200,
            channel = 1,
            pulse_width = 6,
            intensity = 0,
        )

    if (show_plot):
        # Set up plot to call animate() function periodically
        ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1)
        plt.show(block=False)

    if (random_target):
        target_index = random.randint(0, 6)

    # -------------------------------------- STUDY STARTS HERE ------------------------------------ #

    while True: 
        if study_mode == 0:
            print ("Select a condition:")
            study_mode = int(input("1 - EMS PID, 2 - EMS EXO FLEX, 3 - EMS EXO EXT, 4 - read only angle"))

        # EMS PID condition
        elif study_mode == 1:
            # setup logging
            file = open(log_path + "/" + str(target_arr[target_index]) + "/" + log_filename_PID, 'a')
            file.write("time" + "," + "angle" + "," + "target" + "," +"PID_output" + "," + "channel" + "," + "pulse_width" + "," +
                "PID_P = " + str(PID_P) + "," + "PID_I = " + str(PID_I) + "," + "PID_D = " + str(PID_D) + "," + 
                "target = " + str(target) + "\n")

            # Time variables
            first_run = True

            angle = 0

            exo_unlock()

            # init PID controller        
            PID = PIDController(P=PID_P, I=PID_I, D=PID_D, freq=1, min=PID_minOut, max=PID_maxOut)
            PID.target = target_arr[target_index]

            print(PID.target)

            input("Curl fingers.")

            exo_lock()

            input("When at 0, press any key to zero angle.")

            # input("Lay user's hand flat to zero the angle...press any key to continue")

            # zero the angles from the 2 rigid bodies
            setOffset()

            exo_unlock()
            
            input("Ready?")

            time.sleep(random.uniform(1, 4))

            # Reset timer for first run
            time_initial = time.time()
            time_log = 0

            while True:
                # read filtered delta angle
                angle = moving_avg(read_angle())

                time_now = time.time() - time_initial # in seconds

                # update every PID_frequency Hz
                if (time_now - time_log > 1 / PID_frequency):
                    print(time_now - time_log)
                    time_log = time.time() - time_initial

                    output = PID.step(angle)

                    # need to extend more...
                    # if angle < target - error_margin:
                    # if output < 0 - error_margin:
                    if angle < target_arr[target_index] - error_margin:
                        channel = 1
                        # pulse_width_tmp = set_pulse_width(output, channel)
                        pulse_width_tmp = int(abs(output))
                     
                        if ems_connected:                        
                            ems.set_param(
                                pulse_count = 1,
                                channel     = channel,
                                pulse_width = pulse_width_tmp,
                                intensity   = ems_intensity_flex,
                            )
                            ems.send_signal()

                    # need to flex more...
                    # elif angle > target + error_margin:
                    # elif output > 0:
                    elif angle > target_arr[target_index] + error_margin:
                    
                        channel = 2
                        # pulse_width_tmp = set_pulse_width(output, channel)
                        pulse_width_tmp = int(abs(output))

                        if ems_connected:
                            ems.set_param(
                                pulse_count = 1,
                                channel     = channel,
                                pulse_width = pulse_width_tmp,
                                intensity   = ems_intensity_ext,
                            )
                            ems.send_signal()

                    # if position is within error margin, consider target reached
                    else:
                        channel = 0
                        pulse_width_tmp = 0
                        
                        print("target reached!")

                    # if angle > target_arr[target_index - brake_offset]:
                    #     exo_lock()
                        

                    # # Reset timer for first run
                    # if first_run:
                    #     time_initial = time.time()
                    #     first_run = False

                    # Log data to csv
                    file = open(log_path + "/" + str(target_arr[target_index]) + "/" + log_filename_PID, 'a')

                    file.write(str(time_log) + "," + str(angle) + "," + str(PID.target) + "," + str(output) + "," + str(channel) + "," + str(pulse_width_tmp) + "\n")
                    
                    print("angle: " + str("{0:.2f}".format(angle)) + " PID output: " + str("{0:.2f}".format(output)) +  " pulse width: " + str(pulse_width_tmp) + " channel: " + str(channel))
                    
                    if (show_plot):
                        # need pause or else plot crashes
                        plt.pause(0.001)

        # exo condition
        elif study_mode == 2:
            # Unlock joint ring mcp
            exo_unlock()

            # EMS config - flexor
            if ems_connected:
                ems.set_param(
                    pulse_count = 1,
                    channel     = 1,
                    pulse_width = 300,
                    intensity   = ems_intensity_flex,
                )

            # Setting logging
            file = open(log_path + "/" + str(target_arr[target_index]) + "/" + log_filename_EXO, 'a')
            file.write("time" + "," + "angle" + "," + "target" + "," + "output" + "," + "pulse_width" + "," + "brake_state" + "\n")

            # init PID controller
            PID_EXO = PIDController(P=PID_EXO_FLEX_profiles[target_index][0], I=PID_EXO_FLEX_profiles[target_index][1], D=PID_EXO_FLEX_profiles[target_index][2],
                                    freq=1, min=PID_EXO_FLEX_profiles[target_index][3], max=PID_EXO_FLEX_profiles[target_index][4])

            #PID_EXO = PIDController(P=PID_EXO_P, I=PID_EXO_I, D=PID_EXO_D, freq=1, min=PID_EXO_minOut, max=PID_EXO_maxOut)
            PID_EXO.target = target_arr[target_index]

            # unpacking PID profile for clarity
            PID_EXO_frequency = PID_EXO_FLEX_profiles[target_index][5]
            brake_offset = PID_EXO_FLEX_profiles[target_index][6]
            error_margin_EXO = PID_EXO_FLEX_profiles[target_index][7]
            brake_target = target_arr[target_index - brake_offset] - error_margin_EXO

            print(PID_EXO.target)
            print(brake_target)

            time.sleep(1)

            input("Curl fingers.")

            exo_lock()

            input("When at 0, press any key to zero angle.")

            # input("Lay user's hand flat to zero the angle...press any key to continue")

            # zero the angles from the 2 rigid bodies
            setOffset()

            exo_unlock()
            
            input("Ready?")

            time.sleep(random.uniform(1, 4))

            post_lock_timer = 5000
            post_lock_ems = 0

            pulse_width_tmp = 0

            # Reset timer for first run
            time_initial = time.time()
            time_lastEMS = 0

            # Continues to record after target reached for "post_lock_timer" increments
            while post_lock_timer != 0:
                # read filtered delta angle
                angle = moving_avg(read_angle())
                output = PID_EXO.step(angle)

                time_now = time.time() - time_initial # in seconds

                # angular_velocity = get_angular_velocity(angle, time_now)
                # print(angular_velocity)

                if angle < brake_target  and brake_state == 0: # or angle > target + error_margin:
                    # update every PID_frequency Hz
                    if (time_now - time_lastEMS > 1 / PID_EXO_frequency):
                        # print(time_now - time_lastEMS)
                        time_lastEMS = time_now
                        # Send EMS
                        pulse_width_tmp = int(abs(output))
                        if ems_connected:
                            ems.set_param(
                                    pulse_count = 1,
                                    channel     = 1,
                                    pulse_width = pulse_width_tmp,
                                    intensity   = ems_intensity_flex,
                                )
                            ems.send_signal()
                        # else:
                        #     print("Sending EMS...")

                else: # Target reached 
                    if post_lock_ems != 0:
                        # update every PID_frequency Hz
                        if (time_now - time_lastEMS > 1 / PID_EXO_frequency):                
                            time_lastEMS = time_now                    
                            post_lock_ems = post_lock_ems - 1
                            # Send EMS
                            pulse_width_tmp = int(abs(output))
                            if ems_connected:
                                ems.set_param(
                                    pulse_count = 1,
                                    channel     = 1,
                                    pulse_width = pulse_width_tmp,
                                    intensity   = ems_intensity_flex,
                                )
                                # ems.send_signal()
                            # else:
                            #     print("Sending EMS...")

                    if brake_state == 0: # lock joint once
                        exo_lock()

                    # Start timer 
                    post_lock_timer = post_lock_timer - 1

                # Log data to csv
                file = open(log_path + "/" + str(target_arr[target_index]) + "/" + log_filename_EXO, 'a')

                time_log = time.time() - time_initial
                file.write(str(time_log) + "," + str(angle) + "," + str(target_arr[target_index]) + "," + str(output) + "," + str(pulse_width_tmp) + "," + str(brake_state * brake_target) + "\n")

                print("angle: " + str("{0:.2f}".format(angle)) + " PID output: " + str("{0:.2f}".format(output)) +  " pulse width: " + str(pulse_width_tmp) + " brake_state: " + str(brake_state) + " timer: " + str(post_lock_timer))

                if (show_plot):
                #     # need pause or else plot crashes
                    plt.pause(0.01)
                    plt.draw()

            # Stop study
            study_mode = 0
            print("DONE!")

        # exo condition
        elif study_mode == 3:
            # Unlock joint ring mcp
            exo_unlock()

            # EMS config - flexor
            if ems_connected:
                ems.set_param(
                    pulse_count = 1,
                    channel     = 2,
                    pulse_width = 300,
                    intensity   = ems_intensity_flex,
                )

            # Setting logging
            file = open(log_path + "/" + str(target_arr[target_index]) + "/" + log_filename_EXO, 'a')
            file.write("time" + "," + "angle" + "," + "target" + "," + "output" + "," + "pulse_width" + "," + "brake_state" + "\n")

            # init PID controller
            PID_EXO = PIDController(P=PID_EXO_EXT_profiles[target_index][0], I=PID_EXO_EXT_profiles[target_index][1], D=PID_EXO_EXT_profiles[target_index][2],
                                    freq=1, min=PID_EXO_EXT_profiles[target_index][3], max=PID_EXO_EXT_profiles[target_index][4])

            #PID_EXO = PIDController(P=PID_EXO_P, I=PID_EXO_I, D=PID_EXO_D, freq=1, min=PID_EXO_minOut, max=PID_EXO_maxOut)
            PID_EXO.target = target_arr[target_index]

            # unpacking PID profile for clarity
            PID_EXO_frequency = PID_EXO_EXT_profiles[target_index][5]
            brake_offset = PID_EXO_EXT_profiles[target_index][6]
            error_margin_EXO = PID_EXO_EXT_profiles[target_index][7]
            brake_target = target_arr[target_index-brake_offset] - error_margin_EXO

            print(PID_EXO.target)

            print(brake_target)

            time.sleep(1)

            input("Curl fingers.")

            exo_lock()

            input("When at 0, press any key to zero angle.")

            # input("Lay user's hand flat to zero the angle...press any key to continue")

            # zero the angles from the 2 rigid bodies
            setOffset()

            exo_unlock()
            
            input("Ready?")

            time.sleep(random.uniform(1, 4))

            post_lock_timer = 5000
            post_lock_ems = 0

            pulse_width_tmp = 0

            # Reset timer for first run
            time_initial = time.time()
            time_lastEMS = 0

            # Continues to record after target reached for "post_lock_timer" increments
            while post_lock_timer != 0:
                # read filtered delta angle
                angle = moving_avg(read_angle())
                output = PID_EXO.step(angle)

                time_now = time.time() - time_initial # in seconds

                # angular_velocity = get_angular_velocity(angle, time_now)
                # print(angular_velocity)

                if angle > brake_target  and brake_state == 0: # or angle > target + error_margin:
                    # update every PID_frequency Hz
                    if (time_now - time_lastEMS > 1 / PID_EXO_frequency):
                        # print(time_now - time_lastEMS)
                        time_lastEMS = time_now
                        # Send EMS
                        pulse_width_tmp = int(abs(output))
                        if ems_connected:
                            ems.set_param(
                                    pulse_count = 1,
                                    channel     = 2,
                                    pulse_width = pulse_width_tmp,
                                    intensity   = ems_intensity_flex,
                                )
                            ems.send_signal()
                        # else:
                        #     print("Sending EMS...")

                else: # Target reached 
                    if post_lock_ems != 0:
                        # update every PID_frequency Hz
                        if (time_now - time_lastEMS > 1 / PID_EXO_frequency):                
                            time_lastEMS = time_now                    
                            post_lock_ems = post_lock_ems - 1
                            # Send EMS
                            pulse_width_tmp = int(abs(output))
                            if ems_connected:
                                ems.set_param(
                                    pulse_count = 1,
                                    channel     = 2,
                                    pulse_width = pulse_width_tmp,
                                    intensity   = ems_intensity_flex,
                                )
                                # ems.send_signal()
                            # else:
                            #     print("Sending EMS...")

                    if brake_state == 0: # lock joint once
                        exo_lock()

                    # Start timer 
                    post_lock_timer = post_lock_timer - 1

                # Log data to csv
                file = open(log_path + "/" + str(target_arr[target_index]) + "/" + log_filename_EXO, 'a')

                time_log = time.time() - time_initial
                file.write(str(time_log) + "," + str(angle) + "," + str(target_arr[target_index]) + "," + str(output) + "," + str(pulse_width_tmp) + "," + str(brake_state * brake_target) + "\n")

                print("angle: " + str("{0:.2f}".format(angle)) + " PID output: " + str("{0:.2f}".format(output)) +  " pulse width: " + str(pulse_width_tmp) + " brake_state: " + str(brake_state) + " timer: " + str(post_lock_timer))

                if (show_plot):
                #     # need pause or else plot crashes
                    plt.pause(0.01)
                    plt.draw()

            # Stop study
            study_mode = 0
            print("DONE!")

                # read sensor continously
        elif study_mode == 4:
            time_output = 0
            input("Lay user's hand flat to zero the angle...press any key to continue")

            # zero the angles from the 2 rigid bodies
            setOffset()
            while True:
                time_now = time.time() # in seconds

                # update every PID_frequency Hz
                if (time_now - time_output > 1 / 30):
                    angle = moving_avg(read_angle())
                    print("angle: " + str("{0:.2f}".format(angle)) 
                        + " finger: " + str("{0:.2f}".format(finger_bank)) 
                        + " hand: " + str("{0:.2f}".format(hand_bank)))

                    if (debug_opti):
                        # print(str("{0:.2f}".format(hand_attitude)) + " " + str("{0:.2f}".format(hand_heading)) + " " 
                        #     + str("{0:.2f}".format(hand_bank))
                        #     + " -- "
                        #     + str("{0:.2f}".format(finger_attitude)) + " " + str("{0:.2f}".format(finger_heading)) + " " 
                        #     + str("{0:.2f}".format(finger_bank)) )

                        # attitude = finger_attitude - hand_attitude
                        # heading = finger_heading - hand_heading
                        # bank = finger_bank - hand_bank

                        # out = math.sqrt( math.pow(attitude,2) + math.pow(heading,2) + math.pow(bank,2))

                        # print(out)

                        print(str("{0:.2f}".format(t_attitude)) + " " + str("{0:.2f}".format(t_heading)) + " " 
                            + str("{0:.2f}".format(t_bank)))

                    time_output = time.time()

            # ard_angle.close()
            study_mode = 0

        else:
            print("Wrong input, please select again... Input is " + study_mode)
            study_mode = 0


# Animate plot
def animate(i, xs, ys):
    # generate random values to show
    #sensor_value = np.random.random()
    global angle
    sensor_value = angle

    # Add x and y to lists
    xs.append(datetime.now().strftime('%M:%S.%f'))
    ys.append(sensor_value)
    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]
    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)
    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('sensor value')
    plt.ylabel('unit')

# Angle functions
def read_angle():
    global prev_angle
    # if no physical inputs, use random values
    if opti_connected == True: 
        hand_bank_zeroed     = hand_bank - hand_bank_off
        finger_bank_zeroed   = finger_bank - finger_bank_off
        angle = - finger_bank_zeroed + hand_bank_zeroed        
    else:
        # angle = np.random.random() * 10 + target - 9 #always hovering above target
        if prev_angle < target - 5:
            # climbing from 0 to target
            angle = prev_angle + np.random.random() * 0.2
        else:
            # stabilizing around target
            angle = np.random.random() * 2 - 1 + target
        prev_angle = angle
    return angle

def setOffset(): 
    global finger_bank_off, hand_bank_off

    if (opti_connected):
        finger_bank_off = finger_bank
        hand_bank_off = hand_bank

def get_angular_velocity(current_angle, current_angle_time):
    global prev_angle
    global prev_angle_time 

    try:
        angular_velocity = (current_angle - prev_angle) / (current_angle_time - prev_angle_time)
    except:
        angular_velocity = 0

    # print(str(current_angle) + " --- " + str(current_angle - prev_angle) + "  " + str(current_angle_time - prev_angle_time) + " = " + str(angular_velocity))
    # prev_angle = current_angle
    prev_angle_time = current_angle_time

    return angular_velocity


def moving_avg(input): # moving average filter
    global angle_array
    global moving_avg_counter

    angle_array.pop(0)          # remove first element
    angle_array.append(input)   # add input to last element

    # ignore first values to initialize array
    if moving_avg_counter != 0:
        moving_avg_counter -= 1
        if debug_filter:
            print ("Modified list is : " + str(angle_array) + " output " + str(input))
        return input

    else: 
        output = 0
        for x in angle_array:
            output += x
        output = output / len(angle_array)
        if debug_filter:
            print ("Modified list is : " + str(angle_array) + " output " + str(output))
        return output

# Arduino exo functions
def exo_lock(): # Lock joint ring mcp
    global brake_state
    brake_state = 1
    serial_cmd = '1\n'
    if ard_exo_connected:
        ard_exo.write(serial_cmd.encode())
        if debug:
            print("locking")
    else:
        print("locking")

def exo_unlock(): # Unlock joint ring mcp
    global brake_state
    brake_state = 0
    serial_cmd = '0\n'
    if ard_exo_connected:
        ard_exo.write(serial_cmd.encode())
        if debug:
            print("unlocking")
    else:
        print("unlocking")

# EMS functions
def set_pulse_width(pid_output, channel):
    # modify below if need asymetric mapping
    # if channel == 1:
    #     pulse_width = abs(((pid_output) * 250) / target) + 200
    # else:
    #     pulse_width = abs(((pid_output) * 250) / target) + 200

    pulse_width = pid_output
    # Bounding pulse-width range
    # if pulse_width < 200:
    #     pulse_width = 200
    # if pulse_width > 450:
    #     pulse_width = 450
    return int(pulse_width)

# Optitrack functions
def quaternion_to_euler(qx, qy, qz, qw):
    # from NATUiles.cpp - SampleClient3D Motive example:
    Nq = qx * qx + qy * qy + qz * qz + qw * qw
    if Nq > 0.0:
        s = 2.0 / Nq
    else:
        s = 0.0

    xs = qx*s
    ys = qy*s
    zs = qz*s

    wx = qw*xs
    wy = qw*ys
    wz = qw*zs

    xx = qx*xs
    xy = qx*ys
    xz = qx*zs

    yy = qy*ys
    yz = qy*zs
    zz = qz*zs

    cy = math.sqrt((1-(xx+yy))**2 + (yz-wx)**2)

    if (cy > 16 * sys.float_info.epsilon):
        roll  = math.atan2((xy-wz), (1-(yy+zz)))
        yaw   = math.atan2(-(xz+wy), cy)
        pitch = math.atan2((yz-wx), (1-(xx+yy)))
    else:
        roll  = math.atan2(-(xy+wz), (1-(xx+zz)))
        yaw   = math.atan2(-(xz+wy), cy)
        pitch = 0

    # EulParOdd
    roll = - roll
    yaw = - yaw
    pitch = - pitch

    # EulFrmR
    temp = roll
    roll = pitch
    pitch = temp

    return [math.degrees(angle) for angle in [roll, yaw, pitch]]  # TODO: May need to change some things to negative to deal with left-handed coordinate system.


# This is a callback function that gets connected to the NatNet client. It is called once per rigid body per frame
def receiveRigidBodyFrame( id, position, rotation ):
    global hand_attitude, hand_heading, hand_bank
    global finger_attitude, finger_heading, finger_bank
    global t_attitude, t_heading, t_bank
    # print( "Received frame for rigid body", id )
    if id == 1:
        hand_qx, hand_qy, hand_qz, hand_qw = rotation
        hand_attitude, hand_heading, hand_bank = quaternion_to_euler(hand_qx, hand_qy, hand_qz, hand_qw)

    if id == 2:
        finger_qx, finger_qy, finger_qz, finger_qw = rotation
        finger_attitude, finger_heading, finger_bank = quaternion_to_euler(finger_qx, finger_qy, finger_qz, finger_qw)

    if id == 3:
        t_qx, t_qy, t_qz, t_qw = rotation
        t_attitude, t_heading, t_bank = quaternion_to_euler(t_qx, t_qy, t_qz, t_qw)

# This is a callback function that gets connected to the NatNet client and called once per mocap frame.
# def receiveNewFrame( frameNumber, markerSetCount, unlabeledMarkersCount, rigidBodyCount, skeletonCount,
#                     labeledMarkerCount, timecode, timecodeSub, timestamp, isRecording, trackedModelsChanged ):
#     print( "Received frame", frameNumber )

def exit_handler():
    # unlocks brakes when exiting
    if (ard_exo_connected):
        exo_unlock()

if __name__ == "__main__":
    atexit.register(exit_handler)
    main()