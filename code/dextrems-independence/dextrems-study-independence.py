# pip install opencv-python
# require rehastim-integration-lib at the same directory

import cv2 
import numpy as np
import serial
import random
import csv
import os.path
import threading

# EMS
import sys
sys.path.append('./rehastim-integration-lib/ems_interface/modules/')
sys.path.append('./rehastim-integration-lib/ems_interface/tools-and-abstractions/')
import singlepulse
import SerialThingy
import time

# SETTINGS
# ------------------------- #
# debug = True
debug = False # Turn this on to use real serial ports
serial_arduino_path = 'COM9' # windows
# serial_arduino_path = '/dev/cu.usbmodem1411401' # mac
# make sure we have a pair of webcams 1920x1080
webcam_calibration_filepath = './pre-study-camera-calibration/calibration_pair_1080p.para'
# EMS default values
serial_ems_path = 'COM5' # windows
# serial_ems_path = '/dev/cu.usbserial-HMYID101' # mac
channel = 1
intensity = 4
pulse_width = 300
pulse_count = 80
delay = 0.0098 # 9,800 uS
# ------------------------- #
# ------------------------- #
# ------------------------- #

if (debug):
    print('debug mode: not making serial connections')

state = 0
# 0: test EXO
# 1: calibrate EMS
# 2: study
key = cv2. waitKey(1)

# WEBCAM
# ------------------------- #
# we do everything in this resolution!
w = 1920
h = 1080
# camera calibration parameters
cv_file = cv2.FileStorage(webcam_calibration_filepath, cv2.FILE_STORAGE_READ)
camera_matrix = cv_file.getNode("K").mat()
dist_matrix = cv_file.getNode("D").mat()
cv_file.release()
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(camera_matrix,dist_matrix,(w,h),1,(w,h))

# open two webcams: check id here
webcam_left = np.zeros((h,w,3), np.uint8)
webcam_right = np.zeros((h,w,3), np.uint8)
webcam_left = cv2.VideoCapture(1)
webcam_left.set(3, 1920)
webcam_right = cv2.VideoCapture(2)
webcam_right.set(3, 1920)
frame_combined = np.zeros((h,w*2,3), np.uint8)
# ------------------------- #

# ARDUINO
# ------------------------- #
# open arduino
serial_arduino = serial.Serial()
if (not debug):
    serial_arduino = serial.Serial(serial_arduino_path, 9600)
    print(serial_arduino.name)

arduino_lock_state = [0] * 8
arduino_mux_state = 0
def init_arduino_serial():
    if (not debug):
        serial_arduino = serial.Serial(serial_arduino_path, 9600)
        print(serial_arduino.name)

def send_arduino_led(cmd):
    serial_cmd = 'd0\n'
    if (cmd == 1): 
        serial_cmd = 'd1\n'
    if (not debug):
        serial_arduino.write(serial_cmd.encode())

def send_arduino_enable(cmd):
    global arduino_mux_state
    serial_cmd = 'e0\n'
    arduino_mux_state = 0
    if (cmd == 1): 
        serial_cmd = 'e1\n'
        arduino_mux_state = 1
    if (not debug):
        serial_arduino.write(serial_cmd.encode())

def send_arduino_lock():
    serial_cmd = 'l1\n'
    arduino_lock_state[0] = 1
    arduino_lock_state[1] = 1
    arduino_lock_state[2] = 1
    arduino_lock_state[3] = 1
    arduino_lock_state[4] = 1
    arduino_lock_state[5] = 1
    arduino_lock_state[6] = 1
    arduino_lock_state[7] = 1
    if (not debug):
        serial_arduino.write(serial_cmd.encode())

def send_arduino_unlock(cmd):
    serial_cmd = '\n'
    if (cmd == 8): 
        serial_cmd = 'l0\n'
        arduino_lock_state[0] = 0
        arduino_lock_state[1] = 0
        arduino_lock_state[2] = 0
        arduino_lock_state[3] = 0
        arduino_lock_state[4] = 0
        arduino_lock_state[5] = 0
        arduino_lock_state[6] = 0
        arduino_lock_state[7] = 0

    if (cmd == 0): 
        # unlock index pip
        serial_cmd = 'u120\n'
        arduino_lock_state[0] = 0
    if (cmd == 1): 
        # unlock index mcp
        serial_cmd = 'u110\n'
        arduino_lock_state[1] = 0
    if (cmd == 2): 
        # unlock middle pip
        serial_cmd = 'u220\n'
        arduino_lock_state[2] = 0
    if (cmd == 3): 
        # unlock middle mcp
        serial_cmd = 'u210\n'
        arduino_lock_state[3] = 0
    if (cmd == 4): 
        # unlock ring pip
        serial_cmd = 'u320\n'
        arduino_lock_state[4] = 0
    if (cmd == 5): 
        # unlock ring mcp
        serial_cmd = 'u310\n'
        arduino_lock_state[5] = 0
    if (cmd == 6): 
        # unlock pinky pip
        serial_cmd = 'u420\n'
        arduino_lock_state[6] = 0
    if (cmd == 7): 
        # unlock pinky mcp
        serial_cmd = 'u410\n'
        arduino_lock_state[7] = 0

    if (not debug):
        serial_arduino.write(serial_cmd.encode())

def state2str(state):
    if (state == 1):
        return 'locked'
    return 'unlocked'

def enable2str(state):
    if (state == 1):
        return 'enabled'
    return 'disabled'
# ------------------------- #

# EMS
# ------------------------- #
FAKE_SERIAL = False 
if (debug):
    FAKE_SERIAL = True

serial_response_active = False
ems = SerialThingy.SerialThingy(FAKE_SERIAL)

if (not debug):
    ems.open_port(serial_ems_path, serial_response_active)

ems_channel_assign = [1] * 8
ems_intensity_assign = [4] * 8
ems_pulsewidth_assign = [300] * 8
ems_channel_assign_select = 1

def fire_ems(trial_channel, trial_intensity, trial_pulsewidth):
    global ems, pulse_count, delay
    for i in range(pulse_count):
        time.sleep(delay)
        ems.write(singlepulse.generate(trial_channel, trial_pulsewidth, trial_intensity))

# EMS & arduino for each trial

def trial_lock_exo():
    global trial, trials
    which_joint = joint_id(trials[trial-1][1], trials[trial-1][2])

    # lock first
    if (not debug):
        send_arduino_enable(1)
        send_arduino_led(1)
        send_arduino_lock()
        send_arduino_unlock(which_joint)

def trial_fire_ems():
    global trial, trials
    # use these for stimulation
    # ems_channel_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
    # ems_intensity_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
    # ems_pulsewidth_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
    which_joint = joint_id(trials[trial-1][1], trials[trial-1][2])

    # fire ems
    if (not debug):
        fire_ems(ems_channel_assign[which_joint], ems_intensity_assign[which_joint], ems_pulsewidth_assign[which_joint]);

    # save image
    save_img()

    # release locks
    if (not debug):
        send_arduino_unlock(8)
        send_arduino_enable(0)
        send_arduino_led(0)


# ------------------------- #

# USER STUDY
# ------------------------- #
user_no = 1
group_no = 1
repeat = 3
trial = 1
trial_total = 0
trials = []
save_id = 0
trial_save_filename = []

def generate_study_order_file():
    filename = 'user_'+str(user_no)+'_group_'+str(group_no)+'_study_order.csv'
    trial_no = 1
    trials = ['index,pip','index,mcp','middle,pip','middle,mcp','ring,pip','ring,mcp','pinky,pip','pinky,mcp'] *repeat
    conditions = []
    if (group_no == 1):
        conditions = ['ems', 'exo']
    else:
        conditions = ['exo', 'ems']

    f = open(filename, 'a')
    random.shuffle(trials)
    for t in trials:
        f.write(str(trial_no)+','+conditions[0]+','+t+'\n')
        trial_no += 1
    random.shuffle(trials)
    for t in trials:
        f.write(str(trial_no)+','+conditions[1]+','+t+'\n')
        trial_no += 1
    f.close()

def read_study_order_file():
    global trial, trial_total, trial_save_filename
    trials.clear()
    trial = 1
    filename = 'user_'+str(user_no)+'_group_'+str(group_no)+'_study_order.csv'
    if not os.path.isfile(filename):
        return False
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            trials.append([row[1],row[2],row[3]])
            line_count += 1
        trial_total = line_count

    trial_save_filename = [''] * trial_total
    return True

def joint_id(finger_str, joint_str):
    if (finger_str == 'index'):
        if (joint_str == 'pip'):
            return 0
        elif (joint_str == 'mcp'):
            return 1
    if (finger_str == 'middle'):
        if (joint_str == 'pip'):
            return 2
        elif (joint_str == 'mcp'):
            return 3
    if (finger_str == 'ring'):
        if (joint_str == 'pip'):
            return 4
        elif (joint_str == 'mcp'):
            return 5
    if (finger_str == 'pinky'):
        if (joint_str == 'pip'):
            return 6
        elif (joint_str == 'mcp'):
            return 7
    return 8
# ------------------------- #

def save_img():
    global user_no, group_no, trial, trials
    global trial_save_filename
    global save_id
    global frame_combined

    save_id += 1
    save_filename = 'user_'+str(user_no)+'_group_'+str(group_no)+'_trial_'+str(trial)+'_'+trials[trial-1][0]+'_'+trials[trial-1][1]+'_'+trials[trial-1][2]+'_'+str(save_id)+'.jpg'
    cv2.imwrite(filename=save_filename, img=frame_combined)
    trial_save_filename[trial-1] = 'image id ' + str(save_id) + ' saved!'

cv2.namedWindow('user study')

# GUI LOOP
while True:
    try:
        if (state == 0):
            # test exo
            frame_combined = np.zeros((h,w*2,3), np.uint8)
            cv2.putText(frame_combined,'[A] test EXO [B] calibrate EMS [C] study', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.line(frame_combined, (70, 60), (210, 60), (255,255,255), 2) 
            cv2.putText(frame_combined,'[Z] reconnect arduino', (10,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'mux:             [+/-] enable/disable', (10,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,enable2str(arduino_mux_state), (100,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[9] lock all   [0] unlock all', (10,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'unlock individual:', (10,250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[1] index pip:', (10,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[0]), (280,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[Q] index mcp:', (10,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[1]), (280,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[2] middle pip:', (10,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[2]), (280,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[W] middle mcp:', (10,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[3]), (280,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[3] ring pip:', (10,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[4]), (280,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[E] ring mcp:', (10,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[5]), (280,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[4] pinky pip:', (10,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[6]), (280,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[R] pinky mcp:', (10,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,state2str(arduino_lock_state[7]), (280,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        if (state == 1):
            # calibrate EMS
            if (ems_channel_assign_select > 8):
                ems_channel_assign_select = 1
            elif (ems_channel_assign_select < 1):
                ems_channel_assign_select = 8

            frame_combined = np.zeros((h,w*2,3), np.uint8)
            cv2.putText(frame_combined,'[A] test EXO [B] calibrate EMS [C] study', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.line(frame_combined, (290, 60), (500, 60), (255,255,255), 2) 
            cv2.rectangle(frame_combined, (10,80), (780, 210), (255, 255, 255), 1)
            cv2.putText(frame_combined,'intensity:', (20,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[-/+]', (230,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,str(intensity), (180,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pulse width:', (20,180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[(/)]', (330,180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,str(pulse_width), (230,180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'channel:', (450,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[1~8]', (660,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,str(channel), (610,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[SPACE] stimulate!', (450,180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[U] update above as the selected joint [UP/DOWN/J/K] select:', (10,250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  index pip:', (10,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[0]), (240,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[0]), (350,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[0]), (460,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 1):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  index mcp:', (10,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[1]), (240,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[1]), (350,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[1]), (460,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 2):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  middle pip:', (10,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[2]), (240,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[2]), (350,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[2]), (460,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 3):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  middle mcp:', (10,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[3]), (240,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[3]), (350,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[3]), (460,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 4):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  ring pip:', (10,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[4]), (240,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[4]), (350,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[4]), (460,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 5):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  ring mcp:', (10,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[5]), (240,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[5]), (350,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[5]), (460,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 6):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,550), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  pinky pip:', (10,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[6]), (240,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[6]), (350,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[6]), (460,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 7):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,600), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'  pinky mcp:', (10,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'ch '+str(ems_channel_assign[7]), (240,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(ems_intensity_assign[7]), (350,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(ems_pulsewidth_assign[7]), (460,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            if (ems_channel_assign_select == 8):
                cv2.putText(frame_combined,'>                                   [ENTER] stimulate!', (5,650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[S] save a screenshot for backup', (10,700), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        if (state == 2 or state == 3):
            # study open webcams

            frame_right = np.ones((h,w,3), np.uint8)
            frame_right[:] = (255,255,255)
            check_right, frame_right = webcam_right.read()
            # right one should be FHD one
            frame_right = cv2.resize(frame_right,(w,h))
            # undistort webcam
            frame_right = cv2.undistort(frame_right, camera_matrix, dist_matrix, None, newcameramtx)



            frame_left = np.ones((h,w,3), np.uint8)
            frame_left[:] = (255,255,255)
            check_left, frame_left = webcam_left.read()
            # # left one should be low res
            # frame_left = frame_left[0:720, 0:1280]
            if check_left == True:
                frame_left = cv2.resize(frame_left,(w,h))
                # # undistort webcam
                frame_left = cv2.undistort(frame_left, camera_matrix, dist_matrix, None, newcameramtx)

                # frame_debug_2 = webcam_right.read()

                # frame_debug_1 = webcam_left.read()
            else:
                frame_left = np.ones((h,w,3), np.uint8)


            frame_combined = np.hstack((frame_left, frame_right))

            # white background
            cv2.rectangle(frame_combined, (10,10), (1000, 275), (255, 255, 255), -1)
            # tabbed
            cv2.putText(frame_combined,'[A] test EXO [B] calibrate EMS [C] study', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
            cv2.line(frame_combined, (585, 60), (665, 60), (0,0,0), 2) 

        if (state == 2):
            # ready to read study order file (csv)
            cv2.putText(frame_combined,'user number:', (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,str(user_no), (260,90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[<-/->]', (300,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'group number:', (10,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,str(group_no), (260,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[1: ems exo /2: exo ems]', (300,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[ENTER] read user_'+str(user_no)+'_group_'+str(group_no)+'_study_order.csv and start', (10,170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'repeat:', (10,210), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,str(repeat), (260,210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[-/+]', (300,210), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[G] generate random order as user_'+str(user_no)+'_group_'+str(group_no)+'_study_order.csv', (10,240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)

        if (state == 3):
            # real user study trial
            cv2.putText(frame_combined,'user '+str(user_no)+' group '+str(group_no), (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'trial', (10,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,str(trial), (100,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'/', (160,130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,str(trial_total), (200,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,trials[trial-1][0], (280,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,trials[trial-1][1], (380,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,trials[trial-1][2], (500,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[P] prev trial [N] next trial', (10,170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[L] lock exo [SPACE] stimluate ems!', (10,210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(frame_combined,'[S] save image', (10,250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)

            cv2.putText(frame_combined,'ch '+str(channel), (660,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'int '+str(intensity), (770,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'pw '+str(pulse_width), (880,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[1-8]  [-/+]  [(/)]', (660,170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame_combined,'[U] update setting', (660,210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 1, cv2.LINE_AA)

            if (trial == trial_total/2 + 1):
                cv2.rectangle(frame_combined, (270,70), (520, 100), (0, 0, 0), -1)
                cv2.putText(frame_combined,'condition change!', (280,90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)

            if (trial_save_filename[trial-1] != ''):
                cv2.rectangle(frame_combined, (270,230), (550, 260), (0, 0, 0), -1)
                cv2.putText(frame_combined, trial_save_filename[trial-1], (280,250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)

        cv2.imshow('image', frame_combined)

        key = cv2.waitKey(1)
        # check key
        # print(key)

        # switch states
        if key == ord('a'):
            state = 0
        if key == ord('b'):
            state = 1
        if key == ord('c'):
            state = 2

        # exo check: arduino
        if (state == 0):
            if key == ord('z'): 
                init_arduino_serial()
            # enable/disable mux
            if key == ord('-'): # minus
                send_arduino_enable(0)
                send_arduino_led(0)
            if key == ord('='): # plus
                send_arduino_enable(1)
                send_arduino_led(1)
            # unlock each joints
            if key == ord('1'): 
                # unlock index pip
                send_arduino_unlock(0)
            if key == ord('q'): 
                # unlock index mcp
                send_arduino_unlock(1)
            if key == ord('2'): 
                # unlock middle pip
                send_arduino_unlock(2)
            if key == ord('w'): 
                # unlock middle mcp
                send_arduino_unlock(3)
            if key == ord('3'): 
                # unlock ring pip
                send_arduino_unlock(4)
            if key == ord('e'): 
                # unlock ring mcp
                send_arduino_unlock(5)
            if key == ord('4'): 
                # unlock pinky pip
                send_arduino_unlock(6)
            if key == ord('r'): 
                # unlock pinky mcp
                send_arduino_unlock(7)
            if key == ord('0'): # unlock all
                send_arduino_unlock(8)
            # lock
            if key == ord('9'): 
                send_arduino_lock()

        # ems calibration
        if (state == 1):
            # if key == 123: # left
                # print('left')
            # if key == 124: # right
                # print('right')
            if key == 125 or key == ord('j'): # down
                ems_channel_assign_select += 1
            if key == 126 or key == ord('k'): # up 
                ems_channel_assign_select -= 1

            if key == ord(' '): # space 
                # fire ems with setting in the box (global setting)
                if (not debug):
                    ems_thread = threading.Thread(target=fire_ems, args=(channel, intensity, pulse_width))
                    ems_thread.start()

            if key == 13: # enter
                # fire ems with the selected joint data
                if (not debug):
                    ems_thread = threading.Thread(target=fire_ems, args=(ems_channel_assign[ems_channel_assign_select-1], ems_intensity_assign[ems_channel_assign_select-1], ems_pulsewidth_assign[ems_channel_assign_select-1]))
                    ems_thread.start()

            if key == ord('1'): 
                channel = 1
            if key == ord('2'): 
                channel = 2
            if key == ord('3'): 
                channel = 3
            if key == ord('4'): 
                channel = 4
            if key == ord('5'): 
                channel = 5
            if key == ord('6'): 
                channel = 6
            if key == ord('7'): 
                channel = 7
            if key == ord('8'): 
                channel = 8
            if key == ord('-'): # minus
                intensity -= 1
            if key == ord('='): # plus
                intensity += 1
            if key == ord('9'): # (
                pulse_width -= 50
            if key == ord('0'): # )
                pulse_width += 50

            if key == ord('s'): 
                save_id += 1
                save_filename = 'ems_calibration_backup_'+str(save_id) +'.jpg'
                cv2.imwrite(filename=save_filename, img=frame_combined)
            if key == ord('u'): 
                ems_channel_assign[ems_channel_assign_select-1] = channel
                ems_intensity_assign[ems_channel_assign_select-1] = intensity
                ems_pulsewidth_assign[ems_channel_assign_select-1] = pulse_width

        # prepare to read study order file
        if (state == 2):
            if key == 123 or key == ord('j'): # left
                user_no -= 1
                # print('left')
            if key == 124 or key == ord('k'): # right
                user_no += 1
            if key == ord('1'): 
                group_no = 1
            if key == ord('2'): 
                group_no = 2
            if key == ord('-'): # minus
                repeat -= 1
            if key == ord('='): # plus
                repeat += 1
            if key == ord('g'): # plus
                generate_study_order_file()
            if key == 13: # enter
                if (read_study_order_file()):
                    channel = ems_channel_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                    intensity = ems_intensity_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                    pulse_width = ems_pulsewidth_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                    state = 3

        # now real study
        if (state == 3):
            # use these for stimulation
            # ems_channel_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
            # ems_intensity_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
            # ems_pulsewidth_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]

            if key == ord('1'): 
                channel = 1
            if key == ord('2'): 
                channel = 2
            if key == ord('3'): 
                channel = 3
            if key == ord('4'): 
                channel = 4
            if key == ord('5'): 
                channel = 5
            if key == ord('6'): 
                channel = 6
            if key == ord('7'): 
                channel = 7
            if key == ord('8'): 
                channel = 8
            if key == ord('-'): # minus
                intensity -= 1
            if key == ord('='): # plus
                intensity += 1
            if key == ord('9'): # (
                pulse_width -= 50
            if key == ord('0'): # )
                pulse_width += 50
            if key == ord('u'): 
                # update new setting
                ems_channel_assign[joint_id(trials[trial-1][1], trials[trial-1][2])] = channel
                ems_intensity_assign[joint_id(trials[trial-1][1], trials[trial-1][2])] = intensity
                ems_pulsewidth_assign[joint_id(trials[trial-1][1], trials[trial-1][2])] = pulse_width
            if key == ord('n'): 
                # next trial
                if (trial < trial_total):
                    trial += 1
                channel = ems_channel_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                intensity = ems_intensity_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                pulse_width = ems_pulsewidth_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
            if key == ord('p'): 
                # previous trial
                if (trial > 1):
                    trial -= 1
                channel = ems_channel_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                intensity = ems_intensity_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
                pulse_width = ems_pulsewidth_assign[joint_id(trials[trial-1][1], trials[trial-1][2])]
            if key == ord('s'): 
                save_img()

            if key == ord('l'): 
                # lock exo
                trial_lock_exo()

            if key == ord(' '): #space
                # fire ems
                ems_thread = threading.Thread(target=trial_fire_ems)
                ems_thread.start()

        
    except(KeyboardInterrupt):
        print("Turning off camera.")
        webcam_left.release()
        webcam_right.release()
        print("Camera off.")
        print("Program ended.")
        cv2.destroyAllWindows()
        break
