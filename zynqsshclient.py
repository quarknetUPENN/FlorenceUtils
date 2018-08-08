from paramiko import SSHClient, WarningPolicy

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


class ZynqSshClient(SSHClient):
    def __init__(self):
        super().__init__()
        self.set_missing_host_key_policy(WarningPolicy())
        self.connect("169.254.27.144", port=22, username="root", password="root")

    def runcmd(self, cmd):
        ssh_stdin, ssh_stdout, ssh_stderr = self.exec_command(cmd)
        if len(list(ssh_stderr)) != 0:
            print("Error running command \"" + cmd + "\"! ", end="")
            print(ssh_stderr.readlines())
        return ssh_stdin, ssh_stdout, ssh_stderr

    def cccd(self, cmd, rw=None, reg=None, chipid=None, payload=None):
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

        output = result[1].readlines()
        if output[-1].strip() != "Exiting cleanly.":
            return -1
        if rw == Rd:
            return output[1].strip()
        else:
            return 0

    def l1arecv(self, l1as_to_send = 11, lowthreshs = None, highthreshs = None):
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

        with open("l1arecvkwargs.temp", "w") as kwargssave:
            kwargssave.write(str({"l1as_to_send": l1as_to_send, "lowthreshs": lowthreshs, "highthreshs": highthreshs}))

        threshs = [(lowthreshs[n] << 8) | highthreshs[n] for n in range(len(lowthreshs))]

        result = self.runcmd(
            "/run/media/mmcblk0p1/save/l1arecv.out " + str(l1as_to_send) + "".join([" " + str(n) for n in threshs]))

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

