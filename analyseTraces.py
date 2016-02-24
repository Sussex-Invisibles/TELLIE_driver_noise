import os
import sys
import optparse
import calc_utils as calc
import numpy as np
import matplotlib.pyplot as plt
import ROOT

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

def calcAreaSingle(x,y):
    """Calc area of pulses"""
    area  = np.trapz(y,x)
    return area

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
    timeGapHisto = ROOT.TH1D("TimeDifferencebetweennoiseandPMTPeak","TimeDifferencebetweennoiseandPMTPeak",100,(np.amin(TimeGapVals)-1e-8)*1e9,(np.amax(TimeGapVals)+1e-8)*1e9)
    for timeGapVal in TimeGapVals:
        timeGapHisto.Fill(float(timeGapVal)*1e9)
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
        x1 = None
        y1 = None
        try:
            x1,y1 = calc.readPickleChannel(os.path.join(pmt_dir,pmt_file), 1,False)
        except:
            continue
	if not got_time_trace:
	    time_trace = x1
        for i in range(len(y1)):
            pmt_traces.append(y1[i])

    for noise_file in os.listdir(noise_dir):
        x1 = None
        y1 = None
        try:
            x1,y1 = calc.readPickleChannel(os.path.join(pmt_dir,pmt_file), 1,False)
        except:
            continue
        for i in range(len(y1)):
            noise_traces.append(y1[i])
    
    for pin_file in os.listdir(pin_dir):
        pin,rms = readPinFile(os.path.join(pin_dir,pin_file))
        pin_vals.append(pin)
        pin_rms.append(rms)
       
    outRoot = ROOT.TFile("root_files/driver_noiseBox_%02d_Chan_%02d.root" %(box,channel),"RECREATE") 
    
    pinHisto = ROOT.TH1D("PinValues","PinValues",int(np.amax(pin_vals)-np.amin(pin_vals))+4,np.amin(pin_vals)-1,np.amax(pin_vals)+1)
    for pinVal in pin_vals:
        pinHisto.Fill(pinVal)
    
    pinHisto.Write()

    pinRMSHisto = ROOT.TH1D("PinRMSValues","PinRMSValues",int(np.amax(pin_rms)-np.amin(pin_rms))+10,np.amin(pin_rms)-1,np.amax(pin_rms)+1)
    for pinRMS in pin_rms:
        pinRMSHisto.Fill(pinRMS)
    
    #Getting photon count from area under peak
    photonCountsAverage  = []
    photonCounts = []
    photonRMS = []
    for pmt_file in os.listdir(pmt_dir):
        x1 = None
        y1 = None
        try:
            x1,y1 = calc.readPickleChannel(os.path.join(pmt_dir,pmt_file), 1,True)
        except:
            continue
        for i in range(len(y1)):
            photonCounts.append(get_photons(calcAreaSingle(x1,y1[i]),0.7))
        
        num_photons_average_rms =  get_photons(calc.calcArea(x1,y1),0.7)
        photonCountsAverage.append(num_photons_average_rms[0])
        photonRMS.append(num_photons_average_rms[1])
    
    photonHistoAverage = ROOT.TH1D("PhotonCountAverage","PhotonCountAverage",20,np.amin(photonCountsAverage)-10,np.amax(photonCountsAverage)+10)
    photonHistoSingle = ROOT.TH1D("PhotonCountSingle","PhotonCountSingle",100,np.amin(photonCounts)-10,np.amax(photonCounts)+10)
    photonHistoRMS = ROOT.TH1D("PhotonCountRMS","PhotonCountRMS",20,np.amin(photonRMS)-10,np.amax(photonRMS)+10)
   
    for photonSingleVal in photonCounts:
        photonHistoSingle.Fill(photonSingleVal) 

    for photonVal in photonCountsAverage:
       photonHistoAverage.Fill(photonVal)
    
    for photonRMSVal in photonRMS:
       photonHistoRMS.Fill(photonRMSVal)

    pinRMSHisto.Write()

    timeGapHisto = createTimeGapHisto(time_trace,pmt_traces,noise_traces)
    
    timeGapHisto.Write()

    photonHistoSingle.Write()
    
    photonHistoAverage.Write()
   
    photonHistoRMS.Write()

    outRoot.Close()
    
     
    plt.figure(0)
    plt.errorbar(pin_vals,photonCountsAverage,yerr=photonRMS,linestyle="",fmt="o")
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    plt.show()
   
