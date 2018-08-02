import serial
from l1a import L1a
s = serial.Serial('COM4', 115200)

rawdata = []
while 1:
    line = str(s.readline())[2:-5]
    if len(line) == 0:
        print("ignoring, partial line? " + line)
        continue

    if line == "End":
        break
    elif line == "Divider":
        rawdata.append([])
    elif line[0] is "[" and line[-1] is "]":
        try:
            exec("temp = " + line)
            # noinspection PyUnresolvedReferences
            rawdata[-1].append(temp)
        except IndexError:
            print("ignoring, middle of event? " + line)
        except SyntaxError:
            print("ignoring, badly formatted value? " + line)
    else:
        print("ignoring, unrecognized line " + line)
s.close()
print("data reception completed, serial port closed")


# a list to be filled with l1a objects in order received
fmtdata = []
for rawl1a in rawdata:
    if len(rawl1a) != 662:
        print("l1a with wrong length, removing",len(rawl1a))
        rawdata.remove(rawl1a)
        continue
    # a string containing only binary digits, all the data from the FPGA concated together
    # thus, [ROC47bit0 -> ROC0bit0, ROC47bit1 -> ROC0bit1....]
    ds = ''
    for reg in rawl1a:
        # format specifier to convert the number into binary, as a string
        reg[0] = '{0:032b}'.format(reg[0])
        ds += reg[0]

    # make sure that we have all the data we say we do
    if len(ds) != 21184:
        print("l1a improperly formatted, moving on")
        continue

    # create the l1a objects and add them to the list
    buildl1a = L1a([], [], int(rawl1a[-1][0][-16:], 2), rawl1a, ds)
    for i in range(48):
        dtmroc = "".join([ds[(47 - i) + 48 * j] for j in range(int(len(ds) / 48))])
        asdblr = ["".join([dtmroc[j + 1:j + 9], dtmroc[j + 10:j + 18], dtmroc[j + 19:j + 27]]) for j in
                  range(9, len(dtmroc), 27)]
        buildl1a.dtmrocs.append(dtmroc)
        buildl1a.asdblrs.append(asdblr)
    fmtdata.append(buildl1a)

# rigorously check to make sure each is of the correct length, toss it if else
badl1as = []
for l1a in fmtdata:
    if len(l1a.dtmrocs) != 48 or len(l1a.asdblrs) != 48 or len(l1a.rawds) != 21184:
        print("Data parsed incorrectly, wrong number of dtmrocs or bits received, tossing out")
        badl1as.append(l1a)
        continue
    for rocind in range(len(l1a.dtmrocs)):
        if len(l1a.dtmrocs[rocind]) != 441 or len(l1a.asdblrs[rocind]) != 16:
            print("Data parsed incorrectly, wrong length of dtmroc strings received, tossing out")
            badl1as.append(l1a)
            continue
        for asdblrind in range(len(l1a.asdblrs[rocind])):
            if len(l1a.asdblrs[rocind][asdblrind]) != 24:
                print("Data parsed incorrectly, wrong length of asd strings received, tossing out")
                badl1as.append(l1a)
                continue
for badl1a in set(badl1as):
    fmtdata.remove(badl1a)

print("{} l1as of proper length received, will save".format(len(fmtdata)))

savedata = "["
for l1a in fmtdata:
    savedata += l1a.formatSave()
    savedata += ","
savedata = savedata[:-1]
savedata += "]"

with open("save8.fdf", "w") as savefile:
    savefile.write(savedata)

