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
