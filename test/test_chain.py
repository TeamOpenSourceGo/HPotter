import unittest
import iptc
from unittest.mock import call, patch
from src.chain import *

table = iptc.Table(iptc.Table.FILTER)

class TestChain(unittest.TestCase):
    def setup(self):
        pass
    def tearDown(self):
        pass

    def test_create_hpotter_chains(self):
        flush_chains()
        create_hpotter_chains()
        for name in ['hpotter_input','hpotter_output','hpotter_forward']: 
            if iptc.is_table_available(iptc.Table.FILTER):
                self.assertTrue( table.is_chain(name) )
    
    def test_add_drop_rules(self):
        add_drop_rules()
        #check for drop rules in hpotter chains
        for chain in hpotter_chains:
            self.assertTrue(iptc.easy.has_rule('filter', chain.name, drop_rule))
        
        #check for targets to hpotter chains in builtins
        for chain, rule_d in zip(builtin_chains, hpotter_chain_rules):
            self.assertTrue(iptc.easy.has_rule('filter', chain.name, rule_d))

    def test_create_listen_rules(self):
        thread_mock = unittest.mock.Mock()
        thread_mock.listen_port = '33000'
        create_listen_rules(thread_mock)
        proto = 'tcp'
        rule_i = { \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'dport': thread_mock.listen_port} \
        }
        rule_o = { \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'sport': thread_mock.listen_port} \
        }
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', rule_i) )
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', rule_o) )

    def test_create_container_rules(self):
        cont_mock = unittest.mock.Mock()
        cont_mock.container_protocol = 'tcp'
        cont_mock.container_gateway = "71.88.115.9"
        cont_mock.container_ip = "192.188.72.83"
        cont_mock.container_port = 202
        create_container_rules(cont_mock)
        source = cont_mock.container_gateway
        dest = cont_mock.container_ip
        proto = cont_mock.container_protocol
        port = str(cont_mock.container_port)
        rule_t = { \
                'src': source, \
                'dst': dest, \
                'target': 'ACCEPT', \
                'protocol': proto, \
                proto: {'dport': port} \
        }
        rule_f = { \
                'src': dest, \
                'dst': source, \
                'target': 'ACCEPT', \
                'protocol': proto, \
                proto: {'sport': port} \
        }
        drop = { \
                'src': dest, \
                'dst': '!'+source+'/16', \
                'target': 'DROP', \
        }
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', rule_t) )
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', rule_f) )
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', drop) )
        