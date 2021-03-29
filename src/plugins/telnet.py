import socketserver
import threading

from hpotter import tables
from hpotter.tables import CREDS_LENGTH
from hpotter import logger
from hpotter.env import logger, write_db, telnet_server
from hpotter.docker_shell.shell import fake_shell, get_string

# https://docs.python.org/3/library/socketserver.html
class TelnetHandler(socketserver.BaseRequestHandler):

    def creds(self, prompt):
        logger.debug('Getting creds')
        tries = 0
        response = ''
        while response == '':
            self.request.sendall(prompt)

            logger.debug('Before creds get_string')
            response = get_string(self.request, limit=CREDS_LENGTH, telnet=True)

            tries += 1
            if tries > 2:
                logger.debug('Creds no response')
                raise IOError('no response')

        logger.debug('Creds returning %s', response)
        return response

    def handle(self):
        self.request.settimeout(30)

        connection = tables.Connections(
            sourceIP=self.client_address[0],
            sourcePort=self.client_address[1],
            destIP=self.server.socket.getsockname()[0],
            destPort=self.server.socket.getsockname()[1],
            proto=tables.TCP)
        write_db(connection)

        try:
            username = self.creds(b'Username: ')
            password = self.creds(b'Password: ')
        except Exception as exception:
            logger.debug(exception)
            self.request.close()
            return
        logger.debug('After creds')

        creds = tables.Credentials(username=username, password=password, \
            connection=connection)
        write_db(creds)

        self.request.sendall(b'Last login: Mon Nov 20 12:41:05 2017 from 8.8.8.8\n')

        prompt = b'\n$: ' if username in ('root', 'admin') else b'\n#: '
        try:
            fake_shell(self.request, connection, prompt, telnet=True)
        except Exception as exc:
            logger.debug(type(exc))
            logger.debug(exc)
            logger.debug('telnet fake_shell threw exception')

        self.request.close()
        logger.debug('telnet handle finished')

class TelnetServer(socketserver.ThreadingMixIn, socketserver.TCPServer): pass

def start_server():
    global telnet_server
    telnet_handler = TelnetHandler
    telnet_server = TelnetServer(('0.0.0.0', 23), telnet_handler)
    threading.Thread(target=telnet_server.serve_forever).start()

def stop_server():
    if telnet_server:
        telnet_server.shutdown()
