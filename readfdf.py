from datareception import L1a, fmt

errortracker = [0, 0]


def listchecker(checklist, value, name):
    channelcntr = 0
    errors = 0
    for channel in checklist:
        if channel != value:
            print(name + " channel {} error, value was:".format(channelcntr), channel)
            errors += 1
        channelcntr += 1

    errortracker[0] += 27 * channelcntr
    errortracker[1] += errors


with open("dtm0ls.fdf", "r") as fdf:
    exec("data = " + fdf.readline())
# noinspection PyUnresolvedReferences
data = data

channeldata = ["" for i in range(32)]
for l1an in range(0, len(data), 11):
    for l1ann in range(l1an, l1an + 11):
        for channeln in range(len(channeldata)):
            channeldata[channeln] += (data[l1an].asdblrs[0] + data[l1an].asdblrs[47])[channeln]

for channel in channeldata:
    bitn = 0
    for char in channel:
        if bitn % (24 * 11) == 0:
            print(fmt.RED + "|X|" + fmt.END, end="")
        elif bitn % 24 == 0:
            print("|", end="")

        bitn += 1
        if char == "1":
            print(fmt.GREEN + char + fmt.END, end="")
        elif char == "0":
            print(fmt.BLUE + char + fmt.END, end="")

    print("")

#     listchecker(l1a.asdblrs[0], "000010100000101000001010", "asdblrs0")
#     listchecker(l1a.asdblrs[47], "000010110000101100001011", "asdblrs47")
#
# print("Checked {} bits, found {} errors".format(errortracker[0], errortracker[1]))
