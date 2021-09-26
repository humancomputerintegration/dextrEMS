#!/sr/bin/python
# Filename: emstools.py

import singlepulse
import time

version = '0.1'

def sweep(amp_current,pulse_width,delay_seconds,ems):  #go through all channels with the same pulse
	for i in range(1,9):
                ems.write(singlepulse.generate(i,pulse_width,amp_current))
                time.sleep(delay_seconds)

#def sweep(amp_current,pulse_width,delay_seconds,ems,start,end):  #go through all channels with the same pulse
#	for i in range(start-1,end+1):
 #               ems.write(singlepulse.generate(i,pulse_width,amp_current))
  #              time.sleep(delay_seconds)
# End of emstools.py
