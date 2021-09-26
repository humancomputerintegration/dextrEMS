import serial
import time

from pythonosc import osc_server
from pythonosc import dispatcher

# OSC server
# ======================================================= #
ip = "127.0.0.1" # local
# ip = "192.168.0.17" # cross device
port = 5006
# ======================================================= #

# Serial 
# ======================================================= #
# serPort = "/dev/ttyS4" # use for mac COM4
serPort = "COM4"		 # use for windows
baudRate = 9600
# ======================================================= #

# OSC: we change global variable "state" if we recevie \state message
def msg_handler(address, *args):
	#print(f"{address}: {args}")
	print("OSC receives: " + str(args[0]))

	# send to serial
	msgSerial = bytearray.fromhex(args[0])
	ser.write(msgSerial)
	print("Serial sends: " + str(msgSerial))

if __name__ == "__main__":
	# serial setup
	ser = serial.Serial(serPort, baudRate)
	print("Serial port " + serPort + " opened  Baudrate " + str(baudRate))

	# Defining OSC dispatecher
	dispatcher = dispatcher.Dispatcher()
	dispatcher.map("/motors", msg_handler)

	# Start OSC server and run forever
	server = osc_server.ThreadingOSCUDPServer(
	  (ip, port), dispatcher)
	print("Serving on {}".format(server.server_address))
	server.serve_forever()