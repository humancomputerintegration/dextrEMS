#!/usr/bin/python
# Filename: beat.py
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import singlepulse
import time

version = '0.2'
#version = '0.1' was weird with regards to the emphasis beat

def beater(beats,unit,delay,width,flex_amp,extend_amp,emphasis,ems):
	#beats=number of beats in total
	#unit is the note unit (not used)
	#delay=time between notes
	#width=microseconds of each pulse width
	#flex_amp= mAmps of the flexor
	#extend_amp= mAmps of the extensor
	#emphasis = how much mAmps we add as a emphasis (careful!)
	flex_reps=20
	extend_reps=25
	if emphasis == None:
            emphasis=0

	#first emphatic beat
        print('power=emphasis+ext' + str(extend_amp+emphasis))
        print('power=emphasis+flex' + str(flex_amp+emphasis))
        for x in range(0, extend_reps):
            cmd1 = singlepulse.generate(2,width,extend_amp+emphasis)
            ems.write(cmd1)
            time.sleep(0.01)
	    #time.sleep(0.1)
        #time.sleep(0.1)
        for x in range(0, flex_reps):
            cmd1 = singlepulse.generate(1,width,flex_amp+emphasis)
            ems.write(cmd1)
            time.sleep(0.01)
        #for x in range(0, 6):
        #    cmd1 = singlepulse.generate(2,width,extend_amp)
        #    ems.write(cmd1)
        #    time.sleep(0.05)
        time.sleep(delay)

	for x in range(0,beats-1):
            #print('power=ext' + str(extend_amp+emphasis))
            #print('poweris+flex' + str(flex_amp+emphasis))
            for x in range(0, extend_reps):
	        if emphasis == None:
	            cmd1 = singlepulse.generate(2,width,extend_amp+emphasis)
	        else: cmd1 = singlepulse.generate(2,width,extend_amp)
                ems.write(cmd1)
                time.sleep(0.01)
	        #time.sleep(0.1)
            for x in range(0, flex_reps):
	        if emphasis == None:
	            cmd1 = singlepulse.generate(1,width,flex_amp+emphasis)
	        else: cmd1 = singlepulse.generate(1,width,flex_amp)
                ems.write(cmd1)
                time.sleep(0.01)
            #for x in range(0, 6):
            #    cmd1 = singlepulse.generate(2,width,extend_amp)
            #    ems.write(cmd1)
            #    time.sleep(0.05)
            time.sleep(delay)

def crescendo(beats,unit,delay,width,flex_amp,extend_amp,speed,ems):
        #beats=number of beats in total
        #unit is the note unit (not used)
        #delay=time between notes
        #width=microseconds of each pulse width
        #flex_amp= mAmps of the flexor
        #extend_amp= mAmps of the extensor
        #speed_curve = how fast the crescento builds up

        for x in range(0,beats):
                for x in range(0, 2):
                        cmd1 = singlepulse.generate(1,width,extend_amp)
                        ems.write(cmd1)
                        time.sleep(0.01)
                for x in range(0, 20):
                        cmd1 = singlepulse.generate(2,width,flex_amp)
                        ems.write(cmd1)
                        time.sleep(0.01)
                for x in range(0, 6):
                        cmd1 = singlepulse.generate(1,width,extend_amp)
                        ems.write(cmd1)
                        time.sleep(0.05)
                time.sleep(delay)
                delay=delay-(delay/speed_curve)  #10 - 10/2 = 5

# End of beat.py
