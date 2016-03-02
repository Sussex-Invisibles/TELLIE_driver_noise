import os


box_numbers = []
channel_numbers = []

boxFolders = os.listdir("./pmt_response")

for boxFolder in boxFolders:
    channels = os.path.join("./pmt_response",boxFolder)
    for channel in os.listdir(channels):
        box_numbers.append(int(boxFolder[4:]))
        channel_numbers.append(int(channel[8:]))

print box_numbers
print channel_numbers

for i in range(len(box_numbers)):
    os.system("python analyseTraces.py -b %02d -c %02d" %(box_numbers[i],channel_numbers[i]))

