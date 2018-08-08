from datareception import *
from zynqsshclient import *
from socketserver import TCPServer
from threading import Thread
from readfdf import showLastFdf

server = TCPServer(('', 8080), ZynqTCPHandler)
ssh = ZynqSshClient()

ssh.cccd(Reg, Wr, Config, 0b111111, 1)
ssh.l1arecv(l1as_to_send=1,
            lowthreshs=list(sum([[n for j in range(1)] for n in range(40,150,5)], [])),
            highthreshs=None)

t = Thread(target=server.handle_request())
t.start()


ssh.close()
server.server_close()


showLastFdf(useprint=False)
