import socket, ssl
from datetime import datetime

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

def start_server():
    bindsocket = socket.socket()
    bindsocket.bind(('127.0.0.1', 4443))
    bindsocket.listen(5)

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="cert.pem")

    while True:
        newsocket, fromaddr = bindsocket.accept()
        connstream = context.wrap_socket(newsocket, server_side=True)
        try:
            data = connstream.recv(1024)
            connstream.write(Header.encode('utf-8'))
        finally:
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()

def stop_server():
    pass
