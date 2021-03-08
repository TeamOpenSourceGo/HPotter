from logging import error
import iptc
import socket
import threading
import ipaddress
import socket

from src.logger import logger

# here's the idea. create hpotter chains that mirror the three builtins. add
# drop rules at the end of the hpotter chains. insert a target of each of
# the hpotter chains at the beginning of the builtin chains. this
# overwrites whatever was there. make the process reversable so that we can
# put it back the way it was.

# can only set policies in builtin chains

filter_table = iptc.Table(iptc.Table.FILTER)

input_chain = iptc.Chain(filter_table, 'INPUT')
output_chain = iptc.Chain(filter_table, 'OUTPUT')
forward_chain = iptc.Chain(filter_table, 'FORWARD')
builtin_chains = [input_chain, output_chain, forward_chain]

hpotter_chains = []
hpotter_chain_names = ['hpotter_input', 'hpotter_output', 'hpotter_forward']
    
hpotter_chain_rules = []

drop_rule = { 'target': 'DROP' }

cout_rule = { \
        'target': 'ACCEPT', \
        'match': 'state', \
        'state': 'NEW,ESTABLISHED,RELATED'
}

cin_rule = { \
        'target': 'ACCEPT', \
        'match': 'state', \
        'state': 'ESTABLISHED,RELATED'
}

dns_in = { \
        'dst': '127.0.0.53', \
        'target': 'ACCEPT', \
        'protocol': 'udp', \
        'udp': {'dport': '53'} \
}

dns_list = []
ssh_rules = []

thread_lock = threading.Lock()

def add_drop_rules():
    # append drop to all hpotter chains
    for chain in hpotter_chains:
        iptc.easy.add_rule('filter', chain.name, drop_rule)

    # create target for all hpotter chains
    for chain in hpotter_chains:
        rule_d = { 'target' : chain.name }
        hpotter_chain_rules.append( rule_d )

    # make the hpotter chains the target for all builtin chains
    for rule_d, chain in zip(hpotter_chain_rules, builtin_chains):
        iptc.easy.insert_rule('filter', chain.name, rule_d)

def create_listen_rules(obj):
    thread_lock.acquire()

    listen_address = obj.listen_address
    if len(listen_address) == 0 or listen_address == '0.0.0.0':
        listen_address = '0.0.0.0/0'

    proto = "tcp"

    obj.to_rule = { \
        'dst': listen_address, \
        'target': 'ACCEPT', \
        'protocol': proto, \
        proto: {'dport': str(obj.listen_port)} \
    }
    logger.debug(obj.to_rule)
    iptc.easy.insert_rule('filter', 'hpotter_input', obj.to_rule)

    obj.from_rule = { \
        'src': listen_address, \
        'target': 'ACCEPT', \
        'protocol': proto, \
        proto: {'sport': str(obj.listen_port)} \
    }
    logger.debug(obj.from_rule)
    iptc.easy.insert_rule('filter', 'hpotter_output', obj.from_rule)

    thread_lock.release()

def create_container_rules(obj):
    thread_lock.acquire()
    
    proto = obj.container_protocol.lower()
    source_addr = obj.container_gateway
    dest_addr = obj.container_ip
    dstport = str(obj.container_port)

    obj.to_rule = { \
            'src': source_addr, \
            'dst': dest_addr, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'dport': dstport} \
    }
    logger.debug(obj.to_rule)
    iptc.easy.insert_rule('filter', 'hpotter_output', obj.to_rule)

    obj.from_rule = { \
            'src': dest_addr, \
            'dst': source_addr, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'sport': dstport} \
    }
    logger.debug(obj.from_rule)
    iptc.easy.insert_rule('filter', 'hpotter_input', obj.from_rule)

    obj.drop_rule = { \
        'src': dest_addr, \
        'dst': '!' + source_addr + "/16", \
        'target': 'DROP' \
    }
    logger.debug(obj.drop_rule)
    iptc.easy.insert_rule('filter', 'hpotter_input', obj.drop_rule)

    thread_lock.release()

def delete_container_rules(obj):
    thread_lock.acquire()

    logger.debug('Removing rules')

    iptc.easy.delete_rule('filter', "hpotter_output", obj.to_rule)
    iptc.easy.delete_rule('filter', "hpotter_input", obj.from_rule)
    iptc.easy.delete_rule('filter', "hpotter_input", obj.drop_rule)

    thread_lock.release()

def add_connection_rules():
    iptc.easy.insert_rule('filter', 'hpotter_output', cout_rule)
    iptc.easy.insert_rule('filter', 'hpotter_input', cin_rule)

def add_ssh_rules(): #allow LAN/LocalHost IPs, reject all others
    proto = 'tcp'
    port = '22'

    rej_d = { \
            'target': 'DROP', \
            'protocol': proto, \
            proto :{'dport':port} \
    }
    logger.debug(rej_d)
    ssh_rules.insert(0, rej_d)
    iptc.easy.insert_rule('filter', 'hpotter_input', rej_d)

    subnet = get_host_subnet()
    lan_d = { \
            'src': subnet, \
            'dst': host_ip, \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
    }
    logger.debug(lan_d)
    ssh_rules.insert(0, lan_d)
    iptc.easy.insert_rule('filter', 'hpotter_input', lan_d)

    local_d = { \
            'src':'127.0.0.0/8', \
            'dst':'127.0.0.0/8', \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
    }
    logger.debug(local_d)
    ssh_rules.insert(0, local_d)
    iptc.easy.insert_rule('filter', 'hpotter_input', local_d)

def get_host_subnet():
    masks = ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
    dfalt = '127.0.0.0/8'
    for subnet in masks:
        if ipaddress.ip_address(host_ip) in ipaddress.ip_network(subnet):
            return subnet
    return dfalt
    
def add_dns_rules():
    logger.debug(dns_in)
    iptc.easy.insert_rule('filter', 'hpotter_input', dns_in)

    #/etc/resolv.conf may contain more than one server
    servers = get_dns_servers()
    for server in servers:
        dns_out = { \
                'dst': server, \
                'target':'ACCEPT', \
                'protocol':'udp', \
                'udp': {'dport': '53'} \
        }
        dns_list.insert(0, dns_out)
        logger.debug(dns_out)
        iptc.easy.insert_rule('filter', 'hpotter_output', dns_out)
    
# credit to James John: https://github.com/donjajo/py-world/blob/master/resolvconfReader.py
def get_dns_servers():
    resolvers = []
    try:
        with open ('/etc/resolv.conf', 'r') as resolvconf:
            for line in resolvconf.readlines():
                line = line.split('#', 1)[0]
                line = line.rstrip()
                if 'nameserver' in line:
                    resolvers.append( line.split()[1] )

        return resolvers
    except IOError as error:
        return error.strerror

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(('1.1.1.1', 0))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


host_ip = get_host_ip()


def create_hpotter_chains():
    for name in hpotter_chain_names:
        hpotter_chain = iptc.Chain(filter_table, name)

        if not iptc.easy.has_chain('filter', name):
            hpotter_chain = filter_table.create_chain(name)

        if not hpotter_chain in hpotter_chains:
            hpotter_chains.append(hpotter_chain)

def flush_chains():
    for chain, name in zip(builtin_chains, hpotter_chain_names):
        if iptc.easy.has_chain('filter', name):

            #delete hpotter rules in builtins if they exist
            if iptc.easy.has_rule('filter', chain.name, {'target':name}):
                iptc.easy.delete_rule('filter', chain.name, {'target':name})

            #delete hpotter chains if they exist
            iptc.easy.flush_chain('filter', name)
            iptc.easy.delete_chain('filter', name)