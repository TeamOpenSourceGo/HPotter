import socket
import sys
import threading
from binascii import hexlify
import paramiko
from paramiko.py3compat import u, decodebytes
import _thread

from src import tables
from src.logger import logger

class SSHServer(paramiko.ServerInterface):
    undertest = False
    data = (
        b"AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp"
        b"fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC"
        b"KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT"
        b"UWT10hcuO4Ks8=")
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self, connection, database):
        self.event = threading.Event()
        self.connection = connection
        self.database = database

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # changed so that any username/password can be used
        if username and password:
            login = tables.Credentials(username=username, password=password, \
                connection=self.connection)
            self.database.write(login)

            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if username == 'exit':
            sys.exit(1)
        if(username == "user") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(self, username, \
        gss_authenticated=paramiko.AUTH_FAILED, cc_file=None):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(self, username, \
        gss_authenticated=paramiko.AUTH_FAILED, cc_file=None):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    # Turned off, causing problems
    def enable_auth_gssapi(self):
        return False

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    # pylint: disable=R0913
    def check_channel_pty_request(self, channel, term, width, height, \
        pixelwidth, pixelheight, modes):
        return True

class SshThread(threading.Thread):
    def __init__(self, source, connection, container_config, database):
        super(SshThread, self).__init__()
        self.client = source
        self.connection = connection
        self.chan = None
        self.database = database
        self.container_ip = self.container_port = None

    def run(self):
        self.database.write(self.connection)

        transport = paramiko.Transport(self.client)
        transport.load_server_moduli()

        # Experiment with different key sizes at:
        # http://travistidwell.com/jsencrypt/demo/
        host_key = paramiko.RSAKey(filename="RSAKey.cfg")
        transport.add_server_key(host_key)


        server = SSHServer(self.connection, self.database)
        transport.start_server(server=server)

        self.chan = transport.accept()
        if not self.chan:
            logger.info('no chan')
            return

        # TODO: run shell here
        self.chan.close()


    def stop(self):
        logger.info('ssh_thread shutting down')
        if self.chan:
            self.chan.close()
        try:
            _thread.exit()
        except SystemExit:
            pass