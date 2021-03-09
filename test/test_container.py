import unittest
from unittest.mock import call, patch
from src import database
from src.container_thread import ContainerThread

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

    def test_init(self):
        source = unittest.mock.Mock()
        source.recv.side_effect=[bytes(i,'utf-8') for i in 'a']
        connection = unittest.mock.Mock()
        database = unittest.mock.Mock()

        ct = ContainerThread(source, connection, {}, database)
        self.assertEqual(ct.container_gateway, None)
        self.assertEqual(ct.container_ip, None)
        self.assertEqual(ct.container_port, None)
        self.assertEqual(ct.container_protocol, None)
        self.assertEqual(ct.dest, None)
        self.assertEqual(ct.thread1, None)
        self.assertEqual(ct.thread2, None)
        self.assertEqual(ct.container, None)
        self.assertEqual(ct.to_rule, None)
        self.assertEqual(ct.from_rule, None)