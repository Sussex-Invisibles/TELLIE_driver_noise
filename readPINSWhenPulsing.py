###################################################
# Live plots of PIN readings and photon counts also plots 

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
import ROOT


pinValues = []
pinErrors = []
readings = []
photonCount  = []
photonCountError  = []
singleTracePhotonCounts = []
pmtTime = [] #Gap between time pmt crosses 10% of max value and trigger signal in (ns)
pmtTimeErr = []
startTime = 0
timestamp = 0
pulseTimes = []
chan = 0
width = 0
pulse_number = 0 
pulse_delay = 1 #In ms
num_traces = 40

#Method to calculate the area of all the traces
def calcAreaArray(x,y):
    """Calc area of pulses"""
    trapz = np.zeros( len(y[:,0]) )
    for i in range(len(y[:,0])):
        trapz[i] = np.trapz(y[i,:],x)
    return trapz

def get_pmt_time_and_spread(x1,y1,pulse_thresh=-5e-3):
     pmt_times = []
     for i in range(len(y1)):
	 if np.min(y1[i]) < pulse_thresh:
            pmt_times.append(calc.interpolate_threshold(x1,y1[i],pulse_thresh,rise=False))
     pmt_time_avg = np.mean(pmt_times)
     pmt_time_err = np.std(pmt_times)/np.sqrt(len(pmt_times))
     return pmt_time_avg*1.0e9, pmt_time_err*1.0e9

def safe_exit(sc,e, fname):
    print "Exit safely"
    print e
    print timestamp
    plt.figure(0)
    plt.savefig(sweep_noise.check_dir("liveProbePlots/%s/Pin_Photons_Sub_Chan_%d_%s.png"%(fname,chan,timestamp)))
    plt.figure(1)
    plt.savefig(sweep_noise.check_dir("liveProbePlots/%s/PinVSPhoton_Chan_%d_%s.png"%(fname, chan,timestamp)))
    plt.figure(4)
    plt.savefig(sweep_noise.check_dir("liveProbePlots/%s/TriggerPulseOffset_Chan_%d_%s.png"%(fname, chan,timestamp)))
    #Write out hit histo to root file
    outROOTFile = ROOT.TFile(sweep_noise.check_dir("liveProbePlots/%s/SinglePhotonCountHisto_%d_%s.root"%(fname, chan,timestamp)),"recreate")
    outHisto = ROOT.TH1I("Single_Pulse_Photon_Counts","Single Pulse Photon Counts",int(np.max(singleTracePhotonCounts)-np.min(singleTracePhotonCounts)+40),float(np.min(singleTracePhotonCounts)-20),float(np.max(singleTracePhotonCounts)+20))
    for singlePhotonCount in singleTracePhotonCounts:
	outHisto.Fill(singlePhotonCount)
    outHisto.Write()
    outROOTFile.Close()
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
    eV = 1.61e-19
    qe = 0.192 # @ 501nm
    gain = get_gain(applied_volts)
    photons = np.fabs(volts_seconds) /(impedence * eV * gain * qe)
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
    scope_channels = [1,2] # We're using channel 1 and 3 (1 for PMT 3 for probe point and 2 for the trigger signal)!
    termination = [50,50] # Ohms
    trigger_level = 1.0# 
    falling_edge = False
    y_div_units = [0.01,1.0] # volts
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
    scope.set_active_channel(2)
    scope.set_data_mode(half_length, half_length+900)
    scope.set_edge_trigger(trigger_level, 2 , falling=False) # Rising edge trigger 
    y_offset = [-2.5*y_div_units[0],2.5*y_div_units[1]]
    for i in range(len(scope_channels)):
	    scope.set_channel_y(scope_channels[i], y_div_units[i], pos=2.5)
	    scope.set_display_y(scope_channels[i], y_div_units[i], offset=y_offset[i])
	    #scope.set_display_y(scope_chan, y_div_units, offset=y_offset)
	    scope.set_channel_termination(scope_channels[i], termination[i])
    scope.lock()
    scope.begin() # Acquires the pre-amble! 



    os.system("rm ./tempTraces.pkl")


    width = int(options.width)
    channel = (int(options.box)-1)*8 + int(options.channel)
    chan = channel
    width = int(options.width)
    pulse_number = 500
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTE3C0PG")
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(pulse_delay)
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
    outputFile.write("Channel: %02d     Frequency: %f IPW: %d NPulses: %d NTraces: %d\n" % (chan,1.0/(pulse_delay*1e3),width,pulse_number,num_traces))
    outputFile.write("Reading #  Time since start (seconds)  PIN Value  Pin Error  Photon Count  Photon Count Error PMT Time (ns), PMT Time Err (ns)\n")
    print "WROTE HEADER"
    try: 
        while True:
            print "Event no: %i" % counter
            if counter != 0:
                pulseTimes.append(time.time()-startTime)
            sc.fire_sequence()
            save_ck0 = sweep_noise.save_scopeTraces("./tempTraces", scope, 1, num_traces)
                
	    #sleeping for 5 seconds to ensure TELLIE has stopped pulsing
            sleep_time = ((pulse_delay*1e-3)*pulse_number)+0.05
            time.sleep(sleep_time+3)
            pin = None
	    # while not comms_flags.valid_pin(pin,channel):
	    while pin==None:
		pin,rms,chans = sc.tmp_read_rms()
                x1,y1 = calc.readPickleChannel("./tempTraces.pkl", 1,True)
                num_photons_average_rms =  get_photons(calc.calcArea(x1,y1),0.7)
		singleTraceAreas = calcAreaArray(x1,y1)
	        singlePMTTime, singlePMTTimeErr = get_pmt_time_and_spread(x1,y1)
                print "LEN Y1: "+str(len(y1))
                if counter != 0:
                    photonCount.append(num_photons_average_rms[0])
                    photonCountError.append(num_photons_average_rms[1]/np.sqrt(len(y1)))
		    pmtTime.append(singlePMTTime)
	            pmtTimeErr.append(singlePMTTimeErr)
                    for singleArea in singleTraceAreas:
		    	singleTracePhotonCounts.append(get_photons(singleArea,0.7))
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
			plt.figure(3)
			plt.clf()
			plt.plot(np.add(np.multiply(x1,1e9),x_offset),np.mean(y1,axis=0))
			plt.xlabel("Time (ns)")
			plt.ylabel("volts")
			plt.draw()
			plt.figure(4)
			plt.clf()
			plt.errorbar(readings,pmtTime,yerr=pmtTimeErr)
			plt.xlabel("Reading")
			plt.ylabel("PMT Time (ns)")
			plt.draw()
	                outputFile.write("%d %f %f %f %f %f %f %f\n" %(readings[-1],pulseTimes[-1],pinValues[-1],pinErrors[-1],photonCount[-1],photonCountError[-1],pmtTime[-1],pmtTimeErr[-1]))
                        outputFile.flush()
                        os.fsync(outputFile)

			plt.pause(0.001)
            counter = counter + 1
    except Exception,e:
        print e
        safe_exit(sc, e, options.fileName)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt", options.fileName)
        
        
