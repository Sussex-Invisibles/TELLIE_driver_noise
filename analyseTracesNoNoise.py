import os
import sys
import optparse
import calc_utils as calc
import numpy as np
import matplotlib.pyplot as plt
import ROOT

def check_dir(dname):
    """Check if directory exists, create it if it doesn't"""
    direc = os.path.dirname(dname)
    if not os.path.exists(direc):
        print os.makedirs(direc)
        print "Made directory %s...." % dname
    return dname    

def get_photons(volts_seconds,applied_volts):
    """Use the integral (Vs) from the scope to get the number of photons.
    Can accept -ve or +ve pulse
    """
    impedence = 50.0 
    eV = 1.61e-19
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
    npulses = 0
    pinVal = 0 
    pinRMS = 0
    input = open(inFile,"r")
    for line in input:
        vals = line.split()
        npulses = float(vals[0])
        pinVal = float(vals[1])
        pinRMS = float(vals[2])
        break
    return npulses, pinVal, pinRMS

def calcPeakRisePoint(x,y,thresh):
    max_index = np.argmin(y)
    max_val = np.fabs(y[max_index])
    for i in range(max_index,0,-1):
        if np.fabs(y[i]) < max_val*thresh:

           return x[i]

def getNegThresholdCrossing(x,y,thresh):
    for i in range(len(y)):
        if y[i] < thresh:
           return x[i]

def getPosThresholdCrossing(x,y,thresh):
    for i in range(len(y)):
        if y[i] > thresh:
           return x[i]

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-i",dest="ipw",help="IPW Value you want to make plots for",default=-1000)
    parser.add_option("-d",dest="root_dir",help="root directory to output files to and read data files from")
    (options,args) = parser.parse_args()

    
    #Set passed TELLIE parameters
    box = int(options.box)
    channel = int(options.channel)
    width = int(options.ipw)
    root_dir = str(options.root_dir)

    pmt_dir = os.path.dirname(root_dir+"/pmt_response/Box_%02d/Channel_%02d/" % (box,channel))
    pin_dir = os.path.dirname(root_dir+"/pin_response/Box_%02d/Channel_%02d/" % (box,channel))
    #Array to store x Values 
    time_trace = []
    got_time_trace = False
    #Arrays    
    pmt_traces = []
    pin_vals = []
    pin_rms = []
    npulses = []
    
    for pmt_file in os.listdir(pmt_dir):
        x1 = None
        y1 = None
        if width != -1000:
            if int(pmt_file[-9:-4]) != width:
               continue
        try:
            x1,y1 = calc.readPickleChannel(os.path.join(pmt_dir,pmt_file), 1,False)
        except:
            continue
	if not got_time_trace:
	    time_trace = x1
        for i in range(len(y1)):
            pmt_traces.append(y1[i])
    
    for pin_file in os.listdir(pin_dir):
        if width != -1000:
            if int(pin_file[-9:-4]) != width:
               continue
       
        print pin_file
        numPulses,pin,rms = readPinFile(os.path.join(pin_dir,pin_file))
        pin_vals.append(pin)
        pin_rms.append(rms)
        npulses.append(numPulses)
    
     
    
    
    check_dir(root_dir+"/root_files/Box%02d"%(box))
    check_dir(root_dir+"/root_files/Box_%02d/Channel_%02d/"%(box,channel))
    outRoot = 0 
    if width == -1000:
        outRoot = ROOT.TFile(root_dir+"/root_files/Box_%02d/Channel_%02d/histos.root" %(box,channel),"RECREATE") 
    else:
        outRoot = ROOT.TFile(root_dir+"/root_files/Box_%02d/Channel_%02d/histosWidth%05d.root" %(box,channel,width),"RECREATE") 
   

    pinHisto = ROOT.TH1D("PinValues","PinValues",int(np.amax(pin_vals)-np.amin(pin_vals))+4,np.amin(pin_vals)-1,np.amax(pin_vals)+1)
    for pinVal in pin_vals:
        pinHisto.Fill(pinVal)
    
    pinHisto.Write()

    pinRMSHisto = ROOT.TH1D("PinRMSValues","PinRMSValues",int(np.amax(pin_rms)-np.amin(pin_rms))+10,np.amin(pin_rms)-1,np.amax(pin_rms)+1)
    for pinRMS in pin_rms:
        pinRMSHisto.Fill(pinRMS)
    
    #Getting photon count from area under peak
    photonCountsAverage  = []
    numReadings = []
    photonCounts = []
    photonRMS = []
    for pmt_file in os.listdir(pmt_dir):
        if width != -1000:
            if int(pmt_file[-9:-4]) != width:
               continue
        x1 = None
        y1 = None
        try:
            x1,y1 = calc.readPickleChannel(os.path.join(pmt_dir,pmt_file), 1,True)
        except:
            continue
        for i in range(len(y1)):
            photonCounts.append(get_photons(calcAreaSingle(x1,y1[i]),0.7))
        
        numReadings.append(len(y1))
        num_photons_average_rms =  get_photons(calc.calcArea(x1,y1),0.7)
        photonCountsAverage.append(num_photons_average_rms[0])
        photonRMS.append(num_photons_average_rms[1])
    
    photonHistoAverage = ROOT.TH1D("PhotonCountAverage","PhotonCountAverage",20,np.amin(photonCountsAverage)-10,np.amax(photonCountsAverage)+10)
    photonHistoSingle = ROOT.TH1D("PhotonCountSingle","PhotonCountSingle",100,np.amin(photonCounts)-10,np.amax(photonCounts)+10)
    photonHistoRMS = ROOT.TH1D("PhotonCountRMS","PhotonCountRMS",20,np.amin(photonRMS)-10,np.amax(photonRMS)+10)
    
   
    print "LEN of photonCounts: "+str(len(photonCounts)) 
    for photonSingleVal in photonCounts:
        photonHistoSingle.Fill(photonSingleVal) 

    for photonVal in photonCountsAverage:
       photonHistoAverage.Fill(photonVal)
    
    for photonRMSVal in photonRMS:
       photonHistoRMS.Fill(photonRMSVal)

    pinRMSHisto.Write()

    
    photonHistoSingle.Write()
    
    photonHistoAverage.Write()
   
    photonHistoRMS.Write()
   
    outRoot.Close()
    plt.figure(0)
    plt.errorbar(pin_vals,photonCountsAverage,yerr=np.divide(photonRMS,np.sqrt(numReadings)),xerr=np.divide(pin_rms,np.sqrt(npulses)),linestyle="",fmt="")
    plt.scatter(pin_vals,photonCountsAverage,s=10*range(1,(len(pin_vals))+1))
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/PhotonVsPin.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/PhotonVsPinWidth%05d.png"%(box,channel,width))
    readingsCount = range(1,len(photonCountsAverage)+1)
    plt.figure(6)
    plt.xlabel("Reading Number")
    sub = plt.subplot(2,1,1)
    sub.set_ylabel("Photon Count")
    plt.errorbar(readingsCount,photonCountsAverage,yerr=np.divide(photonRMS,np.sqrt(numReadings)),linestyle="")
    sub = plt.subplot(2,1,2)
    sub.yaxis.tick_right()
    sub.set_ylabel("PIN Reading")
    plt.errorbar(readingsCount,pin_vals,yerr=np.divide(pin_rms,np.sqrt(npulses)),linestyle="")
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/readingResults.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/readingResultsWidth%05d.png"%(box,channel,width))

