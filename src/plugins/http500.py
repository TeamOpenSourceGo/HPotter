import socketserver
import threading
from datetime import datetime

from hpotter.env import http500_server, write_db
from hpotter import tables

# remember to put name in __init__.py

Header = '''
HTTP/1.0 500 Internal Server Error
Date: {now}
Server: Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips mod_fcgid/2.3.9 PHP/5.4.16
Last-Modified: {now}
Cache-Control: max-age=0
Content-Type: text/html; charset=UTF-8

<html>
<head>
<title>500 Internal Server Error</title>
</head>
<body>
500 Internal Server Error
</body>
</html>
'''.format(now=datetime.now())

class HTTPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        connection = tables.Connections(
            sourceIP=self.client_address[0],
            sourcePort=self.client_address[1],
            destIP=self.server.server_address[0],
            destPort=self.server.server_address[1],
            proto=tables.TCP)
        write_db(connection)

        self.request.settimeout(30)

        try:
            data = self.request.recv(4096).decode("utf-8")
        except:
            return

        http = tables.HTTPCommands(request=data, connection=connection)
        write_db(http)

        self.request.sendall(Header.encode('utf-8'))

class HTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer): pass

def start_server():
    http_handler = HTTPHandler
    http500_server = HTTPServer(('0.0.0.0', 80), HTTPHandler)
    threading.Thread(target=http500_server.serve_forever).start()

def stop_server():
    if http500_server:
        http500_server.shutdown()
