#Copyright © 2018 Naturalpoint
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.


# OptiTrack NatNet direct depacketization sample for Python 3.x
#
# Uses the Python NatNetClient.py library to establish a connection (by creating a NatNetClient),
# and receive data via a NatNet connection and decode it using the NatNetClient library.

from NatNetClient import NatNetClient
import time
import math

# hand_attitude, hand_heading, hand_bank 
# finger_attitude, finger_heading, finger_bank 

def quaternion_to_euler(qx, qy, qz, qw):
    """Convert quaternion (qx, qy, qz, qw) angle to euclidean (x, y, z) angles, in degrees.
    Equation from http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToEuler/"""

    heading = math.atan2(2*qy*qw-2*qx*qz , 1 - 2*qy**2 - 2*qz**2)
    attitude = math.asin(2*qx*qy + 2*qz*qw)
    bank = math.atan2(2*qx*qw-2*qy*qz , 1 - 2*qx**2 - 2*qz**2)

    return [math.degrees(angle) for angle in [attitude, heading, bank]]  # TODO: May need to change some things to negative to deal with left-handed coordinate system.

# This is a callback function that gets connected to the NatNet client and called once per mocap frame.
# def receiveNewFrame( frameNumber, markerSetCount, unlabeledMarkersCount, rigidBodyCount, skeletonCount,
#                     labeledMarkerCount, timecode, timecodeSub, timestamp, isRecording, trackedModelsChanged ):
#     print( "Received frame", frameNumber )

# This is a callback function that gets connected to the NatNet client. It is called once per rigid body per frame
def receiveRigidBodyFrame( id, position, rotation ):
    global hand_attitude, hand_heading, hand_bank
    global finger_attitude, finger_heading, finger_bank
    # print( "Received frame for rigid body", id )
    if id == 2:
        hand_qx, hand_qy, hand_qz, hand_qw = rotation
        hand_attitude, hand_heading, hand_bank = quaternion_to_euler(hand_qx, hand_qy, hand_qz, hand_qw)
        # print(str("{0:.2f}".format(tPitch)) + " " + str("{0:.2f}".format(tYaw)) + " " 
        #     + str("{0:.2f}".format(tRoll)) + " " + str("{0:.2f}".format(tW)))

        # print(str("{0:.2f}".format(hand_attitude)) + " " + str("{0:.2f}".format(hand_heading)) + " " 
        #     + str("{0:.2f}".format(hand_bank)))

    if id == 3:
        finger_qx, finger_qy, finger_qz, finger_qw = rotation
        finger_attitude, finger_heading, finger_bank = quaternion_to_euler(finger_qx, finger_qy, finger_qz, finger_qw)
        # print(str("{0:.2f}".format(tPitch)) + " " + str("{0:.2f}".format(tYaw)) + " " 
        #     + str("{0:.2f}".format(tRoll)) + " " + str("{0:.2f}".format(tW)))

        # print(str("{0:.2f}".format(finger_attitude)) + " " + str("{0:.2f}".format(finger_heading)) + " " 
        #     + str("{0:.2f}".format(finger_bank)))

    # print(rotation)

# This will create a new NatNet client
streamingClient = NatNetClient()

# Configure the streaming client to call our rigid body handler on the emulator to send data out.
streamingClient.newFrameListener = None #receiveNewFrame
streamingClient.rigidBodyListener = receiveRigidBodyFrame

# Start up the streaming client now that the callbacks are set up.
# This will run perpetually, and operate on a separate thread.
streamingClient.run()

set_offset = False
count = 0

# zero delta angle
# temp = input("press any key to zero the delta angle")
# hand_attitude_off, hand_heading_off, hand_bank_off = hand_attitude, hand_heading, hand_bank
# finger_attitude_off, finger_heading_off, finger_bank_off = finger_attitude, finger_heading, finger_bank

hand_attitude, hand_heading, hand_bank  = 0, 0, 0
finger_attitude, finger_heading, finger_bank = 0, 0, 0
del_attitude_offset = 0
del_heading_offset  = 0
del_bank_offset     = 0
hand_heading_off    = 0
finger_heading_off  = 0


while True:
    # del_attitude = abs( abs(finger_attitude - hand_attitude_off)  - abs(hand_attitude - hand_attitude_off))
    # del_heading  = abs( abs(finger_heading  - finger_heading_off) - abs(hand_heading  - hand_heading_off))
    # del_bank     = abs( abs(finger_bank     - finger_bank_off)    - abs(hand_bank     - hand_bank_off))
    
    del_attitude = abs(finger_attitude - hand_attitude )
    del_heading  = abs(finger_heading  - hand_heading  )
    del_bank     = abs(finger_bank     - hand_bank     )

    # print("pre "
    #     + str("{0:.2f}".format(del_attitude)) + " " 
    #     + str("{0:.2f}".format(del_heading)) + " " 
    #     + str("{0:.2f}".format(del_bank)))
    
    if set_offset == False and count == 1:
        # del_attitude_offset = del_attitude
        # del_heading_offset  = del_heading
        # del_bank_offset     = del_bank
        finger_heading_off = finger_heading
        hand_heading_off = hand_heading

        set_offset = True
        
        print("offset "
        + str("{0:.2f}".format(del_attitude_offset)) + " " 
        + str("{0:.2f}".format(del_heading_offset)) + " " 
        + str("{0:.2f}".format(del_bank_offset)))


    del_attitude = del_attitude - del_attitude_offset  
    del_heading  = del_heading  - del_heading_offset
    del_bank     = del_bank     - del_bank_offset 

    # print("post " 
    #     + str("{0:.2f}".format(del_attitude)) + " " 
    #     + str("{0:.2f}".format(del_heading)) + " " 
    #     + str("{0:.2f}".format(del_bank)))
    hand_heading = hand_heading - hand_heading_off
    finger_heading = finger_heading - finger_heading_off

    print("post " 
        + str("{0:.2f}".format(hand_heading)) + " " 
        + str("{0:.2f}".format(finger_heading)) + " " 
        + str("{0:.2f}".format(finger_heading - hand_heading)))

    count = count+1
    time.sleep(0.01)