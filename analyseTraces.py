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

def createTimeGapHisto(time_trace,pmt_traces,noise_traces,noise_threshold):
    TimeGapVals = []
    TimeGapValsInteresting = []
    noiseCrossIndex = []
    noiseCrossIndexInteresting = []
    for i in range(len(pmt_traces)):
        pmt_pulse_time = calcPeakRisePoint(time_trace,pmt_traces[i],0.2)*1e9
        #driver_noise_time = calc.interpolate_threshold(time_trace,np.fabs(noise_traces[i]),noise_threshold*np.amin(noise_traces[i]))*1e9
        #driver_noise_time = calcPeakRisePoint(time_trace,noise_traces[i],noise_threshold)*1e9
        driver_noise_time = getPosThresholdCrossing(time_trace,noise_traces[i],0.3)*1e9
         

        if not np.isfinite(driver_noise_time) or not np.isfinite(pmt_pulse_time):
            continue
        if (np.fabs(pmt_pulse_time-driver_noise_time))<0:
           TimeGapValsInteresting.append(np.fabs(pmt_pulse_time-driver_noise_time))
           for j in range(len(time_trace)):
               if time_trace[j]*1e9 > driver_noise_time:
	           noiseCrossIndexInteresting.append(j)
	           break
        else:
           TimeGapVals.append(np.fabs(pmt_pulse_time-driver_noise_time))
           for j in range(len(time_trace)):
               if time_trace[j]*1e9 > driver_noise_time:
	           noiseCrossIndex.append(j)
	           break
    timeGapHisto = ROOT.TH1D("TimeDifferencebetweennoiseandPMTPeak","TimeDifferencebetweennoiseandPMTPeak",50,(np.amin(TimeGapVals)-10),(np.amax(TimeGapVals)+10))
    if len(TimeGapValsInteresting)<1: 
        TimeGapValsInteresting = [10,90]
    timeGapHistoInteresting = ROOT.TH1D("TimeDifferencebetweennoiseandPMTPeakLessthan100nsGap","TimeDifferencebetweennoiseandPMTPeakLessthan100nsGap",50,(np.amin(TimeGapValsInteresting)-10),(np.amax(TimeGapValsInteresting)+10))
    for timeGapVal in TimeGapVals:
        timeGapHisto.Fill(float(timeGapVal))
    
    for timeGapValInteresting in TimeGapValsInteresting:
        timeGapHistoInteresting.Fill(float(timeGapValInteresting))
    
    plt.figure(1)
    plt.subplot(211)
    plt.ylabel("Ground Noise Voltage (V)")
    for i in range(len(noiseCrossIndex)):
        noise_trace = noise_traces[i]
        plt.plot(np.multiply(time_trace[noiseCrossIndex[i]-150:]-time_trace[noiseCrossIndex[i]-150],1e9),noise_trace[noiseCrossIndex[i]-150:],label="Trace: "+str(i))
    plt.subplot(212)
    for i in range(len(noiseCrossIndex)):
        pmt_trace = pmt_traces[i]
        plt.plot(np.multiply(time_trace[noiseCrossIndex[i]-150:]-time_trace[noiseCrossIndex[i]-150],1e9),pmt_trace[noiseCrossIndex[i]-150:],label="Trace: "+str(i))
    plt.ylabel("PMT Pulse")
    plt.xlabel("Time (ns)")
    plt.subplot(211)
    ax = plt.gca()
    ax.set_xticklabels([])
    
    plt.figure(2)
    plt.subplot(211)
    plt.ylabel("Ground Noise Voltage (V)")
    for i in range(len(noiseCrossIndexInteresting)):
        noise_trace = noise_traces[i]
        plt.plot(np.multiply(time_trace[noiseCrossIndexInteresting[i]-150:]-time_trace[noiseCrossIndexInteresting[i]-150],1e9),noise_trace[noiseCrossIndexInteresting[i]-150:],label="Trace: "+str(i))
    plt.subplot(212)
    for i in range(len(noiseCrossIndexInteresting)):
        pmt_trace = pmt_traces[i]
        plt.plot(np.multiply(time_trace[noiseCrossIndexInteresting[i]-150:]-time_trace[noiseCrossIndexInteresting[i]-150],1e9),pmt_trace[noiseCrossIndexInteresting[i]-150:],label="Trace: "+str(i))
    plt.ylabel("PMT Pulse")
    plt.xlabel("Time (ns)")
    plt.subplot(211)
    ax = plt.gca()
    ax.set_xticklabels([])
    

    plt.figure(3)
    plt.subplot(211)
    plt.ylabel("Ground Noise Voltage (V)")
    for i in range(len(noise_traces)):
        noise_trace = noise_traces[i]
        plt.plot(np.multiply(time_trace,1e9),noise_trace,label="Trace: "+str(i))
    plt.subplot(212)
    for i in range(len(pmt_traces)):
        pmt_trace = pmt_traces[i]
        plt.plot(np.multiply(time_trace,1e9),pmt_trace,label="Trace: "+str(i))
    plt.ylabel("PMT Pulse")
    plt.xlabel("Time (ns)")
    plt.subplot(211)
    ax = plt.gca()
    ax.set_xticklabels([])
    
    
    return timeGapHisto, timeGapHistoInteresting

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
    npulses = []
    
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
    posNoiseStack = ROOT.THStack("Positive Peak Noise Voltage","Positive Peak Noise Voltage")
    negNoiseStack = ROOT.THStack("Negative Peak Noise Voltage","Negative Peak Noise Voltage")
    colIter = 1
    posPeakNoiseTotal = []
    negPeakNoiseTotal = []
    for noise_file in os.listdir(noise_dir):
        x1 = None
        y1 = None
        posPeakNoise = []
        negPeakNoise = []
        try:
            x1,y1 = calc.readPickleChannel(os.path.join(noise_dir,noise_file), 1,False)
        except:
            continue
        for i in range(len(y1)):
            noise_traces.append(y1[i])
            posPeakNoise.append(np.amax(y1))
            negPeakNoise.append(np.amin(y1))
            posPeakNoiseTotal.append(np.amax(y1))
            negPeakNoiseTotal.append(np.amin(y1))
        posNoiseHisto = ROOT.TH1D("Positive Peak Noise"+str(colIter),"Positive Peak Noise"+str(colIter),25,0.56,0.63)
        negNoiseHisto = ROOT.TH1D("Negative Peak Noise"+str(colIter),"Negative Peak Noise"+str(colIter),25,-0.63,0.56)
        posNoiseHisto.SetFillColor(colIter)
        negNoiseHisto.SetFillColor(colIter)
        colIter+= 1
        for entry in posPeakNoise:
          posNoiseHisto.Fill(entry)

        for entry in negPeakNoise:
          negNoiseHisto.Fill(entry)

        posNoiseStack.Add(posNoiseHisto)
        negNoiseStack.Add(negNoiseHisto)
    totalPosNoiseHisto = ROOT.TH1D("PeakPositiveNoiseOverall","PeakPositiveNoiseOverall",50,np.amin(posPeakNoiseTotal)-0.01,np.amax(posPeakNoiseTotal)+0.01)     
    totalNegNoiseHisto = ROOT.TH1D("PeakNegativeNoiseOverall","PeakNegativeNoiseOverall",50,np.amin(negPeakNoiseTotal)-0.01,np.amax(negPeakNoiseTotal)+0.01)     
    
    for entry in posPeakNoiseTotal:
        totalPosNoiseHisto.Fill(entry)

    for entry in negPeakNoiseTotal:
        totalNegNoiseHisto.Fill(entry)
    
    for pin_file in os.listdir(pin_dir):
        print pin_file
        numPulses,pin,rms = readPinFile(os.path.join(pin_dir,pin_file))
        pin_vals.append(pin)
        pin_rms.append(rms)
        npulses.append(numPulses)
    check_dir("root_files/Box%02d"%(box))
    check_dir("root_files/Box_%02d/Channel_%02d/"%(box,channel))
    outRoot = ROOT.TFile("root_files/Box_%02d/Channel_%02d/histos.root" %(box,channel),"RECREATE") 
    
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
   
    for photonSingleVal in photonCounts:
        photonHistoSingle.Fill(photonSingleVal) 

    for photonVal in photonCountsAverage:
       photonHistoAverage.Fill(photonVal)
    
    for photonRMSVal in photonRMS:
       photonHistoRMS.Fill(photonRMSVal)

    pinRMSHisto.Write()

    timeGapHisto, timeGapHistoInteresting = createTimeGapHisto(time_trace,pmt_traces,noise_traces,0.1)
    
    timeGapHisto.Write()
    
    timeGapHistoInteresting.Write()

    photonHistoSingle.Write()
    
    photonHistoAverage.Write()
   
    photonHistoRMS.Write()
   
    posNoiseStack.Write()
    negNoiseStack.Write()

    totalPosNoiseHisto.Write()
    totalNegNoiseHisto.Write()

    outRoot.Close()
    
     
    plt.figure(0)
    plt.errorbar(pin_vals,photonCountsAverage,yerr=np.divide(photonRMS,np.sqrt(numReadings)),xerr=np.divide(pin_rms,np.sqrt(npulses)),linestyle="",fmt="")
    plt.scatter(pin_vals,photonCountsAverage,s=10*range(1,(len(pin_vals))+1))
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    plt.savefig("root_files/Box_%02d/Channel_%02d/PhotonVsPin.png"%(box,channel))
    plt.figure(1)
    plt.savefig("root_files/Box_%02d/Channel_%02d/envelope.png"%(box,channel))
    plt.figure(2)
    plt.savefig("root_files/Box_%02d/Channel_%02d/envelopeLessThan350ns.png"%(box,channel))
    plt.figure(3)
    plt.savefig("root_files/Box_%02d/Channel_%02d/envelopeRAW.png"%(box,channel))
