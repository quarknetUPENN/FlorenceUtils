import serial

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
# each L1A is a list with 48 entries, one for each DTMROC, in order
# each DTMROC is a binary string, containing the data, in order
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

    fmtdata.append(([], l1a[-1][0][:-16]))
    for i in range(48):
        fmtdata[-1][0].append("".join([ds[(47-i)+48*j] for j in range(int(len(ds)/48))]))

# check to make sure each is of the correct length, toss it if else.  shouldn't be needed, just in case
for l1a in fmtdata:
    for roc in l1a[0]:
        if len(l1a[0]) != 48 or len(roc) != 441:
            print("Data parsed incorrectly, tossing out")
            fmtdata.remove(l1a)

print(fmtdata[0][0][0])
print(fmtdata[0][0][47])
print(fmtdata[0][1])
print(rawdata[0])