import unittest
from unittest.mock import call, patch
from src import database
from src.container_thread import ContainerThread
from src.database import Database

class TestContainer(unittest.TestCase):
    
    @patch('logging.Logger.debug')
    def test_run(self,mock):
        cont = unittest.mock.Mock()
        cont.source = unittest.mock.Mock()
        cont.source.recv.side_effect=[bytes(i,'utf-8') for i in 'a']
        cont.dest = unittest.mock.Mock()
        cont.dest.recv.side_effect=[bytes(i,'utf-8') for i in 'b']
        cont.connection = unittest.mock.Mock()
        cont.container_config = {}
        cont.database = unittest.mock.Mock()

        ContainerThread._start_and_join_threads(cont)
        mock.assert_any_call('Joining thread2')