from socketserver import StreamRequestHandler
from os.path import exists
from os import remove


class L1a:
    def __init__(self, dtmrocs, asdblrs, eventid, rawl1a, rawds):
        self.dtmrocs = dtmrocs
        self.asdblrs = asdblrs
        self.eventid = eventid
        self.rawl1a = rawl1a
        self.rawds = rawds

    def formatSave(self):
        return "L1a(" + str(self.dtmrocs) + ", " + \
               str(self.asdblrs) + ", " + \
               str(self.eventid) + ", " + \
               str(self.rawl1a) + ", \'" + \
               str(self.rawds) + "\')"


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


class ZynqTCPHandler(StreamRequestHandler):
    LogFileName = "ZynqTCPHandler.log"

    def __init__(self, request, client_address, server):
        super(ZynqTCPHandler, self).__init__(request, client_address, server)

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
                # format specifier to convert the number into binary, as a string
                reg[0] = '{0:032b}'.format(reg[0])
                ds += reg[0]

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
        return (fmtdata, len(set(badl1as)))

    def handle(self):
        log = open(self.LogFileName, "a")

        log.write("\nstarting run...")
        print("Run started, receiving data...", end="")

        rawdata = []
        while 1:
            line = self.rfile.readline().strip().decode("utf-8")

            if len(line) == 0:
                log.write("ignoring, partial line? " + line+"\n")
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
                    log.write("ignoring, middle of event? " + line+"\n")
                except SyntaxError:
                    log.write("ignoring, badly formatted value? " + line+"\n")
            else:
                log.write("ignoring, unrecognized line " + line+"\n")
        log.write("finished receiving data \n")
        fmtdata, badl1an = self._datafmter(rawdata, log)

        log.write("{} proper l1as received, {} bad ones \n".format(len(fmtdata), badl1an))
        print("{} proper l1as received, {} bad l1as, will save".format(len(fmtdata), badl1an))

        savedata = "["
        for l1a in fmtdata:
            savedata += l1a.formatSave()
            savedata += ","
        savedata = savedata[:-1]
        savedata += "]"

        self._savefile(savedata, log)

        log.close()

    # recursively saves file by asking user for a valid filename
    def _savefile(self, savedata, log):
        filename = input("Input filename to save data as. Leave blank to not save\t\t")
        if filename == "":
            log.write("user chose not to save data \n")
            print("Data not saved")
            return
        elif exists(filename + ".fdf"):
            if input("Warning!  File already exists.  Overwrite? (y/n)\t") != "y":
                self._savefile(savedata, log)
                return

        with open(filename + ".fdf", "w") as savefile:
            savefile.write(savedata)
            savefile.write("\n")
            with open("l1arecvkwargs.temp") as kwargsfile:
                savefile.write(kwargsfile.readline())
            remove("l1arecvkwargs.temp")
        log.write("Saved data to file " + filename + ".fdf\n")
        print("Saved file as " + filename + ".fdf \n")