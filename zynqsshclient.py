from paramiko import SSHClient, WarningPolicy
from os import system, remove
from sys import exit as sysexit
from queue import Queue
from format import fmt

# these make typing cccd commands a bit nicer since you don't have to type the quotes explicitly
Config = "Config"
Status = "Status"
Thresh1 = "Thresh1"
Thresh2 = "Thresh2"

Reg = "Reg"
L1a = "L1A"
SoftRst = "SoftRst"
BxRst = "BxRst"

Rd = "RD"
Wr = "WR"


# This class allows us to access a shell running on the Zynq from a Python script running on Ubuntu
# provides easy functions to call our C++ routines and other things
class ZynqSshClient(SSHClient):
    # This queue allows one way cross thread communication from here to the server receiving the data
    # It stores the arguments used to invoke l1arecv as as dict, so when l1arecv is called it throws a dict
    # into this queue.  When the server goes to save the fdf, it reads the dict out of this queue
    kwargsq = Queue()

    def __init__(self):
        super().__init__()
        self.set_missing_host_key_policy(WarningPolicy())
        # username for Zynq, pswd for Zynq, the Zynq's IP, and the port that it's SSH server is listening on
        self.username = "root"
        self.password = "root"
        self.ip = "169.254.27.144"
        self.port = 22
        self.persistpath = "/run/media/mmcblk0p1/save/"
        self.connect(self.ip, port=self.port, username=self.username, password=self.password)

    # A wrapper over paramiko's function that also detects errors and prints them out
    def runcmd(self, cmd):
        print("running command : " + cmd + "\n")
        ssh_stdin, ssh_stdout, ssh_stderr = self.exec_command(cmd)
        
        #print(" stdin   : " + ssh_stdin.readlines() + "\n")
        #print(" stdout  : " + ssh_stdout + "\n")
        #print(" stderr  : " + ssh_stderr + "\n")
        
        if len(list(ssh_stderr)) != 0:
            print("Error running command \"" + cmd + "\"! ", end="")
            print(ssh_stderr.readlines())
            # okay this is brutal but at current stage, stderr means something Very Bad (TM) happened
            sysexit(1)
        return ssh_stdin, ssh_stdout, ssh_stderr

    def cccd(self, cmd, rw=None, reg=None, chipid=None, payload=None, printresult=True):
        if cmd is not None and rw is None and reg is None and chipid is None and payload is None:
            result = self.runcmd(self.persistpath+"cccd.out {}".format(cmd))
        elif cmd is not None and rw is not None and reg is not None and chipid is not None and payload is None:
            result = self.runcmd(self.persistpath+"cccd.out {} {} {} {}".format(cmd, rw, reg, chipid, ))
        elif cmd is not None and rw is not None and reg is not None and chipid is not None and payload is not None:
            result = self.runcmd(self.persistpath+"cccd.out {} {} {} {} {}".format(cmd, rw, reg, chipid, payload))
        else:
            print("Invalid number of arguments given to cccd!  Ignoring")
            return -2

        if printresult:
            print("cccd invocation {} {} {} {} {} ".format(cmd, rw, reg, bin(chipid), payload), end="")
        output = result[1].readlines()
        if output[-1].strip() != "Exiting cleanly.":
            if printresult:
                print("failed")
            return -1

        if printresult:
            print("successful")

        if rw == Rd:
            return output[1].strip()
        else:
            return 0

    def l1arecv(self, l1as_to_send=11, lowthreshs=None, highthreshs=None):
        # if ya didn't specify one or both of these, we automatically make them for you
        if lowthreshs is None and highthreshs is None:
            lowthreshs = [0 for n in range(l1as_to_send)]
            highthreshs = [255 for n in range(l1as_to_send)]
        elif lowthreshs is not None and highthreshs is None:
            highthreshs = [255 for n in range(len(lowthreshs))]
        elif highthreshs is not None and lowthreshs is None:
            lowthreshs = [0 for n in range(len(highthreshs))]

        # Need the same number of both thresholds, and they are only 8 bits each
        if len(lowthreshs) != len(highthreshs):
            return -3
        if max(lowthreshs) > 255 or max(highthreshs) > 255:
            return -4

        # send the options we ran this with over to the TCP server
        self.kwargsq.put({"l1as_to_send": l1as_to_send, "lowthreshs": lowthreshs, "highthreshs": highthreshs})

        # Bit shift the low and high thresholds to the correct spots in the threshold register
        threshs = [(lowthreshs[n] << 8) | highthreshs[n] for n in range(len(lowthreshs))]

        # create a temporary threshs file here and scp it over to the Zynq, then remove it from here
        threshfilename = "threshs"
        with open(threshfilename, "w") as threshsfile:
            for thresh in threshs:
                threshsfile.write(str(thresh))
                threshsfile.write("\n")
        threshcp = system("sshpass -p \"{}\" scp {} {}@{}:{}".format(self.password, threshfilename, self.username,
                                                                     self.ip, self.persistpath))
        if threshcp != 0:
            print(fmt.RED+fmt.UNDERLINE+"FATAL: Failed to copy threshs file to Zynq.  Can you scp into the Zynq? "
                  "Is the Zynq in your known_hosts file?"+fmt.END)
            sysexit(threshcp)
        remove(threshfilename)

        # actually run the command and return 0 if it worked
        result = self.runcmd("cd {}; ./l1arecv.out {} {}".format(self.persistpath, l1as_to_send, threshfilename))
        if len(list(result[2])) != 0:
            return -1
        elif result[1].readlines()[-1].strip() == "Unmapping the axi slaves from memory...done":
            return 0
        else:
            return -2

    # Programs the FPGA with the bitstream on the SD card
    def buildpl(self, printresult=True):
        result = self.runcmd("cd {}pl; ./fpgaconfig.sh".format(self.persistpath))
        if len(list(result[2])) != 0:
            if printresult:
                print("Error occurred programming FPGA!")
                print(result[2].readlines())
            return 1
        elif "Successfully programmed fpga" in result[1].readlines()[-1]:
            print("FPGA successfully programmed")
            return 0
        else:
            if printresult:
                print("Unknown error occurred programming FPGA!")
            return 2
