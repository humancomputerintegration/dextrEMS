import threading

class SerialThread (threading.Thread):

    SERIAL_THREAD_DEBUG = True

    def __init__(self,serial_device):
        threading.Thread.__init__(self)
        self.ser = serial_device
    def run (self):
        if SERIAL_THREAD_DEBUG: print("Started a listening SerialThread on " + str(self.ser))
        while 1:
            v = self.ser.read(size=1)
            #print(len(v))
            if(len(v) > 0):
            #v = v.decode("utf-8").rstrip('\r\n') #not sure if needed for EMS SERIAL RESPONSE
                if SERIAL_THREAD_DEBUG: print("SERIAL_THREAD_RESPONSE:" + str(v))
                if SERIAL_THREAD_DEBUG: print(v.encode("hex"))
