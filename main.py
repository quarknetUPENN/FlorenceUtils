from datareception import *
from zynqsshclient import *
from socketserver import TCPServer
from threading import Thread
from readfdf import showLastFdf

server = TCPServer(('', 8080), ZynqTCPHandler)
ssh = ZynqSshClient()


ssh.cccd(Reg, Wr, Config, 0b111111, 1)


t = Thread(target=server.handle_request)
t.start()

ssh.l1arecv(l1as_to_send=1,
            lowthreshs=list(sum([[n for j in range(10)] for n in range(40,150,5)], [])),
            highthreshs=None)

t.join()
ssh.close()
server.server_close()


showLastFdf(useprint=False)
