import sys

sys.path.append("rehastim-integration-lib/ems_interface/modules/")
sys.path.append(
    "rehastim-integration-lib/ems_interface/tools-and-abstractions/"
)
import singlepulse
import SerialThingy
import time
import serial

FAKE_SERIAL = False
serial_response_active = False


class EMSController:
    def __init__(self, port, pulse_count, channel, pulse_width, intensity):
        self.ems = SerialThingy.SerialThingy(FAKE_SERIAL)
        if len(port) > 1:
            self.ems.open_port(port, serial_response_active)
        else:
            self.ems.open_port(serial_response_active)

        self.channel = channel
        self.pulse_width = pulse_width
        self.intensity = intensity
        self.pulse_count = pulse_count

    def set_param(self, pulse_count, channel, pulse_width, intensity):
        self.channel = channel
        self.pulse_width = pulse_width
        self.intensity = intensity
        self.pulse_count = pulse_count

    # return null
    # self.channel = channel
    # self.pulse_width = pulse_width
    # self.intensity = intensity
    # self.pulse_count = pulse_count

    # def start(self, poort):
    #     ems = SerialThingy.SerialThingy(FAKE_SERIAL)
    #     if len(port) > 1:
    #         ems.open_port(port, serial_response_active)
    #     else:
    #         ems.open_port(serial_response_active)

    #     return ems

    def send_signal(self):
        # TODO: not sure what this open_port is, is it ok to call it every time
        # sending a signal?
        # ems = SerialThingy.SerialThingy(FAKE_SERIAL)
        # if len(port) > 1:
        #     ems.open_port(port, serial_response_active)
        # else:
        #     ems.open_port(serial_response_active)

        for i in range(self.pulse_count):
            self.ems.write(
                singlepulse.generate(
                    self.channel, self.pulse_width, self.intensity
                )
            )
            # ems.write(singlepulse.generate(channel+1, pulse_width, intensity-5))
            # channel number (1-8), pulse width (200-450) in microseconds,
            # intensity (0-100mA, limited 32mA)
            time.sleep(0.01)
