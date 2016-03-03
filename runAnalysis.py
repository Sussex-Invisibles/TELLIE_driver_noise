import os
import sys


box_numbers = []
channel_numbers = []
root_dir = sys.argv[1]
boxFolders = os.listdir(root_dir+"/pmt_response")

for boxFolder in boxFolders:
    channels = os.path.join(root_dir+"/pmt_response",boxFolder)
    for channel in os.listdir(channels):
        box_numbers.append(int(boxFolder[4:]))
        channel_numbers.append(int(channel[8:]))

print box_numbers
print channel_numbers

for i in range(len(box_numbers)):
    os.system("python analyseTraces.py -d %s -b %02d -c %02d" %(root_dir,box_numbers[i],channel_numbers[i]))

