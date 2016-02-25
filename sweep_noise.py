#!/usr/bin/env python
#########################
# sweep_noise.py
#  Generic module for running
# IPW sweeps with Tek scope
# modified to collect a fixed number of traces using scope
#
#########################
import os
from core import serial_command
from common import comms_flags
import math
import time
#try:
import utils
#except:
#    pass
import sys
import calc_utils as calc
import numpy as np

port_name = "/dev/tty.usbserial-FTE3C0PG"
#port_name = "/dev/tty.usbserial-FTGA2OCZ"
## TODO: better way of getting the scope type
scope_name = "Tektronix3000"
_boundary = [0,1.5e-3,3e-3,7e-3,15e-3,30e-3,70e-3,150e-3,300e-3,700e-3,1000]
_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0]
_v_div_1 = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,2.0]
#_v_div = [20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1] # For scope at sussex
#_v_div_1 = [20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1, 2]

sc = None
sc = serial_command.SerialCommand(port_name)

#initialise sc here, faster options setting
def start():
    global sc
    sc = serial_command.SerialCommand(port_name)

def set_port(port):
    global port_name
    port_name = port

def set_scope(scope):
    global scope_name
    if scope=="Tektronix3000" or scope=="LeCroy":
        scope_name = scope
    else:
        raise Exception("Unknown scope")

def check_dir(dname):
    """Check if directory exists, create it if it doesn't"""
    direc = os.path.dirname(dname)
    if not os.path.exists(direc):
        print os.makedirs(direc)
        print "Made directory %s...." % dname
    return dname    

def return_zero_result():
    r = {}
    r['pin'] = 0
    r['width'], r['width error'] = 0, 0
    r['rise'], r['rise error'] = 0, 0
    r['fall'], r['fall error'] = 0, 0
    r['area'], r['area error'] = 0, 0
    r['peak'], r['peak error'] = 0, 0
    return r

def save_scopeTraces(fileName, scope, channel, noPulses):
    """Save a number of scope traces to file - uses compressed .pkl"""
    scope._get_preamble(channel)
    results = utils.PickleFile(fileName, 1)
    results.add_meta_data("timeform_1", scope.get_timeform(channel))

    #ct = scope.acquire_time_check()
    #if ct == False:
    #    print 'No triggers for this data point. Will skip and set data to 0.'
    #    results.save()
    #    results.close()
    #    return False

    t_start, loopStart = time.time(),time.time()
    for i in range(noPulses):
        try:
            ct = scope.acquire_time_check(timeout=.4)
            results.add_data(scope.get_waveform(channel), 1)
        except Exception, e:
            print "Scope died, acquisition lost."
            print e
        if i % 100 == 0 and i > 0:
            print "%d traces collected - This loop took : %1.1f s" % (i, time.time()-loopStart)
            loopStart = time.time()
    print "%d traces collected TOTAL - took : %1.1f s" % (i, (time.time()-t_start))
    results.save()
    results.close()
    return True

def save_scopeTraces_Multiple(fileNames, scope, channels, noPulses):
    """Save a number of scope traces to file - uses compressed .pkl"""
    results = []
    for i in range(len(fileNames)):
	    scope._get_preamble(channels[i])
	    results.append(utils.PickleFile(fileNames[i], 1))
	    results[i].add_meta_data("timeform_1", scope.get_timeform(channels[i]))

    #ct = scope.acquire_time_check()
    #if ct == False:
    #    print 'No triggers for this data point. Will skip and set data to 0.'
    #    results.save()
    #    results.close()
    #    return False

    t_start, loopStart = time.time(),time.time()
    for i in range(noPulses):
        try:
            ct = scope.acquire_time_check(timeout=.4)
            for j in range(len(results)):
		    results[j].add_data(scope.get_waveform(channels[j]), 1)
        except Exception, e:
            print "Scope died, acquisition lost."
            print e
        if i % 100 == 0 and i > 0:
            print "%d traces collected - This loop took : %1.1f s" % (i, time.time()-loopStart)
            loopStart = time.time()
    print "%d traces collected TOTAL - took : %1.1f s" % (i, (time.time()-t_start))
    for i in range(len(results)):
	    results[i].save()
	    results[i].close()
    return True


def find_and_set_scope_y_scale(channel,height,width,delay,scope,scaleGuess=None):
    """Finds best y_scaling for current pulses
    """
    func_time = time.time()
    sc.fire_continuous()
    time.sleep(0.1)
    
    # If no scale guess, try to find reasonable trigger crossings at each y_scale
    ct = False
    if scaleGuess==None:
        for i, val in enumerate(_v_div):
            scope.set_channel_y(channel,_v_div[-1*(i+1)], pos=3) # set scale, starting with largest
            scope.set_edge_trigger( (-1*_v_div[-1*(i+1)]), channel, falling=True)
            if i==0:
                time.sleep(1) # Need to wait to clear previous triggered state
            ct = scope.acquire_time_check(timeout=.5) # Wait for triggered acquisition
            if ct == True:
                break
    else: #Else use the guess
        if abs(scaleGuess) > 1:
            guess_v_div = _v_div
        else:
            tmp_idx = np.where( np.array(_v_div) >= abs(scaleGuess) )[0][0]
            guess_v_div = _v_div[0:tmp_idx]
        for i, val in enumerate(guess_v_div):
            scope.set_channel_y(channel,guess_v_div[-1*(i+1)],pos=3) # set scale, starting with largest
            scope.set_edge_trigger( (-1*guess_v_div[-1*(i+1)]), channel, falling=True)
            if i==0:
                time.sleep(0.2) # Need to wait to clear previous triggered state
            ct = scope.acquire_time_check() # Wait for triggered acquisition
            if ct == True:
                break

    time.sleep(0.5) # Need to wait for scope to recognise new settings
    scope._get_preamble(channel)
    # Calc min value
    mini, wave = np.zeros( 10 ), None    
    for i in range( len(mini) ):
        # Check we get a trigger - even at the lowest setting we might see nothing
        ct = scope.acquire_time_check(timeout=.4)
        if ct == False:
            print 'Triggers missed for this data point. Will skip and set data to 0.'
            return False
        wave = scope.get_waveform(channel)
        mini[i] = min(wave) - np.mean(wave[0:10])
    min_volt = np.mean(mini)
    print "MINIMUM MEASUREMENT:", min_volt
    if np.abs(min_volt) < 0.006:
        return False

    # Set scope
    if -1*(min_volt/6) > _v_div_1[-1]:
        scale = _v_div_1[-1]
    else: 
        scale_idx = np.where( np.array(_v_div_1) >= -1*(min_volt/6) )[0][0]
        scale = _v_div_1[scale_idx]
    # Because of baseline noise!
    if scale == 2e-3:
        trig = -7.5e-3
        #trig = -4e-3
    elif scale == 1e-3:
        trig = -7.5e-3
        #trig = -3e-3
    elif scale == 5e-3:
        trig = -7.5e-3
    else:
        trig = -1.*scale
    print "Preticted scale = %1.3fV, actual scale = %1.3fV, trigger @ %1.4fV" % (-1*(min_volt/6.6) , scale, trig)
    scope.set_channel_y( channel, scale, pos=3) # set scale, starting with largest
    scope.set_edge_trigger( trig, channel, falling=True)

    print "TOTAL FUNC TIME = %1.2f s" % (time.time() - func_time)
    sc.stop()
    return True
    
def sweep_noise(dirs_out,box,channel,width,delay,scope,min_volt=None):
    """Perform a measurement using a default number of
    pulses, with user defined width, channel and rate settings.
    """
    print '____________________________'
    print width

    #fixed options
    height = 16383    
    fibre_delay = 0
    trigger_delay = 0
    pulse_number = 11100
    #first select the correct channel and provide settings
    logical_channel = (box-1)*8 + channel
    
    sc.select_channel(logical_channel)
    sc.set_pulse_width(width)
    sc.set_pulse_height(16383)
    sc.set_pulse_number(pulse_number)
    sc.set_pulse_delay(delay)
    sc.set_fibre_delay(fibre_delay)
    sc.set_trigger_delay(trigger_delay)
    print "Set up TELLIE" 
    # first, run a single acquisition with a forced trigger, effectively to clear the waveform
    scope._connection.send("trigger:state ready")
    time.sleep(0.1)
    scope._connection.send("trigger force")
    time.sleep(0.1)
    print "Reset Scope"
    # File system stuff
    fname0 = "%sWidth%05d" % (dirs_out[0],width)
    fname1 = "%sWidth%05d" % (dirs_out[1],width)
    
    print "Set up Files" 
    # Check scope
    print "Saving raw pmt  files to: %s..." % fname0
    print "Saving raw probe  files to: %s..." % fname1
    sc.fire_sequence()
    print "Fired TELLIE"
    fileNames = [fname0,fname1]
    channels = [1,3]
    saved = save_scopeTraces_Multiple(fileNames,scope,channels,100)
    #save_ck0 = save_scopeTraces(fname0, scope, 1, 100)
    #save_ck1 = save_scopeTraces(fname1, scope, 3, 100)
    print "Saved scope traces"
    #sleeping for 5 seconds to ensure TELLIE has stopped pulsing
    time.sleep(5)
    pin = None
    # while not comms_flags.valid_pin(pin,channel):
    while pin==None:
        pin,rms,chans = sc.tmp_read_rms()
        print pin
        print chans
    return pulse_number,pin[logical_channel],rms[logical_channel]

