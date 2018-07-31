import serial
from l1a import *

s = serial.Serial('COM4', 115200)
rawdata = []

linen = 0
while linen < 3000:
    line = str(s.readline())[2:-5]
    if len(line) == 0:
        print("ignoring, partial line? " + line)
        continue

    if line == "Divider":
        rawdata.append([])
    elif line[0] is "[" and line[-1] is "]":
        try:
            exec("temp = " + line)
            rawdata[-1].append(temp)
        except IndexError:
            print("ignoring, middle of event? " + line)
        except SyntaxError:
            print("ignoring, badly formatted value? " + line)
    else:
        print("ignoring, unrecognized line " + line)
    linen += 1

s.close()

for l1a in rawdata:
    if len(l1a) != 1324:
        print("l1a with wrong length, removing")
        rawdata.remove(l1a)


# a list to be filled with L1As in order received
fmtdata = []
for l1a in rawdata:
    # a string containing only binary digits, all the data from the FPGA concated together
    # thus, [ROC47bit0 -> ROC0bit0, ROC47bit1 -> ROC0bit1....]
    ds = ''
    for reg in l1a:
        # format specifier to convert the number into binary, as a string
        reg[0] = '{0:032b}'.format(reg[0])
        ds += reg[0]

    if len(ds) != 21184:
        print("l1a improperly formatted, moving on")
        continue

    fmtdata.append([])
    for i in range(48):
        dtmrocs = "".join([ds[(47-i)+48*j] for j in range(int(len(ds)/48))])
        asdblrs = []
        for dtmroc in dtmrocs:
            asdblrs.append()#some stuff
        fmtdata[-1].append(L1a(dtmrocs, asdblrs, int(l1a[-1][0][:-16])))

# check to make sure each is of the correct length, toss it if else
for l1a in fmtdata:
    if len(l1a.dtmrocs) != 48 or len(l1a.dtmrocs[0]) != 441:
        print("Data parsed incorrectly, tossing out")
        fmtdata.remove(l1a)

print(fmtdata[0][0][0])
print(fmtdata[0][0][47])
print(fmtdata[0][1])
print(rawdata[0])