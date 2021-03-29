<<<<<<< HEAD
OneWayThread import socket
=======
import socket
>>>>>>> e5484a776a396c2272c04ac193f06c389276e1ce
import threading

from src import tables
from src import logger
from src.database import database

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
            database.write(self.connection)

    def exceptions(self, function):
        try:
            return function()
        except socket.timeout as timeout:
            logger.debug(timeout)
            raise CustomError("Socket timeout").
        except socket.error as error:
            logger.debug(error)
            raise Exception(error)
        except Exception as exc:
            logger.debug(exc)
            raise Exception(exc)

    def run(self):
        total = b''
        while 1:
            try:
                data = exceptions(lambda data = data: self.source.recv(4096))
            except Exception:
                break

            if data == b'' or not data:
                break

            if self.table or self.limit > 0:
                total += data

            try:
                exceptions(lambda eData = data: self.dest.sendall(eData))
            except Exception:
                break

            if self.limit > 0 and len(total) >= self.limit:
                break

        if self.table:
            http = self.table(request=str(total), connection=self.connection)
            database.write(http)
