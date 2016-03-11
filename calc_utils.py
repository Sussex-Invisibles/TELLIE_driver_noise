###############################################
# Functions to read in pickled scope traces
# and perform standard measurements.
# 
# Will calculate: Integrated area, rise time,
# fall time, pulse width, peak voltage and
# the jitter on two signals. 
# 
# Author: Ed Leming
# Date: 17/03/2015
################################################
import pickle
import utils
import time
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

def readPickleChannel(file, channel_no, correct_offset=True):
    """Read data set as stored in pickle file"""
    # Make sure file path is correct format
    if file[-4:] == ".pkl":
        file = file[0:-4]
    ### READ Pickle File ###
    wave = utils.PickleFile(file, 4)
    wave.load()
    xRaw = wave.get_meta_data("timeform_%i" % channel_no)
    yRaw = wave.get_data(channel_no)
    # Correct for trigger offset in timestamps
    x = xRaw - xRaw[0]
    # Count how many pulses saved the file
    count = 0
    for i in yRaw:
        count = count + 1
    ### Make 2D array of pulse y values ###
    y = np.zeros( (count, len(xRaw)) )
    print len(xRaw)
    for i, ent in enumerate(yRaw):
        if correct_offset == True:
            y[i, :] = ent  - np.mean(ent[0:20])
        else:
            y[i, :] = ent  
    return x,y

def readPickleChannelPadY(file, channel_no, correct_offset=True):
    """Read data set as stored in pickle file"""
    # Make sure file path is correct format
    if file[-4:] == ".pkl":
        file = file[0:-4]
    ### READ Pickle File ###
    wave = utils.PickleFile(file, 4)
    wave.load()
    xRaw = wave.get_meta_data("timeform_%i" % channel_no)
    yRaw = wave.get_data(channel_no)
    # Correct for trigger offset in timestamps
    x = xRaw - xRaw[0]
    # Count how many pulses saved the file
    count = 0
    for i in yRaw:
        count = count + 1
    ### Make 2D array of pulse y values ###
    y = np.zeros( (count, len(xRaw)) )
    print len(xRaw)
    for i, ent in enumerate(yRaw):
        if correct_offset == True:
            try:
                y[i, :] = ent  - np.mean(ent[0:20])
            except:
                while len(ent)<len(x):
                  ent = np.append(ent,0)
                y[i, :] = ent  - np.mean(ent[0:20])
                
        else:
            try:
                y[i, :] = ent  
            except:
                while len(ent)<len(x):
                  ent = np.append(ent,0)
                y[i, :] = ent  
    return x,y

def positive_check(y):
    if np.abs(max(y[1,:])) > np.abs(min(y[1,:])):
        return True
    else:
        return False

def rms(alist):
    '''Calc rms of 1d array'''
    if len(alist) > 1:
        listsum = sum((i - np.mean(alist))**2 for i in alist)
        return np.sqrt(listsum/(len(alist) - 1.0))
    else:
       logging.warning("More than one item needed to calculate RMS, thus returning 0")
       return 0.

def interpolate_threshold(x, y, thresh, rise=True, start=0):
    """Calculate the threshold crossing using a linear interpolation"""
    if rise == True:
        index_high = np.where( y > thresh )[0][start]
    else:
        index_high = np.where( y < thresh )[0][start]
    index_low = index_high - 1
    dydx = (y[index_high] - y[index_low])/(x[index_high]-x[index_low])
    time = x[index_low] + (thresh - y[index_low]) / dydx
    #print "x0 = %1.1f\t(thresh - y0) = %1.1f\tdydx = %1.3f\ttime = %1.1f\tdx = %1.1f" % (x[index_low], (thresh - y[index_low]), dydx, time, (x[index_high] - x[index_low])) 
    return time

def calcArea(x,y):
    """Calc area of pulses"""
    trapz = np.zeros( len(y[:,0]) )
    for i in range(len(y[:,0])):
        trapz[i] = np.trapz(y[i,:],x)
    return np.mean(trapz), rms(trapz)

def calcRise(x,y):
    """Calc rise time of pulses"""
    rise = np.zeros( len(y[:,0]) )
    f = positive_check(y)
    if f == True:
        for i in range(len(y[:,0])):
            m = max(y[i,:])
            lo_thresh = m*0.1
            hi_thresh = m*0.9
            low = interpolate_threshold(x, y[i,:], lo_thresh)
            high = interpolate_threshold(x, y[i,:], hi_thresh)
            rise[i] = high - low
        return np.mean(rise), rms(rise)
    else: 
        for i in range(len(y[:,0])):
            m = min(y[i,:])
            lo_thresh = m*0.1
            hi_thresh = m*0.9
            low = interpolate_threshold(x, y[i,:], lo_thresh, rise=False)
            high = interpolate_threshold(x, y[i,:], hi_thresh, rise=False)
            rise[i] = high - low
        return np.mean(rise), rms(rise) 

def calcFall(x,y):
    """Calc fall time of pulses"""
    fall = np.zeros( len(y[:,0]) )
    f = positive_check(y)
    if f == True:
        for i in range(len(y[:,0])):
            m = max(y[i,:])
            m_index = np.where(y[i,:] == m)[0][0]
            lo_thresh = m*0.1
            hi_thresh = m*0.9
            low = interpolate_threshold(x[m_index-1:], y[i,m_index-1:], lo_thresh, rise=False)
            high = interpolate_threshold(x[m_index-1:], y[i,m_index-1:], hi_thresh, rise=False)
            fall[i] = low - high
        return np.mean(fall), rms(fall)
    else:
        for i in range(len(y[:,0])):
            m = min(y[i,:])
            m_index = np.where(y[i,:] == m)[0][0]
            lo_thresh = m*0.1
            hi_thresh = m*0.9
            low = interpolate_threshold(x[m_index:], y[i,m_index:], lo_thresh)
            high = interpolate_threshold(x[m_index:], y[i,m_index:], hi_thresh)
            fall[i] = low - high
        return np.mean(fall), rms(fall)
        
def calcWidth(x,y):
    """Calc width of pulses"""
    width = np.zeros( len(y[:,0]) )
    f = positive_check(y)
    if f == True:
        for i in range(len(y[:,0])):
            m = max(y[i,:])
            m_index = np.where(y[i,:] == m)[0][0]
            thresh = m*0.5
            first = interpolate_threshold(x[:m_index+1], y[i,:m_index+1], thresh, rise=True)
            second = interpolate_threshold(x[m_index-1:], y[i,m_index-1:], thresh, rise=False)
            width[i] = second - first
        return np.mean(width), rms(width)
    else:
        for i in range(len(y[:,0])):
            m = min(y[i,:])
            m_index = np.where(y[i,:] == m)[0][0]
            thresh = m*0.5
            first = interpolate_threshold(x[:m_index+1], y[i,:m_index+1], thresh, rise=False)
            second = interpolate_threshold(x[m_index-1:], y[i,m_index-1:], thresh, rise=True)
            width[i] = second - first
        return np.mean(width), rms(width)

def calcPeak(x,y):
    """Calc min amplitude of pulses"""
    peak = np.zeros( len(y[:,0]) )
    f = positive_check(y)
    if f == True:
        for i in range(len(y[:,0])):
            peak[i] = max(y[i,:])
        return np.mean(peak), rms(peak)
    else:
        for i in range(len(y[:,0])):
            peak[i] = min(y[i,:])
        return np.mean(peak), rms(peak)

def calcSinglePeak(pos_check, y_arr):
    """Calculate peak values for single trace inputs can be positive or negative."""
    if pos_check == True:
        m = max(y_arr)
    else:
        m = min(y_arr)
    return m

def calcJitter(x1, y1, x2, y2):
    """Calc jitter between trig and signal using CFD"""
    p1 = positive_check(y1)
    p2 = positive_check(y2)
    times = np.zeros(len(y1[:,0]))
    for i in range(len(y1[:,0])):
        m1 = calcSinglePeak(p1, y1[i,:])
        m2 = calcSinglePeak(p2, y2[i,:])
        time_1 = interpolate_threshold(x1, y1[i,:], 0.1*m1, rise=p1)
        time_2 = interpolate_threshold(x2, y2[i,:], 0.1*m2, rise=p2)
        times[i] = time_1 - time_2
    return np.mean(times), np.std(times), np.std(times)/np.sqrt(2*len(y1[:,0]))

def dictionary_of_params(x,y):
    """Calculate standard parameters and print to screen"""
    dict = {}
    dict["area"], dict["area error"] = calcArea(x,y)
    dict["rise"], dict["rise error"] = calcRise(x,y)
    dict["fall"], dict["fall error"] = calcFall(x,y)
    dict["width"], dict["width error"] = calcWidth(x,y)
    dict["peak"], dict["peak error"] = calcPeak(x,y)
    return dict

def printParamsDict(dict, name):
    """Calculate standard parameters and print to screen"""
    area, areaStd = dict["area"], dict["area error"]
    rise, riseStd = dict["rise"], dict["rise error"]
    fall, fallStd = dict["fall"], dict["fall error"]
    width, widthStd = dict["width"], dict["width error"]
    peak, peakStd = dict["peak"], dict["peak error"]

    print "%s:" % name
    print "--------"
    print "Area \t\t= %1.2e +/- %1.2e Vs" % (area, areaStd)
    print "Fall time \t= %1.2f +/- %1.2f ns" % (fall*1e9, fallStd*1e9)
    print "Rise time \t= %1.2f +/- %1.2f ns" % (rise*1e9, riseStd*1e9)
    print "Width \t\t= %1.2f +/- %1.2f ns" % (width*1e9, widthStd*1e9)
    print "Peak \t\t= %1.2f +/- %1.2f V" % (peak, peakStd)

def printParams(x,y, name):
    """Calculate standard parameters and print to screen"""
    area, areaStd = calcArea(x,y)
    rise, riseStd = calcRise(x,y)
    fall, fallStd = calcFall(x,y)
    width, widthStd = calcWidth(x,y)
    peak, peakStd = calcPeak(x,y)

    print "\n%s:" % name
    print "--------"
    print "Area \t\t= %1.2e +/- %1.2e Vs" % (area, areaStd)
    print "Fall time \t= %1.2f +/- %1.2f ns" % (fall*1e9, fallStd*1e9)
    print "Rise time \t= %1.2f +/- %1.2f ns" % (rise*1e9, riseStd*1e9)
    print "Width \t\t= %1.2f +/- %1.2f ns" % (width*1e9, widthStd*1e9)
    print "Peak \t\t= %1.2f +/- %1.2f V" % (peak, peakStd)

def plot_eg_pulses(x,y,n,scale=1e9,title=None,fname=None,show=False):
    """Plot example pulses""" 
    plt.figure()
    for i in range(n):
        plt.plot(x*scale,y[i,:])
    if title == None:
        plt.title( "Example pulses")
    else:
        plt.title(title)
    plt.xlabel("Time (ns)")
    plt.ylabel("Amplitude (V)")
    if fname is not None:
        plt.savefig(fname)
    if show == True:
        plt.show()
    plt.clf()
    plt.close()
