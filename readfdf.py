from l1a import L1a

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


with open("save.fdf", "r") as fdf:
    exec("data = " + fdf.readline())
# noinspection PyUnresolvedReferences
data = data

for l1a in data:
    print("l1a eventid", l1a.eventid)
    print(l1a.dtmrocs[0])
    print(l1a.dtmrocs[47])

    listchecker(l1a.asdblrs[0], "000010100000101000001010", "asdblrs0")
    listchecker(l1a.asdblrs[47], "000010110000101100001011", "asdblrs47")

print("Checked {} bits, found {} errors".format(errortracker[0], errortracker[1]))
