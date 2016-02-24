import sys
import calc_utils as calc
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":

    ## File path
    fileName1 = sys.argv[1]
    fileName2 = sys.argv[2]
    
    ## Read data
    x1,y1 = calc.readPickleChannel(fileName1, 1,False)
    x2,y2 = calc.readPickleChannel(fileName2, 1, False)
    
    y1mean = np.mean(y1,0)
    y2mean = np.mean(y2,0)

    plt.figure(0)
    plt.plot(x1,y1mean,label=fileName1)
    plt.plot(x1,y2mean,label=fileName2)
    plt.legend(loc = "upper right")
    plt.show()
    
