from datareception import *
from zynqsshclient import *
import socketserver
from threading import Thread
from readfdf import showLastFdf

server = socketserver.TCPServer(('', 8080), ZynqTCPHandler)

ssh = ZynqSshClient()

print(ssh.cccd(Reg, Wr, Config, 0b111111, 1))


def getl1as():
    if ssh.l1arecv(l1as_to_send=100, lowthreshs=list(range(0, 150, 10))) != 0:
        ssh.close()
        server.server_close()
        quit()


t = Thread(target=getl1as)
t.start()


server.handle_request()


ssh.close()
server.server_close()


showLastFdf(usePrint=False)