OneWayThread import socket
import threading

from hpotter import tables
from hpotter.env import logger, write_db

# read and write between two sockets with a possible upper limit. write to
# db if table passed in.
class OneWayThread(threading.Thread):
    def __init__(self, source, dest, table=None, limit=0):
        super().__init__()
        self.source = source
        self.dest = dest
        self.table = table
        self.limit = limit

        if self.table:
            self.connection = tables.Connections(
                sourceIP=self.source.getsockname()[0],
                sourcePort=self.source.getsockname()[1],
                destIP=self.dest.getsockname()[0],
                destPort=self.dest.getsockname()[1],
                proto=tables.TCP)
            write_db(self.connection)

    def exceptions(function):
        try:
            return function()
        except socket.timeout as timeout:
            logger.debug(timeout)
            raise Exception
        except socket.error as error:
            logger.debug(error)
            raise Exception
        except Exception as exc:
            logger.debug(exc)
            raise Exception

    def run(self):
        total = b''
        while 1:
            try:
                data = exceptions(lambda: self.source.recv(4096))
            except Exception:
                break

            if data == b'' or not data:
                break

            if self.table or self.limit > 0:
                total += data

            try:
                exceptions(lambda: self.dest.sendall(data))
            except Exception:
                break

            if self.limit > 0 and len(total) >= self.limit:
                break

        if self.table:
            http = self.table(request=str(total), connection=self.connection)
            write_db(http)
