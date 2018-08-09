from socketserver import StreamRequestHandler
from os.path import exists
from zynqsshclient import ZynqSshClient


class L1a:
    def __init__(self, dtmrocs, asdblrs, eventid, rawl1a=None, rawds=None):
        # This is a 48 element list, one for each DTMROC, containing the 441 bits that DTMROC-n sent for this l1a as a
        # string.  So dtmrocs[n] gives the bits that DTMROC #n sent, for integer n on [0,47]
        self.dtmrocs = dtmrocs

        # This is a list of lists, which is 48 x 16, allowing you to see all of the low threshold bits that specific
        # asdblr channel sent for this l1a - so each binary string here is 24 long
        # So asdblrs[n][m] gives the bits from channel m on DTMROC #n, for integer n, m on [0,47] and [0,15] respectively
        # Note that on our boards channel #15 is tied low, #14 tied high, #13 tied low, and #12 tied high
        self.asdblrs = asdblrs

        # This is the 16-bit event ID as an integer, for this L1A, allowing L1As to be associated together as events
        # Each DTMROC's BxCntr and L1aCntr can also help verify this
        self.eventid = eventid

        # these are optional pieces of raw data that get formatted into the above
        self.rawl1a = rawl1a
        self.rawds = rawds

    # This formats the processed data into a string, which when eval()'d, becomes this L1a object again
    def formatSave(self):
        return "L1a(" + str(self.dtmrocs) + ", " + \
               str(self.asdblrs) + ", " + \
               str(self.eventid) + ")"


# helps makes printing in the terminal pretty
class fmt:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# this class allows us to receive data from the Zynq using a socket connection over ethernet
# theoritically this can be two way.  However, we simply listen for data coming for the Zynq
# and process it into L1a objects, catching any unexpected data that comes in and logging such events
# into a logfile without clogging up stdout
class ZynqTCPHandler(StreamRequestHandler):
    LogFileName = "ZynqTCPHandler.log"

    def __init__(self, request, client_address, server):
        super(ZynqTCPHandler, self).__init__(request, client_address, server)

    # this function gets called when a socket connection is made
    def handle(self):
        log = open(self.LogFileName, "a")

        log.write("\nstarting run...")
        print("Run started, receiving data...", end="")

        rawdata = []
        while 1:
            line = self.rfile.readline().strip().decode("utf-8")

            if len(line) == 0:
                log.write("ignoring, partial line? " + line + "\n")
                break

            if line == "End":
                break
            elif line == "Divider":
                rawdata.append([])
            elif line[0] is "[" and line[-1] is "]":
                try:
                    exec("self.temp = " + line)
                    # noinspection PyUnresolvedReferences
                    rawdata[-1].append(self.temp)
                except IndexError:
                    log.write("ignoring, middle of event? " + line + "\n")
                except SyntaxError:
                    log.write("ignoring, badly formatted value? " + line + "\n")
            elif line[:11] == "dips error ":
                log.write(line+"\n")
                dipscode = int(line[-1])
                if dipscode % 2 == 1:
                    print("dips overflowed!!!")
                elif dipscode % 2 == 0:
                    print("dips empty!")
            else:
                log.write("ignoring, unrecognized line " + line + "\n")
        log.write("finished receiving data \n")
        fmtdata, badl1an = self._datafmter(rawdata, log)

        log.write("{} proper l1as received, {} bad ones \n".format(len(fmtdata), badl1an))
        print("{} proper l1as received, {} bad l1as".format(len(fmtdata), badl1an))

        self._savefile(fmtdata, log)
        log.close()

    @staticmethod
    def _datafmter(rawdata, logfile):
        # a list to be filled with l1a objects in order received
        fmtdata = []
        for rawl1a in rawdata:
            if len(rawl1a) != 662:
                logfile.write("received l1a of length {}, removing \n".format(len(rawl1a)))
                rawdata.remove(rawl1a)
                continue
            # a string containing only binary digits, all the data from the FPGA concated together
            # thus, [ROC47bit0 -> ROC0bit0, ROC47bit1 -> ROC0bit1....]
            ds = ''
            for reg in rawl1a:
                # format specifier to convert the number into binary, properly padded
                reg[0] = '{0:032b}'.format(reg[0])
                ds += reg[0]

            # create the l1a objects and add them to the list by parsing the data in
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
                logfile.write("Data parsed incorrectly, wrong number of dtmrocs or bits received, tossing out\n")
                badl1as.append(l1a)
                continue
            for rocind in range(len(l1a.dtmrocs)):
                if len(l1a.dtmrocs[rocind]) != 441 or len(l1a.asdblrs[rocind]) != 16:
                    logfile.write("Data parsed incorrectly, wrong length of dtmroc strings received, tossing out\n")
                    badl1as.append(l1a)
                    continue
                for asdblrind in range(len(l1a.asdblrs[rocind])):
                    if len(l1a.asdblrs[rocind][asdblrind]) != 24:
                        logfile.write("Data parsed incorrectly, wrong length of asd strings received, tossing out\n")
                        badl1as.append(l1a)
                        continue
        for badl1a in set(badl1as):
            fmtdata.remove(badl1a)
        return fmtdata, len(set(badl1as))

    # saves fmtdata by asking user for a valid filename recursively
    def _savefile(self, fmtdata, log):
        filename = input("Input filename to save data as. Leave blank to not save\t\t")
        if filename == "":
            log.write("user chose not to save data \n")
            print("Data not saved")
            return
        elif exists(filename + ".fdf"):
            while True:
                overwriteprompt = input("Warning!  File already exists.  Overwrite? (y/n)\t")
                if overwriteprompt == "y":
                    break
                elif overwriteprompt == "n":
                    self._savefile(fmtdata, log)
                    return

        kwargsdict = ZynqSshClient.kwargsq.get()
        notes = input("Any notes to add? (press Enter if not)\n")
        kwargsdict["notes"] = notes

        with open(filename + ".fdf", "w") as savefile:
            savefile.write(str(kwargsdict))
            savefile.write("\n")
            for l1a in fmtdata:
                savefile.write(l1a.formatSave())
                savefile.write("\n")
        log.write("Saved data to file " + filename + ".fdf\n")
        print("Saved file as " + filename + ".fdf \n")
