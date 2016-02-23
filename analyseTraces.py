import os
import sys
import optparse
import calc_utils as calc
import numpy as np
import matplotlib.pyplot as plt
import ROOT

def readPinFile(inFile):
    pinVal = 0 
    pinRMS = 0
    input = open(inFile,"r")
    for line in input:
        vals = line.split()
        pinVal = float(vals[0])
        pinRMS = float(vals[1])
        break
    return pinVal, pinRMS


def createTimeGapHisto(time_trace,pmt_traces,noise_traces):
    TimeGapVals = []
    for i in range(len(pmt_traces)):
        max_pmt_index = np.argmax(np.fabs(pmt_traces[i]))
        max_noise_index = np.argmax(np.fabs(noise_traces[i]))
        TimeGapVals.append(np.fabs(time_trace[max_pmt_index]-time_trace[max_noise_index]))
    timeGapHisto = ROOT.TH1D("TimeDifferencebetweennoiseandPMTPeak","TimeDifferencebetweennoiseandPMTPeak",20,np.amin(TimeGapVals)-1e-8,np.amax(TimeGapVals)+1e-8)
    for timeGapVal in TimeGapVals:
        print timeGapVal
        timeGapHisto.Fill(float(timeGapVal))
    return timeGapHisto

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    (options,args) = parser.parse_args()

    
    #Set passed TELLIE parameters
    box = int(options.box)
    channel = int(options.channel)

    pmt_dir = os.path.dirname("pmt_response/Box_%02d/Channel_%02d/" % (box,channel))
    pin_dir = os.path.dirname("pin_response/Box_%02d/Channel_%02d/" % (box,channel))
    noise_dir = os.path.dirname("driver_noise/Box_%02d/Channel_%02d/" % (box,channel))
    #Array to store x Values 
    time_trace = []
    got_time_trace = False
    #Arrays    
    pmt_traces = []
    pin_vals = []
    pin_rms = []
    noise_traces = []

    for pmt_file in os.listdir(pmt_dir):
        x1,y1 = calc.readPickleChannel(os.path.join(pmt_dir,pmt_file), 1,False)
	if not got_time_trace:
	    time_trace = x1

        pmt_traces.append(np.mean(y1,0))

    for noise_file in os.listdir(noise_dir):
        x1,y1 = calc.readPickleChannel(os.path.join(noise_dir,noise_file), 1,False)
        noise_traces.append(np.mean(y1,0))
    
    for pin_file in os.listdir(pin_dir):
        pin,rms = readPinFile(os.path.join(pin_dir,pin_file))
        pin_vals.append(pin)
        pin_rms.append(rms)
       
    outRoot = ROOT.TFile("driver_noiseBox_%02d_Chan_%02d.root" %(box,channel),"RECREATE") 
    
    pinHisto = ROOT.TH1I("PinValues","PinValues",int(np.amax(pin_vals)-np.amin(pin_vals)),np.amin(pin_vals),np.amax(pin_vals))
    for pinVal in pin_vals:
        pinHisto.Fill(pinVal)
    
    pinHisto.Write()

    pinRMSHisto = ROOT.TH1I("PinRMSValues","PinRMSValues",int(np.amax(pin_rms)-np.amin(pin_rms)),np.amin(pin_rms),np.amax(pin_rms))
    for pinRMS in pin_rms:
        pinRMSHisto.Fill(pinRMS)

    pinRMSHisto.Write()

    timeGapHisto = createTimeGapHisto(time_trace,pmt_traces,noise_traces)
    
    timeGapHisto.Write()

    outRoot.Close()

   
