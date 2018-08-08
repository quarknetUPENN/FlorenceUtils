from paramiko import SSHClient, WarningPolicy
from os import system, remove
from queue import Queue

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
    kwargsq = Queue()

    def __init__(self):
        super().__init__()
        self.set_missing_host_key_policy(WarningPolicy())
        self.username = "root"
        self.password = "root"
        self.ip = "169.254.27.144"
        self.port = 22
        self.connect(self.ip, port=self.port, username=self.username, password=self.password)

    def runcmd(self, cmd):
        ssh_stdin, ssh_stdout, ssh_stderr = self.exec_command(cmd)
        if len(list(ssh_stderr)) != 0:
            print("Error running command \"" + cmd + "\"! ", end="")
            print(ssh_stderr.readlines())
        return ssh_stdin, ssh_stdout, ssh_stderr

    def cccd(self, cmd, rw=None, reg=None, chipid=None, payload=None, printresult=True):
        if cmd is not None and rw is None and reg is None and chipid is None and payload is None:
            result = self.runcmd("/run/media/mmcblk0p1/save/cccd.out {}".format(cmd))
        elif cmd is not None and rw is not None and reg is not None and chipid is not None and payload is None:
            result = self.runcmd("/run/media/mmcblk0p1/save/cccd.out {} {} {} {}".format(cmd, rw, reg, chipid, ))
        elif cmd is not None and rw is not None and reg is not None and chipid is not None and payload is not None:
            result = self.runcmd(
                "/run/media/mmcblk0p1/save/cccd.out {} {} {} {} {}".format(cmd, rw, reg, chipid, payload))
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
        if lowthreshs is None and highthreshs is None:
            lowthreshs = [0 for n in range(l1as_to_send)]
            highthreshs = [255 for n in range(l1as_to_send)]
        elif lowthreshs is not None and highthreshs is None:
            highthreshs = [255 for n in range(len(lowthreshs))]
        elif highthreshs is not None and lowthreshs is None:
            lowthreshs = [0 for n in range(len(highthreshs))]

        if len(lowthreshs) != len(highthreshs):
            return -3
        if max(lowthreshs) > 255 or max(highthreshs) > 255:
            return -4

        self.kwargsq.put({"l1as_to_send": l1as_to_send, "lowthreshs": lowthreshs, "highthreshs": highthreshs})

        threshs = [(lowthreshs[n] << 8) | highthreshs[n] for n in range(len(lowthreshs))]

        with open("threshs", "w") as threshsfile:
            for thresh in threshs:
                threshsfile.write(str(thresh))
                threshsfile.write("\n")
        system('sshpass  -p "{}" scp threshs {}@{}:/run/media/mmcblk0p1/save/'.format(self.password, self.username, self.ip))
        remove("threshs")

        result = self.runcmd("cd /run/media/mmcblk0p1/save; ./l1arecv.out " + str(l1as_to_send) + " threshs")

        if len(list(result[2])) != 0:
            return -1
        elif result[1].readlines()[-1].strip() == "Unmapping the axi slaves from memory...done":
            return 0
        else:
            return -2

    def buildpl(self):
        result = self.runcmd("cd /run/media/mmcblk0p1/save/pl; ./fpgaconfig.sh")
        if len(list(result[2])) != 0:
            return 1
        elif "Successfully programmed fpga" in result[1].readlines()[-1]:
            return 0
        else:
            return 2
