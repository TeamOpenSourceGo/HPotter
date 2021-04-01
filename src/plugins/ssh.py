import socket
import sys
import threading
from binascii import hexlify
import paramiko
from paramiko import SSHClient
from paramiko.py3compat import u, decodebytes
import _thread
import docker

from src import tables
from src.one_way_thread import OneWayThread
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
        self.user = None
        self.password = None

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # changed so that any username/password can be used
        if username and password:
            login = tables.Credentials(username=username, password=password, \
                connection=self.connection)
            self.user = username
            self.password = password
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
        self.source = source
        self.connection = connection
        self.container_config = container_config
        self.database = database
        self.chan = self.dest = None
        self.container = None
        self.user = self.password = None
        self.thread1 = self.thread2 = None

    def start_paramiko_server(self):
        transport = paramiko.Transport(self.source)
        transport.load_server_moduli()

        # Experiment with different key sizes at:
        # http://travistidwell.com/jsencrypt/demo/
        host_key = paramiko.RSAKey(filename="RSAKey.cfg")
        transport.add_server_key(host_key)

        server = SSHServer(self.connection, self.database)
        transport.start_server(server=server)

        self.chan = transport.accept()

        self.user = server.user
        self.password = server.password

    def create_container(self):
        d_client = docker.from_env()
        self.container = d_client.containers.run('debian:sshd', dns=['1.1.1.1'], detach=True)
        self.container.reload()

        self.container.exec_run('useradd -m -s /bin/bash '+self.user)
        self.container.exec_run('chpasswd '+self.user+':'+self.password)
        self.container.exec_run('usermod -aG sudo '+self.user)

    def _connect_to_container(self):
        container_ip = self.container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
        logger.debug(container_ip)

        ports = self.container.attrs['NetworkSettings']['Ports']
        assert len(ports) == 1

        for port in ports.keys():
            container_port = int(port.split('/')[0])
            container_protocol = port.split('/')[1]
        logger.debug(container_port)
        logger.debug(container_protocol)


        sshClient = SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            sshClient.connect(container_ip, port=container_port, username=self.user, password=self.password)
            self.dest = sshClient.get_transport().open_channel("session")
            self.dest.get_pty()
            self.dest.invoke_shell()

            logger.debug(self.dest)
        except:
            logger.info('unable to connect to ssh container')

    def _start_and_join_threads(self):
        logger.debug('Starting thread1')
        self.thread1 = OneWayThread(self.chan, self.dest, self.connection,
            self.container_config, 'request', self.database)
        self.thread1.start()

        logger.debug('Starting thread2')
        self.thread2 = OneWayThread(self.dest, self.chan, self.connection,
            self.container_config, 'response', self.database)
        self.thread2.start()

        logger.debug('Joining thread1')
        self.thread1.join()
        logger.debug('Joining thread2')
        self.thread2.join()

    def run(self):
        self.database.write(self.connection)

        self.start_paramiko_server()
        if not self.chan:
            logger.info('no chan')
            return

        self.create_container()
        self._connect_to_container()
        
        if self.chan and self.dest:
            self._start_and_join_threads()
        
        self._stop_and_remove()

    def _stop_and_remove(self):
        if self.chan:
            self.chan.close()
        if self.dest:
            self.dest.close()
        
        logger.debug(str(self.container.logs()))
        logger.info('Stopping: %s', self.container)
        self.container.stop()
        logger.info('Removing: %s', self.container)
        self.container.remove()

    def shutdown(self):
        ''' Called to shutdown the one-way threads and stop and remove the
        container. Called externally in response to a shutdown request. '''
        self.thread1.shutdown()
        self.thread2.shutdown()
        self._stop_and_remove()