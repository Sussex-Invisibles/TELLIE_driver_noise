import csv
import optparse
import sys
import os
import calc_utils as calc
import matplotlib.pyplot as plt


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-f",dest="fileName",default="test",help="Data File")
    (options,args) = parser.parse_args()
    cwd = os.getcwd()
    inFileName = os.path.join(cwd,options.fileName)
    inDir = os.path.dirname(inFileName)
    inFile =  open(inFileName,"r")
    
    fileNameString = (os.path.split(options.fileName))[1]
    print fileNameString
    timeInfoIndex = fileNameString.find("DATA")
    timeInfo = fileNameString[timeInfoIndex+4:-4]
    print "Time INFO: "+timeInfo
    
    readings = []
    time = []
    pinValues = []
    pinErrors = []
    photonCount = []
    photonCountError = [] 

    #Skipping header
    next(inFile)
    next(inFile)
    read = csv.reader(inFile,delimiter=" ")
    for row in read:
        readings.append(int(row[0]))
        time.append(float(row[1]))
        pinValues.append(float(row[2]))
        pinErrors.append(float(row[3]))
        photonCount.append(float(row[4]))
        photonCountError.append(float(row[5]))
    plt.figure(0)
    plt.subplot(211)
    plt.errorbar(readings,pinValues,yerr=pinErrors)
    plt.ylabel("PIN Reading")
    plt.subplot(212)
    plt.errorbar(readings,photonCount,yerr=photonCountError)
    plt.xlabel("Reading")
    plt.ylabel("Photon Count")
    plt.savefig(os.path.join(inDir,"PhotonPinVsReading"+timeInfo+".png"))
    plt.show()
    plt.figure(1)
    plt.errorbar(pinValues,photonCount,xerr=pinErrors,yerr=photonCountError,linestyle="")
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    plt.savefig(os.path.join(inDir,"PhotonVsPin"+timeInfo+".png"))
    plt.show()
    
