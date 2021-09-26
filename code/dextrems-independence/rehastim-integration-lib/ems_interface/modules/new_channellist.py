#!/usr/bin/python
# Filename: channellist.py

import binascii
import struct

version = '0.1'

get_bin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)

#type of command
CHANNEL_INIT = 0
CHANNEL_UPDATE = 1
CHANNEL_STOP = 2
SINGLE_PULSE = 3

def stop():
	ident = CHANNEL_STOP
	binarized_cmd = get_bin(1,1) + get_bin(ident,2) + get_bin(0, 5)
        hex_command = (hex(int(binarized_cmd, 2)).replace("0x",''))
        #print(hex(int(binarized_cmd, 2)))
        return(binascii.unhexlify(hex_command))

def initialize(_n_factor,_channels,_channels_lf,_group_time,_main_time):
        print("new")
        ident = CHANNEL_INIT
	n_factor = _n_factor
	channels = _channels
	channels_lf = _channels_lf
	group_time = _group_time
	main_time = _main_time
	checksum = (n_factor +channels + channels_lf + group_time + main_time) % 8
	#print("checksum verify = " + str(checksum))

	#print("binary command: \n" + 
	#"\t" + get_bin(ident,2) +  "\t\t#ident\t\t"+ str(len(get_bin(ident,2))) + "\n" + 
	#"\t" + get_bin(checksum, 3) + "\t\t#checksum\t" + str(len(get_bin(checksum, 3))) + "\n" +  
	#"\t" + get_bin(n_factor,3) + "\t\t#channel_number\t" + str(len(get_bin(n_factor,3))) + "\n" +  
	#"\t" + get_bin(channels,8) + "\t\t#channel_number\t" + str(len(get_bin(channels,8))) + "\n" +  
	#"\t" + get_bin(channels_lf,8) + "\t\t#channel_number\t" + str(len(get_bin(channels_lf,8))) + "\n" +  
	#"\t" + get_bin(group_time,5) + "\t\t#channel_number\t" + str(len(get_bin(group_time,5))) + "\n" +  
	#"\t" + get_bin(main_time,11) + "\t\t#channel_number\t" + str(len(get_bin(main_time,11))) + "\n"  
	#) 
	binarized_cmd = get_bin(ident,2) + get_bin(checksum, 3) + get_bin(n_factor,3) + get_bin(channels,8) + get_bin(channels_lf,8) + get_bin(group_time,5) + get_bin(main_time,11)
	cmd_pointer = 0
	new_cmd_pointer = 0
	proper_cmd= ["0" for x in range(48)]

	for c in proper_cmd:
    		if new_cmd_pointer == 0: #add a 1
    			proper_cmd[new_cmd_pointer]="1"
    		elif new_cmd_pointer == (9-1) or new_cmd_pointer == (17-1) or new_cmd_pointer == (25-1) or new_cmd_pointer == (33-1) or new_cmd_pointer == (41-1): #add a 0 
    			proper_cmd[new_cmd_pointer]="0"
    		elif new_cmd_pointer == (29-1) or new_cmd_pointer == (30-1): #add a X
    			proper_cmd[new_cmd_pointer]="0"
    		else:
			proper_cmd[new_cmd_pointer]=binarized_cmd[cmd_pointer]
 			cmd_pointer+=1
    		new_cmd_pointer+=1
	proper_bin_command = ''.join(map(str,proper_cmd))
	#print(proper_bin_command)
	hex_command = (hex(int(proper_bin_command, 2)).replace("0x",''))
	print(hex(int(proper_bin_command, 2)))
	return(binascii.unhexlify(hex_command))
        #print(hex_command)
        #return(binascii.unhexlify("99294061101F"))


def update(_channels): #channels is a array with several [id,mode,pulse_width,amp] 's, one per channel to change
	ident = CHANNEL_UPDATE
        mode = _mode
        pulse_width = _pulse_width
        pulse_current = _pulse_current

	sum_mode = 0
        for each channel in _channels:
            

	for m in mode:
		#print m
		sum_mode+=m
	sum_pulse = 0
	for m in pulse_width:
		#print m
		sum_pulse+=m
	sum_current = 0
	for m in pulse_current:
		#print m
		sum_current+=m
        checksum = (sum_mode + sum_pulse + sum_current) % 32
        print("checksum verify = " + str(checksum))
 
        #print("binary header command: \n" +
        #"\t" + get_bin(ident,2) +  "\t\t#ident\t\t"+ str(len(get_bin(ident,2))) + "\n" +
        #"\t" + get_bin(checksum, 5) + "\t\t#checksum\t" + str(len(get_bin(checksum, 5)))
 	#)
 	#form first the 8 header
        header_cmd = get_bin(1,0) + get_bin(ident,2) + get_bin(checksum, 5) 
 	binarized_cmd = []	
 
 	for c in range(0,channel_number):
		#print(pulse_width[c])
		#print(pulse_current[c])
		#print(mode[c])
 		#print("binary channel update: \n" + 
         	#"\t" + get_bin(pulse_width[c],9) + "\t#pulse_width\t" + str(len(get_bin(pulse_width[c],9))) + "\n" +
         	#"\t" + get_bin(pulse_current[c],7) + "\t\t#pulse_current\t" + str(len(get_bin(pulse_current[c],7))) + "\n"
         	#)
         	temp_cmd=(get_bin(0,1) +  get_bin(mode[c],2) + get_bin(0,3) +  get_bin(pulse_width[c],9) + get_bin(pulse_current[c],7))
       
 		cmd_pointer = 0
         	new_cmd_pointer = 0
 
         	proper_cmd= ["0" for x in range(24)]
 
         	for c in proper_cmd:
                 	#if new_cmd_pointer == 0: #add a 1
                        #		proper_cmd[new_cmd_pointer]="1"
                 	if new_cmd_pointer == (9-1) or new_cmd_pointer == (17-1): #add a 0
                         	proper_cmd[new_cmd_pointer]="0"
                 	#elif new_cmd_pointer == (4-1) or new_cmd_pointer == (5-1) or new_cmd_pointer == (6-1) : #add a X
                        # 	proper_cmd[new_cmd_pointer]="0"
                 	else:
                         	proper_cmd[new_cmd_pointer]=temp_cmd[cmd_pointer]
                         	cmd_pointer+=1
                 	new_cmd_pointer+=1
         	proper_bin_command = ''.join(map(str,proper_cmd))
         	#print(proper_bin_command)
         	#print(len(proper_bin_command))
		header_cmd+=proper_bin_command
         	#print(header_cmd)
         	#print(len(header_cmd))
		#print(hex(int(proper_bin_command, 2)))
		#format to triple hex
# 		#append these comands before exiting.
# 	full_cmd = header_cmd + proper_bin_command #this might be doing the wrong thing.. adding
        hex_command = (hex(int(header_cmd, 2)).replace("0x",''))
        print(hex_command)
	hex_command = hex_command.replace("L",'')
        print(hex_command)
        print(hex(int(header_cmd, 2)))
        print(len(header_cmd))
        return(binascii.unhexlify(hex_command))
        #return(binascii.unhexlify("bb006434414837222c4823105c"))

# End of channellist.py
