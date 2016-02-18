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
import sweep
import scopes
import scope_connections
import utils


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-i",dest="ipw",help="IPW value to run at")
    parser.add_option("-n",dest=pulse_number,help="Number of pulses to run over")
    (options,args) = parser.parse_args()

    #Time
    total_time = time.time()
    
    #Set passed TELLIE parameters
    box = int(options.box)
    channel = int(options.channel)
    ipw = int(options.ipw)
    pulse_number = int(options.pulse_number)

    #Fixed parameters
    delay = 1.0 # 1ms -> kHz
    
    fibre_delay =  0
    trigger_delay = 0

    # Set up serial connection
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTE3C0PG")
    
    logical_channel = (box-1)*8 + channel
    
    sc.select_channel(logical_channel)
    sc.set_pulse_width(ipw)
    sc.set_pulse_height(16383)
    sc.set_pulse_number(pulse_number)
    sc.set_pulse_delay(delay)
    sc.set_fibre_delay(fibre_delay)
    sc.set_trigger_delay(trigger_delay)

    #run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)
    ###########################################
    scope_channels = [1,3] # We're using channel 1 and 2 (1 for PMT 3 for probe point)!
    termination = [50,1e6] # Ohms
    trigger_level = 0.5 # half peak minimum
    falling_edge = True
    min_trigger = -0.004
    y_div_units = 1 # volts
    x_div_units = 4e-9 # seconds
    y_offset = -2.5*y_div_units # offset in y (2.5 divisions up)
    x_offset = +2*x_div_units # offset in x (2 divisions to the left)
    record_length = 1e3 # trace is 100e3 samples long
    half_length = record_length / 2 # For selecting region about trigger point
    ###########################################
    scope.unlock()
    scope.set_horizontal_scale(x_div_units)
    scope.set_horizontal_delay(x_offset) #shift to the left 2 units
    scope.set_single_acquisition() # Single signal acquisition mode
    scope.set_record_length(record_length)
    scope.set_data_mode(half_length-50, half_length+50)
    scope.set_edge_trigger(trigger, 1, True) # Rising edge trigger 
    
    for i in range(len(scope_channels)):
	    scope.set_channel_y(scope_channels[i], y_div_units[i], pos=2.5)
	    #scope.set_display_y(scope_chan, y_div_units, offset=y_offset)
	    scope.set_channel_termination(scope_channels[i], termination[i])
    scope.lock()
    scope.begin() # Acquires the pre-amble! 



    #Create a new, timestamped, summary file
    sweep.check_dir('./driver_noise')
    sweep.check_dir("./pmt_response")
    sweep.check_dir("./pin_response")
    saveDirNoise = sweep.check_dir("./driver_noise/Box_%02d/" % (box))
    saveDirPMTResponse = sweep.check_dir("./driver_noise/Box_%02d/" % (box))
    saveDirPINResponse = sweep.check_dir("./driver_noise/Box_%02d/" % (box))
    #Run 1KHz for 10 mins save 100 traces at intervals of 30 secs extract PIN response
    timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
    output_dirname_noise = "%s/Chan%02d__%s" % (saveDirNoise,channel,timestamp)
    output_dirname_pmt = "%s/Chan%02d__%s" % (saveDirPMTResponse,channel,timestamp)
    output_dirname_pin = "%s/Chan%02d__%s" % (saveDirPINResponse,channel,timestamp)
   
