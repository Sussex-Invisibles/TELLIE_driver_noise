###########################################
# Script to read in pickled wave 
# file for basic checks. Inherits
# strongly from AcquireTek/calc_utils.py
# 
# Author: Ed Leming 
# Date:   08/04/2015
############################################
import time
import sys
import calc_utils as calc

if __name__ == "__main__":

    ## File path
    fileName = sys.argv[1]
    
    ## Read data
    fileRead = time.time()
    x,y = calc.readPickleChannel(fileName, 1,False)
    print "Reading %d pulses from file took %1.2f s" % ( len(y[:,0]), (time.time()-fileRead) )
    calc.printParams(x,y,"pmt pulses")
    print "Reading + calcs on %d pulses from file took %1.2f s" % ( len(y[:,0]), (time.time()-fileRead) )

    ### PLOT ###
    calc.plot_eg_pulses(x,y,10,show=True)
    
