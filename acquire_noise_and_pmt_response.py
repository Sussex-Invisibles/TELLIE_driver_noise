#!/usr/bin/env python
###################################
# acquire_noise_and_pmt_response.py
#
#Runs several scans at a fixed ipw value saves the PMT response and the noise on the driver board also stores the pin response
#
# Note that the rate is fixed (1 kHz)
#
###################################

import os
import sys
import optparse
import time
import sweep_noise
import scopes
import scope_connections
import utils


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-i",dest="ipw",help="IPW value to run at")
    parser.add_option("-t",dest="nmins",help="Number of mins to run for")
    parser.add_option("-d",dest="root_dir",help="root directory to output files to")
    (options,args) = parser.parse_args()

    #Time
    total_time = time.time()
    
    #Set passed TELLIE parameters
    box = int(options.box)
    channel = int(options.channel)
    ipw = int(options.ipw)
    nmins = int(options.nmins)
    root_dir = str(options.root_dir)

    #Fixed parameters
    delay = 1.0 # 1ms -> kHz
    

    #run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)
    ###########################################
    scope_channels = [1,4,2] # We're using channel 1 and 3 (1 for PMT 3 for probe point and 2 for the trigger signal)!
    termination = [50,1e6,50] # Ohms
    trigger_level = 1.4 # 
    falling_edge = True
    y_div_units = [0.05,0.2,1.0] # volts
    x_div_units = 100e-9 # seconds
    x_offset = +2*x_div_units # offset in x (2 divisions to the left)
    record_length = 10e3 # trace is 100e3 samples long
    half_length = record_length / 2 # For selecting region about trigger point
    ###########################################
    scope.unlock()
    scope.set_horizontal_scale(x_div_units)
    scope.set_sample_rate(2.5e9)
    scope.set_horizontal_delay(x_offset) #shift to the left 2 units
    scope.set_single_acquisition() # Single signal acquisition mode
    scope.set_record_length(record_length)
    scope.set_active_channel(1)
    scope.set_active_channel(4)
    scope.set_active_channel(2)
    scope.set_data_mode(half_length-1500, half_length+900)
    scope.set_edge_trigger(trigger_level, 2 , falling=False) # Rising edge trigger 
    y_offset = [-2.5*y_div_units[0],0.05,0]
    
    for i in range(len(scope_channels)):
	    scope.set_channel_y(scope_channels[i], y_div_units[i], pos=2.5)
	    scope.set_display_y(scope_channels[i], y_div_units[i], offset=y_offset[i])
	    #scope.set_display_y(scope_chan, y_div_units, offset=y_offset)
	    scope.set_channel_termination(scope_channels[i], termination[i])
    scope.lock()
    scope.begin() # Acquires the pre-amble! 



    #Create a new, timestamped, summary file
    saveDirNoise = sweep_noise.check_dir(root_dir+'/driver_noise')
    saveDirPMTResponse = sweep_noise.check_dir(root_dir+"/pmt_response")
    saveDirPINResponse = sweep_noise.check_dir(root_dir+"/pin_response")

    saveDirNoise = sweep_noise.check_dir("%s/Box_%02d" % (saveDirNoise,box))
    saveDirPMTResponse =  sweep_noise.check_dir("%s/Box_%02d" % (saveDirPMTResponse,box))
    saveDirPINResponse = sweep_noise.check_dir("%s/Box_%02d" % (saveDirPINResponse,box))
    
    saveDirNoise = sweep_noise.check_dir("%s/Channel_%02d/" % (saveDirNoise,channel))
    saveDirPMTResponse = sweep_noise.check_dir("%s/Channel_%02d/" % (saveDirPMTResponse,channel))
    saveDirPINResponse = sweep_noise.check_dir("%s/Channel_%02d/" % (saveDirPINResponse,channel))

    #Run 1KHz for 10 mins save 100 traces at intervals of 30 secs extract PIN response
    start_time = time.time()
    run_time = 0
    saveDirs = ["",""]
    while run_time<60*nmins:
        run_time = time.time()-start_time
        #Reading every 30 secs
        if ((int(run_time))%30)==0:
            print run_time
	    timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
	    output_dirname_noise = ("%s/Time__%s" % (saveDirNoise,timestamp))
	    output_dirname_pmt = ("%s/Time__%s" % (saveDirPMTResponse,timestamp))
	    output_filename_pin = sweep_noise.check_dir("%s/Time__%sWidth%05d.dat" % (saveDirPINResponse,timestamp,ipw))
            saveDirs[0] = output_dirname_pmt
            saveDirs[1] = output_dirname_noise
            print saveDirs 
            print box
            print channel
	    print ipw
	    print delay
            print scope
            npulses,pin,rms = sweep_noise.sweep_noise(saveDirs,box,channel,ipw,delay,scope)
            pinFile = open(output_filename_pin,"w")
            pinFile.write("%s %s %s\n" % (npulses,pin,rms))
            pinFile.close()
            
            
   
