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

def createTimeGapHisto(time_trace,pmt_traces,noise_traces,noise_threshold):
    TimeGapVals = []
    noiseCrossIndex = []
    meanOffset = []
    meanOffsetError = []
    offsetFWHM = []
    offsetFWHMError = []
    timeGapValsSingle = []
    pmtPulseTimes = []
    ledPulseTimeVoltages = []
    ledPulseTimeVoltagesMeans = []
    fftFrequencies = []
    fftValues = []
    sampleIndex = 0
    for i in range(len(pmt_traces)):
        pmt_pulse_time = calcPeakRisePoint(time_trace,pmt_traces[i],0.2)*1e9
        #driver_noise_time = calc.interpolate_threshold(time_trace,np.fabs(noise_traces[i]),noise_threshold*np.amin(noise_traces[i]))*1e9
        #driver_noise_time = calcPeakRisePoint(time_trace,noise_traces[i],noise_threshold)*1e9
        driver_noise_time = getPosThresholdCrossing(time_trace,noise_traces[i],0.3)*1e9
        pmtPulseTimes.append(pmt_pulse_time)
        led_pulse_time = pmt_pulse_time-237.6
        noise_vals = []

        if i==0:
           #Getting index 20 ns before PMT pulse
           sampleIndex = int(np.argwhere(time_trace > pmt_pulse_time*1e-9)[-50])
           fftValues = np.absolute(np.fft.rfft(pmt_traces[i][:sampleIndex]))
           fftFrequencies = np.fft.rfftfreq(sampleIndex,0.4e-9)
        else:
           fftValues += np.absolute(np.fft.rfft(pmt_traces[i][:sampleIndex]))
        for entry in np.argwhere(time_trace >= led_pulse_time*1e-9)[:6]:
            ledPulseTimeVoltages.append(noise_traces[i][entry])
            noise_vals.append(noise_traces[i][entry])
        for entry in np.argwhere(time_trace < led_pulse_time*1e-9)[-5:]:
            ledPulseTimeVoltages.append(noise_traces[i][entry])
            noise_vals.append(noise_traces[i][entry])
             
            ledPulseTimeVoltagesMeans.append(np.mean(noise_vals)) 

        if not np.isfinite(driver_noise_time) or not np.isfinite(pmt_pulse_time):
            continue
        TimeGapVals.append(np.fabs(pmt_pulse_time-driver_noise_time))
        timeGapValsSingle.append(np.fabs(pmt_pulse_time-driver_noise_time))
        for j in range(len(time_trace)):
            if time_trace[j]*1e9 > driver_noise_time:
                noiseCrossIndex.append(j)
                break
        if (i+1)%100 == 0:        
 	    timeGapHistoSingle = ROOT.TH1D("TimeDifferencebetweennoiseandPMTPeakSingleReading","TimeDifferencebetweennoiseandPMTPeakSingleReading",50,(np.amin(timeGapValsSingle)-10),(np.amax(timeGapValsSingle)+10))
	    for timeGapVal in timeGapValsSingle:
	       timeGapHistoSingle.Fill(timeGapVal)
	    timeGapHistoSingle.Fit("gaus")
	    meanOffset.append(timeGapHistoSingle.GetFunction("gaus").GetParameter(1))
	    meanOffsetError.append(timeGapHistoSingle.GetFunction("gaus").GetParError(1))
	    offsetFWHM.append(timeGapHistoSingle.GetFunction("gaus").GetParameter(2)*2.35482)
	    offsetFWHMError.append(timeGapHistoSingle.GetFunction("gaus").GetParError(2)*2.35482)
            #Emptying array
            timeGapValsSingle = []
        
    

    timeGapHisto = ROOT.TH1D("TimeDifferencebetweennoiseandPMTPeak","TimeDifferencebetweennoiseandPMTPeak",50,(np.amin(TimeGapVals)-10),(np.amax(TimeGapVals)+10))
    LEDPulseTimeNoiseVoltageHisto = ROOT.TH1D("GroundNoiseVoltageWhenLEDIsPulsing","GroundNoiseVoltageWhenLEDIsPulsing",50,(np.amin(ledPulseTimeVoltages)-0.01),(np.amax(ledPulseTimeVoltages)+0.01))
    for timeGapVal in TimeGapVals:
        timeGapHisto.Fill(float(timeGapVal))
   
    for noiseVoltage in ledPulseTimeVoltages:
        LEDPulseTimeNoiseVoltageHisto.Fill(float(noiseVoltage))
   
    LEDPulseTimeNoiseVoltageHisto.Write() 

    plt.figure(1)
    plt.subplot(211)
    plt.ylabel("Ground Noise Voltage (V)")
    for k in range(len(noiseCrossIndex)):
        noise_trace = noise_traces[k]
        plt.plot(np.multiply(time_trace[noiseCrossIndex[k]-150:]-time_trace[noiseCrossIndex[k]-150],1e9),noise_trace[noiseCrossIndex[k]-150:],label="Trace: "+str(k))
        plt.axvline(pmtPulseTimes[k]-237.6-(time_trace[noiseCrossIndex[k]-150]*1e9),linewidth=2,color="black")
    plt.subplot(212)
    for k in range(len(noiseCrossIndex)):
        pmt_trace = pmt_traces[k]
        plt.plot(np.multiply(time_trace[noiseCrossIndex[k]-150:]-time_trace[noiseCrossIndex[k]-150],1e9),pmt_trace[noiseCrossIndex[k]-150:],label="Trace: "+str(i))
        plt.axvline(pmtPulseTimes[k]-237.6-(time_trace[noiseCrossIndex[k]-150]*1e9),linewidth=2,color="black")
       
    plt.ylabel("PMT Pulse")
    plt.xlabel("Time (ns)")
    plt.subplot(211)
    ax = plt.gca()
    ax.set_xticklabels([])
    

    plt.figure(3)
    plt.subplot(211)
    plt.ylabel("Ground Noise Voltage (V)")
    for k in range(len(noise_traces)):
        noise_trace = noise_traces[k]
        plt.plot(np.multiply(time_trace,1e9),noise_trace,label="Trace: "+str(i))
        plt.axvline(pmtPulseTimes[k]-237.6,linewidth=2,color="black")
    plt.subplot(212)
    for k in range(len(pmt_traces)):
        pmt_trace = pmt_traces[k]
        plt.plot(np.multiply(time_trace,1e9),pmt_trace,label="Trace: "+str(i))
        plt.axvline(pmtPulseTimes[k]-237.6,linewidth=2,color="black")
    plt.ylabel("PMT Pulse")
    plt.xlabel("Time (ns)")
    plt.subplot(211)
    ax = plt.gca()
    ax.set_xticklabels([])


    plt.figure(9)
    plt.subplot(211)
    plt.ylabel("Mean Ground Noise Voltage (V)")
    plt.plot(np.multiply(time_trace,1e9),np.mean(noise_traces,0))
    plt.axvline(np.mean(pmtPulseTimes[k])-237.6,linewidth=2,color="black")
    plt.subplot(212)
    plt.plot(np.multiply(time_trace,1e9),np.mean(pmt_traces,0))
    plt.axvline(np.mean(pmtPulseTimes[i])-237.6,linewidth=2,color="black")
    plt.ylabel("Mean PMT Pulse")
    plt.xlabel("Time (ns)")
    plt.subplot(211)
    ax = plt.gca()
    ax.set_xticklabels([])

    plt.figure(10)
    sub =plt.subplot(211)
    plt.ylabel("Fourier Transform of PMT dark noise")
    plt.plot(fftFrequencies,fftValues)
    sub.set_xlabel("Frequency (Hz)")
    print fftFrequencies
    print fftValues
    sub = plt.subplot(212)
    for k in range(len(pmt_traces)):
        pmt_trace = pmt_traces[k]
        plt.plot(np.multiply(time_trace[:sampleIndex],1e9),pmt_trace[:sampleIndex],label="Trace: "+str(i))
        plt.axvline(pmtPulseTimes[k]-237.6,linewidth=2,color="black")
    sub.set_ylabel("PMT Noise")
    sub.set_xlabel("Time (ns)")
    
    return timeGapHisto, meanOffset, meanOffsetError, offsetFWHM, offsetFWHMError, ledPulseTimeVoltagesMeans


def fftNoiseTraceLowPassFilter(time_trace,noise_traces,threshold_lower=0.0e9,threshold_upper=0.1e9):
    fftValues = []
    fftSingleTraceValues = []
    scalingFactor = []
    fftFrequencies = []
    filteredNoise = []
    cutoffIndexUpper = 0
    cutoffIndexLower = 0
    for i in range(len(noise_traces)):
        if i==0:
           #Getting index 20 ns before PMT pulse
           fftValues = np.absolute(np.fft.rfft(noise_traces[i],norm="ortho"))
           fftSingleTraceValues.append(np.fft.rfft(noise_traces[i],norm="ortho"))
           fftFrequencies = np.fft.rfftfreq(len(noise_traces[i]),0.4e-9)
           cutoffIndexUpper = int(np.where(fftFrequencies < threshold_upper)[-1][-1])
           cutoffIndexlower = int(np.where(fftFrequencies > threshold_lower)[-1][0])
           scalingFactor.append(np.trapz(fftFrequencies[cutoffIndexlower:cutoffIndexUpper],fftValues[cutoffIndexlower:cutoffIndexUpper])/np.trapz(fftFrequencies,fftValues))
           filteredNoise.append(np.multiply(np.fft.irfft(fftSingleTraceValues[i][cutoffIndexLower:cutoffIndexUpper],norm="ortho"),1.0))
           
        else:
           fftSingleTraceValues.append(np.fft.rfft(noise_traces[i],norm="ortho"))
           fftValues += np.absolute(np.fft.rfft(noise_traces[i]))
           scalingFactor.append(np.trapz(fftFrequencies[cutoffIndexlower:cutoffIndexUpper],fftValues[cutoffIndexlower:cutoffIndexUpper])/np.trapz(fftFrequencies,fftValues))
           filteredNoise.append(np.multiply(np.fft.irfft(fftSingleTraceValues[i][cutoffIndexLower:cutoffIndexUpper]),1.0))

    timeValues = np.arange(0,np.amax(time_trace),np.amax(time_trace)/len(filteredNoise[0]))
    plt.figure(20)
    sub = plt.subplot(311)
    sub.set_ylabel("Ground Noise Voltage (V)")
    for i in range(len(noise_traces)):
        plt.plot(np.multiply(time_trace,1e9),(noise_traces[i]))
    sub = plt.subplot(312)
    plt.plot(fftFrequencies,fftValues)
    sub.set_ylabel("Sum of Abs Fourier transform")
    sub.set_xlabel("Frequency (Hz)")
    sub = plt.subplot(313)
    sub.set_ylabel("Filtered ground noise with cutoff %f to %f"%(threshold_lower,threshold_upper))
    sub.set_xlabel("Time (ns)")
    for i in range(len(filteredNoise)):
        plt.plot(np.multiply(timeValues,1e9),filteredNoise[i])


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
    noise_dir = os.path.dirname(root_dir+"/driver_noise/Box_%02d/Channel_%02d/" % (box,channel))
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
    posNoiseStack = ROOT.THStack("Positive Peak Noise Voltage","Positive Peak Noise Voltage")
    negNoiseStack = ROOT.THStack("Negative Peak Noise Voltage","Negative Peak Noise Voltage")
    colIter = 1
    posPeakNoiseTotal = []
    negPeakNoiseTotal = []
    absPeakNoiseTotal = []
    absPeakNoiseAvg = []
    absPeakNoiseError = []
    posPeakNoiseAvg = []
    posPeakNoiseError = []
    negPeakNoiseAvg = []
    negPeakNoiseError = []
    

    for noise_file in os.listdir(noise_dir):
        if width != -1000:
            if int(noise_file[-9:-4]) != width:
               continue
       
        x1 = None
        y1 = None
        posPeakNoise = []
        negPeakNoise = []
        absPeakNoise  = []
        try:
            x1,y1 = calc.readPickleChannelPadY(os.path.join(noise_dir,noise_file), 1,False)
        except Exception,e:
            print str(e) 
            continue
        print "READ IN FILES"
        print "NOISE FILE: "+noise_file
        print "TRACE COUNT: "+str(len(y1))
        for i in range(len(y1)):
            noise_traces.append(y1[i])
            posPeakNoise.append(np.amax(y1[i]))
            negPeakNoise.append(np.amin(y1[i]))
            posPeakNoiseTotal.append(np.amax(y1[i]))
            negPeakNoiseTotal.append(np.amin(y1[i]))
            absPeakNoiseTotal.append(np.amax(np.fabs(y1[i])))
            absPeakNoise.append(np.amax(np.fabs(y1[i])))
       
        print "Doing noise analysis" 
        absPeakNoiseAvg.append(np.mean(absPeakNoise))
        absPeakNoiseError.append(np.std(absPeakNoise)/np.sqrt(len(absPeakNoise)))
        posPeakNoiseAvg.append(np.mean(posPeakNoise))
        posPeakNoiseError.append(np.std(posPeakNoise)/np.sqrt(len(posPeakNoise)))
        negPeakNoiseAvg.append(np.mean(negPeakNoise))
        negPeakNoiseError.append(np.std(negPeakNoise)/np.sqrt(len(negPeakNoise)))
        posNoiseHisto = ROOT.TH1D("Positive Peak Noise"+str(colIter),"Positive Peak Noise"+str(colIter),40,0.4,0.75)
        negNoiseHisto = ROOT.TH1D("Negative Peak Noise"+str(colIter),"Negative Peak Noise"+str(colIter),40,-0.6,-0.25)
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
    
   
    posNoiseVsPhoton = ROOT.TH2D("MaximumNoiseVoltageVsPhotonCount","MaximumNoiseVoltageVsPhotonCount",15,np.amin(posPeakNoiseTotal)-.01,np.amax(posPeakNoiseTotal)+.01,75,np.amin(photonCounts)-100,np.amax(photonCounts)+100) 
    negNoiseVsPhoton = ROOT.TH2D("MaximumNegativeNoiseVoltageVsPhotonCount","MaximumNegativeNoiseVoltageVsPhotonCount",15,np.amin(negPeakNoiseTotal)-.01,np.amax(negPeakNoiseTotal)+.01,75,np.amin(photonCounts)-100,np.amax(photonCounts)+100) 
    print "LEN of posPeakNoise: "+str(len(posPeakNoiseTotal)) 
    print "LEN of photonCounts: "+str(len(photonCounts)) 
    for i in range(len(photonCounts)):
        posNoiseVsPhoton.Fill(posPeakNoiseTotal[i],photonCounts[i])
        negNoiseVsPhoton.Fill(negPeakNoiseTotal[i],photonCounts[i])
    for photonSingleVal in photonCounts:
        photonHistoSingle.Fill(photonSingleVal) 

    for photonVal in photonCountsAverage:
       photonHistoAverage.Fill(photonVal)
    
    for photonRMSVal in photonRMS:
       photonHistoRMS.Fill(photonRMSVal)

    pinRMSHisto.Write()

    timeGapHisto, meanOffset, meanOffsetError, offsetFWHM, offsetFWHMError, ledPulseTimeNoiseVoltages  = createTimeGapHisto(time_trace,pmt_traces,noise_traces,0.1)
    
    photonCountVsPulseTimeNoiseVoltage = ROOT.TH2D("photonCountVsledPulseTimeNoiseVoltages","photonCountVsledPulseTimeNoiseVoltages",20,np.amin(ledPulseTimeNoiseVoltages)-.01,np.amax(ledPulseTimeNoiseVoltages)+.01,75,np.amin(photonCounts)-100,np.amax(photonCounts)+100) 
    
    for k in range(len(photonCounts)):
         photonCountVsPulseTimeNoiseVoltage.Fill(ledPulseTimeNoiseVoltages[k],photonCounts[k])
    
    
    timeGapHisto.Write()

    photonCountVsPulseTimeNoiseVoltage.Write()
    

    photonHistoSingle.Write()
    
    photonHistoAverage.Write()
   
    photonHistoRMS.Write()
   
    posNoiseStack.Write()
    negNoiseStack.Write()

    totalPosNoiseHisto.Write()
    totalNegNoiseHisto.Write()

    posNoiseVsPhoton.Write()
    negNoiseVsPhoton.Write()
    outRoot.Close()
    print posPeakNoiseError 
    plt.figure(0)
    plt.errorbar(pin_vals,photonCountsAverage,yerr=np.divide(photonRMS,np.sqrt(numReadings)),xerr=np.divide(pin_rms,np.sqrt(npulses)),linestyle="",fmt="")
    plt.scatter(pin_vals,photonCountsAverage,s=10*range(1,(len(pin_vals))+1))
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/PhotonVsPin.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/PhotonVsPinWidth%05d.png"%(box,channel,width))
    plt.figure(1)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/envelope.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/envelopeWidth%05d.png"%(box,channel,width))
    plt.figure(3)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/envelopeRAW.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/envelopeRAWWidth%05d.png"%(box,channel,width))
    plt.figure(4)
    plt.xlabel("Absolute Peak Noise")
    plt.ylabel("Photon Count")
    plt.scatter(absPeakNoiseTotal,photonCounts)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/absPeakNoiseVsPhotonCount.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/absPeakNoiseVsPhotonCountWidth%05d.png"%(box,channel,width))
    plt.figure(5)
    plt.xlabel("Average Absolute Peak Noise")
    plt.ylabel("PIN  Readings")
    plt.errorbar(absPeakNoiseAvg,pin_vals,yerr=np.divide(pin_rms,np.sqrt(npulses)),xerr=absPeakNoiseError,linestyle="")
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/meanAbsPeakNoiseVsPIN.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/meanAbsPeakNoiseVsPINWidth%05d.png"%(box,channel,width))

    readingsCount = range(1,len(photonCountsAverage))
    plt.figure(6)
    plt.xlabel("Reading Number")
    sub = plt.subplot(2,2,1)
    sub.set_ylabel("Photon Count")
    plt.errorbar(readingsCount,photonCountsAverage,yerr=np.divide(photonRMS,np.sqrt(numReadings)),linestyle="")
    sub = plt.subplot(2,2,2)
    sub.yaxis.tick_right()
    sub.set_ylabel("PIN Reading")
    plt.errorbar(readingsCount,pin_vals,yerr=np.divide(pin_rms,np.sqrt(npulses)),linestyle="")
    sub = plt.subplot(2,2,3)
    sub.set_ylabel("Average Max Positive Noise (V)")
    plt.errorbar(readingsCount,posPeakNoiseAvg,yerr=posPeakNoiseError,linestyle="")
    sub = plt.subplot(2,2,4)
    sub.set_ylabel("Average Max Negative Noise (V)")
    sub.yaxis.tick_right()
    plt.errorbar(readingsCount,negPeakNoiseAvg,yerr=negPeakNoiseError,linestyle="")
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/readingResults.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/readingResultsWidth%05d.png"%(box,channel,width))
    print "Len mean offset: "+str(len(meanOffset))
    print "Len mean offset error: "+str(len(meanOffsetError))
    plt.figure(7)
    plt.xlabel("Reading Number")
    plt.ylabel("Mean Time Offset (ns)")
    plt.errorbar(readingsCount,meanOffset,yerr=meanOffsetError)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/readingMeanOffset.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/readingMeanOffsetWidth%05d.png"%(box,channel,width))
    
    print "Len mean offset FWHM: "+str(len(offsetFWHM))
    print "Len mean offset FWHM error: "+str(len(offsetFWHMError))
    plt.figure(8)
    plt.xlabel("Reading Number")
    plt.ylabel("Time Offset FWHM (ns)")
    plt.errorbar(readingsCount,offsetFWHM,yerr=offsetFWHMError)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/OffsetFWHM.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/OffsetFWHM%05d.png"%(box,channel,width))


    plt.figure(9)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/envelopeMean.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/envelopeMean%05d.png"%(box,channel,width))
    
    plt.figure(10)
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/PMTNoiseFreq.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/PMTNoiseFreq%05d.png"%(box,channel,width))
    
    fftNoiseTraceLowPassFilter(time_trace,noise_traces)
    plt.figure(20)
    
    if width == -1000:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/filteredGroundNoise.png"%(box,channel))
    else:
        plt.savefig(root_dir+"/root_files/Box_%02d/Channel_%02d/filteredGroundNoise%05d.png"%(box,channel,width))
