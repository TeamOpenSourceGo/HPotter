import unittest
import signal
from unittest.mock import mock_open, call, patch
from src.__main__ import HP, GracefulKiller

class TestMain(unittest.TestCase):
    def setup(self):
        pass
    def tearDown(self):
        pass

    @patch('logging.Logger.info')
    def test_startup(self, mock):
        hp = HP()
        hp.startup()
        mock.assert_any_call('Creating SSL configuration files')
        hp.shutdown()
    
    @patch('logging.Logger.info')
    def test_exit_gracefully(self, mock):
        killer = GracefulKiller()
        killer.exit_gracefully(3, 5)
        mock.assert_called_with('In exit_gracefully')


        
