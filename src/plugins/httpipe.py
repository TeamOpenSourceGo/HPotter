import os
import platform
import docker

from hpotter.tables import HTTPCommands, HTTP_COMMAND_LENGTH
from hpotter.env import logger
from hpotter.plugins.generic import PipeThread

class Singletons():
    httpd_container = None
    httpd_thread = None

def rm_container():
    if Singletons.httpd_container:
        logger.info('Stopping httpd_container')
        Singletons.httpd_container.stop()
        logger.info('Removing httpd_container')
        Singletons.httpd_container.remove()
        Singletons.httpd_container = None
    else:
        logger.info('No httpd_container to stop')

def start_server():
    try:
        client = docker.from_env()

        container = 'httpd:latest'
        if platform.machine() == 'armv6l':
            container = 'arm32v6/httpd:alpine'

        try:
            os.mkdir('apache2')
        except FileExistsError:
            pass
        except OSError as error:
            logger.info(error)
            return

        Singletons.httpd_container = client.containers.run(container, \
            detach=True, ports={'80/tcp': 8080}, read_only=True, \
            volumes={'apache2': \
                {'bind': '/usr/local/apache2/logs', 'mode': 'rw'}})
        logger.info('Created: %s', Singletons.httpd_container)
        # Can't close the bridge because we need it to connect to the
        # container.

    except OSError as err:
        logger.info(err)
        if Singletons.httpd_container:
            logger.info(Singletons.httpd_container.logs())
            rm_container()
        return

    Singletons.httpd_thread = PipeThread(('0.0.0.0', 80), \
        ('127.0.0.1', 8080), HTTPCommands, HTTP_COMMAND_LENGTH)
    Singletons.httpd_thread.start()

def stop_server():
    if Singletons.httpd_container is not None:
        Singletons.httpd_thread.request_shutdown()
    rm_container()
