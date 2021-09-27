"""
Open an OSC server and read from/write to BLE (nRF)

Python dependencies: bleak, python-osc
"""
import threading
import platform
import asyncio
import logging
import time

# import CoreBluetooth

from bleak import BleakClient
from pythonosc import osc_server
from pythonosc import dispatcher

from ems_controller import EMSController


# Turn this on if you have BLE
ble = True

# BLE device settings
# ======================================================= #
BLE_MAC_ADDR = "E2:EF:9C:05:9B:A9"  # dextrEMS board address, different for all boards
BLE_IDENTIFIER = "04F380A7-181D-4836-8489-8380BA6B7E92"  # dextrEMS
# characteristic for write (LED in blinky example)
LED_UUID = "00001525-1212-efde-1523-785feabcd123"
# characteristic for read (button in blinky example)
SENSOR_UUID = "00001524-1212-efde-1523-785feabcd123"
# ======================================================= #

# OSC server
# ======================================================= #
# OSC_IP = "127.0.0.1"  # local
# OSC_IP = "192.168.0.17" # cross device
OSC_IP = "0.0.0.0"  # local device's OSC_IP on LAN
OSC_PORT = 5006
# ======================================================= #

# EMS_PORT = "/dev/tty.usbserial-HMYID101"
EMS_PORT = "COM4"

# this is the variable we want to read from OSC and send to BLE
motor_state = 0
receive_motor = True
ems_init = False
ems = None

# OSC: we change global variable "motor_state" if we recevie \motors
# message


def motor_handler(address, *args):
    # print(f"{address}: {args}")
    global motor_state
    motor_state = str(args[0])
    global receive_motor
    receive_motor = True

    print("OSC receives: " + str(motor_state))


def ems_handler(address, *args):
    # print(f"{address}: {args}")

    if len(args) == 1:
        print("OSC receives: " + str(args))
        global ems
        ems = EMSController(EMS_PORT)
        global ems_init
        ems_init = True

    if len(args) == 4 and ems_init == True:
        print("OSC receives: " + str(args))
        pulse_count, channel, pulse_width, intensity = args
        ems.send_signal(pulse_count, channel, pulse_width, intensity)


dispatcher = dispatcher.Dispatcher()
dispatcher.map("/motors", motor_handler)
dispatcher.map("/ems", ems_handler)


def callback(sender, data):
    # print(f"{sender}: {data}")
    data_converted = int.from_bytes(bytes(data), byteorder="little")
    print("BLE sensor: " + str(data_converted))


# all about BLE
async def run(address, loop, debug=True):
    log = logging.getLogger(__name__)
    if debug:
        import sys

        loop.set_debug(True)
        log.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        log.addHandler(h)

    async with BleakClient(address, loop=loop) as client:
        x = await client.is_connected()
        log.info("BLE Connected: {0}".format(x))

        # await client.start_notify(SENSOR_UUID, callback)
        print("Start notification")

        while await client.is_connected():

            # read sensor value from BLE
            value = await client.read_gatt_char(SENSOR_UUID)
            value_converted = int.from_bytes(bytes(value), byteorder="big")
            # print("BLE sensor: " + str(value_converted))
            # print("I/O Data Post-Write Value: {0}".format(value))

            global receive_motor
            global motor_state

            # write to BLE when receive from OSC
            if receive_motor:
                # messages need to be in bytes, 03FF -> OK, 3FF -> not OK
                b = bytearray.fromhex(motor_state)

                print(b)
                await client.write_gatt_char(LED_UUID, b)
                print("BLE write: " + str(b))
                receive_motor = False

        await client.stop_notify(SENSOR_UUID)
        print("Stop notification")
        time.sleep(0.5)


if __name__ == "__main__":

    # start OSC server in a thread to prevent conflicting with BLE
    server = osc_server.ThreadingOSCUDPServer((OSC_IP, OSC_PORT), dispatcher)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True # needed for Windows, otherwise can't stop application
    server_thread.start()
    print("open an OSC server at " + OSC_IP + ":" + str(OSC_PORT))
    # server.serve_forever()

    address = (
        # for windows we need mac address
        BLE_MAC_ADDR
        if platform.system() != "Darwin"
        # for mac we need identifier
        else BLE_IDENTIFIER
    )

    if ble:
        # start BLE, this will run forever
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(address, loop, True))
