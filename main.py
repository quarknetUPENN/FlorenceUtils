from datareception import *
import socketserver

with socketserver.TCPServer(('', 8080), ZynqTCPHandler) as server:
    server.serve_forever()
