###################################################
# Live plots of PIN readings and photon counts

# Author: Mark Stringer <ms711@sussex.ac.uk>
# Date: 29/03/16
###################################################
from core import serial_command
import optparse
import sys
import os
import time
import numpy as np
import calc_utils as calc
import matplotlib.pyplot as plt
import scopes
import scope_connections
import sweep_noise


pinValues = []
pinErrors = []
readings = []
photonCount  = []
photonCountError  = []
startTime = 0
timestamp = 0
pulseTimes = []
chan = 0
width = 0
pulse_number = 0 
pulse_delay = 0.1
num_traces = 40

def safe_exit(sc,e, fname):
    print "Exit safely"
    print e
    print timestamp
    plt.figure(0)
    plt.savefig(sweep_noise.check_dir("liveProbePlots/%s/Pin_Photons_Sub_%s.png"%(fname, timestamp)))
    plt.figure(1)
    plt.savefig(sweep_noise.check_dir("liveProbePlots/%s/PinVSPhoton_%s.png"%(fname, timestamp)))
    sc.stop()
    pin_dict, rms_dict, this_channel = sc.read_pin(chan)
 
    
    
    outputFile.close() 
    print pin_dict
    print rms_dict

def get_photons(volts_seconds,applied_volts):
    """Use the integral (Vs) from the scope to get the number of photons.
    Can accept -ve or +ve pulse
    """
    impedence = 50.0 
    eV = (6.626e-34 * 3e8) / (500e-9)
    qe = 0.192 # @ 501nm
    gain = get_gain(applied_volts)
    photons = np.fabs(volts_seconds) / (impedence * eV * gain * qe)
    return photons

def get_gain(applied_volts):
    """Get the gain from the applied voltage.
       Constants taken from pmt gain calibration
       taken July 2015 at site.
       See smb://researchvols.uscs.susx.ac.uk/research/neutrino_lab/SnoPlus/PmtCal.
    """
    a, b, c = 2.432, 12.86, -237.5
    #a, b, c = 545.1, 13.65, 0
    gain = a*np.exp(b*applied_volts) + c
    return gain


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-w",dest="width",default=0,help="IPW setting (0-16383)")
    parser.add_option("-f",dest="fileName",default="test",help="SaveName for plots")
    (options,args) = parser.parse_args()


    #run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)
    ###########################################
    scope_channels = 1 # We're using channel 1 and 3 (1 for PMT 3 for probe point and 2 for the trigger signal)!
    termination = 50 # Ohms
    trigger_level = -0.01 # 
    falling_edge = True
    y_div_units = 0.01 # volts
    x_div_units = 4e-9 # seconds
    x_offset = +2*x_div_units # offset in x (2 divisions to the left)
    record_length = 1e3 # trace is 100e3 samples long
    half_length = record_length / 2 # For selecting region about trigger point
    ###########################################
    scope.unlock()
    scope.set_horizontal_scale(x_div_units)
    scope.set_sample_rate(2.5e9)
    scope.set_horizontal_delay(x_offset) #shift to the left 2 units
    scope.set_single_acquisition() # Single signal acquisition mode
    scope.set_record_length(record_length)
    scope.set_active_channel(1)
    scope.set_data_mode(half_length-25, half_length+50)
    scope.set_edge_trigger(trigger_level, 1 , falling=falling_edge) 
    y_offset = -2.5*y_div_units
    scope.set_channel_y(1, y_div_units, pos=2.5)
    scope.set_display_y(1, y_div_units, offset=y_offset)
    scope.set_channel_termination(1, termination)
    scope.lock()
    scope.begin() # Acquires the pre-amble! 



    os.system("rm ./tempTraces.pkl")


    width = int(options.width)
    channel = (int(options.box)-1)*8 + int(options.channel)
    chan = channel
    width = int(options.width)
    pulse_number = 5000
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTE3C0PG")
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(0.1)
    sc.set_trigger_delay(0)
    sc.set_fibre_delay(0)
    #sc.set_pulse_delay(25e-3) 
    sc.set_pulse_number(pulse_number)
    pinValues.append(0)
    pinErrors.append(0)
    readings.append(0)
    photonCount.append(0)
    photonCountError.append(0)
    plt.ion()
    plt.figure(0)
    plt.subplot(211)
    plt.errorbar(readings,pinValues,yerr=pinErrors)
    plt.ylabel("PIN Reading")
    plt.subplot(212)
    plt.errorbar(readings,photonCount,yerr=photonCountError)
    plt.xlabel("Reading")
    plt.ylabel("Photon Count")
    plt.show(block=False)
    plt.figure(1)
    plt.errorbar(pinValues,photonCount,xerr=pinErrors,yerr=photonCountError)
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    plt.show(block=False)
    counter = 0
    startTime  = time.time()
    timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
    outputFile = open(sweep_noise.check_dir("liveProbePlots/%s/DATA_%s.dat"%(options.fileName, timestamp)),"w")
    #Now writing data file header
    outputFile.write("Channel: %02d     Frequency: %f IPW: %d NPulses: %d NTraces: %d\n" % (chan,1.0/pulse_delay,width,pulse_number,num_traces))
    outputFile.write("Reading #  Time since start (seconds)  PIN Value  Pin Error  Photon Count  Photon Count Error\n")
    print "WROTE HEADER"
    try: 
        while True:
            print "Event no: %i" % counter
            if counter != 0:
                pulseTimes.append(time.time()-startTime)
            sc.fire_sequence()
            save_ck0 = sweep_noise.save_scopeTraces("./tempTraces", scope, 1, num_traces)
                
	    #sleeping for 5 seconds to ensure TELLIE has stopped pulsing
            sleep_time = ((0.1/1e3)*pulse_number)+0.05
            time.sleep(sleep_time+3)
            pin = None
	    # while not comms_flags.valid_pin(pin,channel):
	    while pin==None:
		pin,rms,chans = sc.tmp_read_rms()
                x1,y1 = calc.readPickleChannel("./tempTraces.pkl", 1,True)
                num_photons_average_rms =  get_photons(calc.calcArea(x1,y1),0.7)
                
                print "LEN Y1: "+str(len(y1))
                if counter != 0:
                    photonCount.append(num_photons_average_rms[0])
                    photonCountError.append(num_photons_average_rms[1]/np.sqrt(len(y1)))
                os.system("rm ./tempTraces.pkl")
                print "\n====================================="
                print "%1.1f +/- %1.3f" % (float(pin[channel]), float(rms[channel])/np.sqrt(pulse_number))
                if counter != 0:
			pinValues.append(float(pin[channel]))
			pinErrors.append(float(rms[channel])/np.sqrt(pulse_number))
			readings = range(1,len(pinValues[1:])+1)
			plt.figure(0)
			plt.clf()
			sub = plt.subplot(211)
			plt.errorbar(readings,pinValues[1:],yerr=pinErrors[1:])
			plt.ylabel("PIN Reading")
			plt.subplot(212)
			plt.errorbar(readings,photonCount[1:],yerr=photonCountError[1:])
			plt.xlabel("Reading")
			plt.ylabel("Photon Count")
			plt.draw()
			plt.figure(1)
			plt.clf()
			plt.errorbar(pinValues[1:],photonCount[1:],xerr=pinErrors[1:],yerr=photonCountError[1:],fmt="",linestyle="")
			plt.xlabel("PIN Reading")
			plt.ylabel("Photon Count")
			plt.draw()
	                outputFile.write("%d %f %f %f %f %f\n" %(readings[-1],pulseTimes[-1],pinValues[-1],pinErrors[-1],photonCount[-1],photonCountError[-1]))
                        outputFile.flush()
                        os.fsync(outputFile)

			plt.pause(0.001)
            counter = counter + 1
    except Exception,e:
        print e
        safe_exit(sc, e, options.fileName)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt", options.fileName)
        
        
