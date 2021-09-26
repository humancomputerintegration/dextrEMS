#!/sr/bin/python
# Filename: continuous.py
import singlepulse
import time

version = '0.1'

def continuous(channel,pulse_width,min_amp_val,max_amp_val,slope_decay,delay_val,repetitions,ems):
        min_val = min_amp_val
        max_val = max_amp_val
        slope = slope_decay
        delay = delay_val
        reps = repetitions
        for x in range(reps):
                if x > 0 and (min_val+x/slope) < max_val:
                        cmd1 = singlepulse.generate(1,200,min_val+x/slope)
                        #print min_val+x/slope
                elif (min_val+x/slope) >= max_val:
                        cmd1 = singlepulse.generate(1,200,max_val)
                        #print "maxed out"
                else: cmd1 = singlepulse.generate(1,200,min_val)
                ems.write(cmd1)
                time.sleep(delay)

# End of continuous.py
