import unittest
import iptc
from src.chain import *
unittest.TestLoader.sortTestMethodsUsing = None

table = iptc.Table(iptc.Table.FILTER)

class TestChain(unittest.TestCase):
    def setup(self):
        pass
    def tearDown(self):
        pass

    def test01_create_hpotter_chains(self):
        #flush_chains()
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
        thread_mock.listen_address = '192.168.12.15'
        thread_mock.listen_port = 33000
        create_listen_rules(thread_mock)
        proto = 'tcp'
        rule_i = { \
            'dst': thread_mock.listen_address, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'dport': str(thread_mock.listen_port)} \
        }
        rule_o = { \
            'src': thread_mock.listen_address, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'sport': str(thread_mock.listen_port)} \
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

        cont_mock.to_rule = rule_t
        cont_mock.from_rule = rule_f
        cont_mock.drop_rule = drop
        delete_container_rules(cont_mock)
        self.assertTrue(not iptc.easy.has_rule('filter', 'hpotter_output', rule_t) )
        self.assertTrue(not iptc.easy.has_rule('filter', 'hpotter_input', rule_f) )
        self.assertTrue(not iptc.easy.has_rule('filter', 'hpotter_input', drop) )

    def test_add_connection_rules(self):
        out = { \
            'target': 'ACCEPT', \
            'match': 'state', \
            'state': 'NEW,ESTABLISHED,RELATED'
        }
        inr = { \
            'target': 'ACCEPT', \
            'match': 'state', \
            'state': 'ESTABLISHED,RELATED'
        }
        add_connection_rules()
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', inr))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', out))
        
    def test_add_ssh_rules(self):
        proto = 'tcp'
        port = '22'
        host_ip = get_host_ip()
        rej = { \
            'target': 'DROP', \
            'protocol': proto, \
            proto :{'dport':port} \
        }
        lan = { \
            'src':'10.0.0.0/16', \
            'dst': host_ip, \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
        }
        lcl = { \
            'src':'127.0.0.0/8', \
            'dst':'127.0.0.0/8', \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
        }
        add_ssh_rules()
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', rej))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', lan))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', lcl))
    
    def test_add_dns_rules(self):
        servers = get_dns_servers()
        out_rules = []
        d_in = { \
            'dst':'127.0.0.53', \
            'target':'ACCEPT', \
            'protocol':'udp', \
            'udp':{'dport':'53'} \
        }
        for server in servers:
            rule = { \
                    'dst': server, \
                    'target':'ACCEPT', \
                    'protocol':'udp', \
                    'udp': {'dport': '53'} \
            }
            out_rules.append(rule)
        add_dns_rules()
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', d_in))
        for rule in out_rules:
            self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', rule))
    
    def test_flush(self):
        flush_chains()
        for chain,name in zip(builtin_chains, hpotter_chain_names):
            rule = {'target': name}
            self.assertTrue(not iptc.easy.has_rule('filter', chain.name, rule))
        self.assertTrue(not iptc.easy.has_chain('filter', 'hpotter_output'))
        self.assertTrue(not iptc.easy.has_chain('filter', 'hpotter_input'))
        self.assertTrue(not iptc.easy.has_chain('filter', 'hpotter_forward'))
        
        