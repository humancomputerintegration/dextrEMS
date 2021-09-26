#!/sr/bin/python
# Filename: sweepdown.py
import singlepulse
import time

version = '0.1'

def sweepdown(channel,pulse_width,min_amp_val,max_amp_val,slope_decay,delay_val,repetitions,ems):
        min_val = min_amp_val
        max_val = max_amp_val
        slope = slope_decay
        delay = delay_val
        reps = repetitions
        for x in range(reps):
                if x > 0 and (max_val-x/slope) > min_val:
                        cmd1 = singlepulse.generate(1,200,max_val-x/slope)
                        print  max_val-x/slope
                elif (max_val-x/slope) <= min_val:
                        cmd1 = singlepulse.generate(1,200,min_val)
                        print "mined out at " min_val
                else: cmd1 = singlepulse.generate(1,200,max_val)
                ems.write(cmd1)
                time.sleep(delay)

# End of sweepdown.py
