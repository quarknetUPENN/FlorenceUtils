from datareception import *
from zynqsshclient import *
from socketserver import TCPServer
from threading import Thread
from readfdf import showLastFdf
from os import popen

# Check to make sure that Ubuntu's IP address is configured correctly
with popen('ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1') as f:
    if f.readline().strip() != "169.254.27.143":
        print(fmt.RED+fmt.UNDERLINE+"FATAL: IP address on Ubuntu configured incorrectly"+fmt.END)
        print("Try running configip.sh")
        exit(1)

server = TCPServer(('', 8080), ZynqTCPHandler)

try:
    ssh = ZynqSshClient()
except BaseException as e:
    print(e)
    server.server_close()
    exit(1)

try:
    ssh.buildpl()
    ssh.cccd(Reg, Wr, Config, 0b111111, 5)

    t = Thread(target=server.handle_request)
    t.start()

    ssh.l1arecv(l1as_to_send=1,
                lowthreshs=list(sum([[n for j in range(2)] for n in range(40,150,5)], [])),
                highthreshs=None)

    t.join()
finally:
    print("Closing down connections")
    ssh.close()
    server.server_close()
    print("Closed down connections")


showLastFdf()
