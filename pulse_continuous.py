###################################################
# Pulses TELLIE in continuous mode.
# This script produces a continuous
# signal to allow for adjustments of
# the PIN diode pots.
# 
# Author: Ed Leming <e.leming09@googlemail.com>
# Date: 01/05/15
###################################################
from core import serial_command
import optparse
import sys

chan = 0

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()
    pin_dict, rms_dict, this_channel = sc.read_pin(chan)
    print pin_dict
    print rms_dict

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-w",dest="width",default=0,help="IPW setting (0-16383)")
    (options,args) = parser.parse_args()

    width = int(options.width)
    channel = (int(options.box)-1)*8 + int(options.channel)
    chan = channel
    width = int(options.width)
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTE3C0PG")
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(0.1)
    #sc.set_pulse_delay(25e-3) 
    try:
        sc.fire_continuous()
        while True:
            pass
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")
        
        
