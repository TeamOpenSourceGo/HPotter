''' Start and stop a connection to a database, creating one if necessary.  '''

import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database

from src.tables import Base
from src.logger import logger

db_thread_lock = threading.Lock()

class Database():
    ''' Read from the config.yml file (if it exists) and set up the
    database connection. '''
    def __init__(self, config):
        self.config = config
        self.lock_needed = False
        self.engine = None

    def _get_database_string(self):
        database = self.config.get('database', 'sqlite')
        database_name = self.config.get('database_name', 'hpotter.db')

        if database != 'sqlite':
            database_user = self.config.get('database_user', '')
            database_password = self.config.get('database_password', '')
            database_host = self.config.get('database_host', '')
            database_port = self.config.get('database_port', '')

            # this is a little tricky as some are optional, but if they
            # are present they must be prefixed.
            database_password = ':' + database_password if database_password else ''
            database_port = ':' + database_port if database_port else ''
            database_name = '/' + database_name if database_name else ''

            return '{0}://{1}{2}@{3}{4}{5}'.format(database, database_user,
                database_password, database_host, database_port, database_name)

        self.lock_needed = True
        return 'sqlite:///' + database_name

    def write(self, table):
        ''' Write into the database, with locking if necessary. '''
        session = scoped_session(sessionmaker(self.engine))()
        if self.lock_needed:
            with db_thread_lock:
                session.add(table)
                session.commit()
                session.close()
        else:
            session.add(table)
            session.commit()
            session.close()

    def open(self):
        ''' Open the connection. '''
        logger.debug('Opening db')
        self.engine = create_engine(self._get_database_string())
        # engine = create_engine(db, echo=True)

        # https://stackoverflow.com/questions/6506578/how-to-create-a-new-database-using-sqlalchemy
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

        Base.metadata.create_all(self.engine)

    def close(self):
        ''' Close the connection. '''
        logger.debug('Closing db')
        # self.session.commit()
        # self.session.close()
