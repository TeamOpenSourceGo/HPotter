import os
import platform
import docker
import re

from hpotter.tables import SQL, SQL_COMMAND_LENGTH
from hpotter.env import logger
from hpotter.plugins.generic import PipeThread

class Singletons():
    mariadb_container = None
    mariadb_thread = None

def rm_container():
    if Singletons.mariadb_container:
        logger.info('Stopping mariadb_container')
        Singletons.mariadb_container.stop()
        logger.info('Removing mariadb_container')
        Singletons.mariadb_container.remove()
        Singletons.mariadb_container = None
    else:
        logger.info('No mariadb_container to stop')

def start_server():
    try:
        client = docker.from_env()

        container = 'mariadb:latest'
        if platform.machine() == 'armv6l':
            container = 'apcheamitru/arm32v6-mariadb:latest'

        try:
            os.mkdir('tmp')
            os.mkdir('mysqld')
        except FileExistsError:
            pass
        except OSError as error:
            logger.info(error)
            return

        Singletons.mariadb_container = client.containers.run(container, \
            detach=True, ports={'3306/tcp': 33060}, \
            environment=['MYSQL_ALLOW_EMPTY_PASSWORD=yes'])
        logger.info('Created: %s', Singletons.mariadb_container)

    except OSError as err:
        logger.info(err)
        if Singletons.mariadb_container:
            logger.info(Singletons.mariadb_container.logs())
            rm_container()
        return

    di = lambda a: re.sub(b'([\x00-\x20]|[\x7f-\xff])+', b' ', a)
    Singletons.mariadb_thread = PipeThread(('0.0.0.0', 3306), \
        ('127.0.0.1', 33060), SQL, SQL_COMMAND_LENGTH, di=di)
    Singletons.mariadb_thread.start()

def stop_server():
    Singletons.mariadb_thread.request_shutdown()
    rm_container()
