import iptc
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

hpotter_input_chain = filter_table.create_chain("hpotter_input")
hpotter_output_chain = filter_table.create_chain("hpotter_output")
hpotter_forward_chain = filter_table.create_chain("hpotter_forward")
hpotter_chains = [hpotter_input_chain, hpotter_output_chain, hpotter_forward_chain]

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

def delete_drop_rules():
    for rule_d, chain in zip(hpotter_chain_rules, builtin_chains):
        iptc.easy.delete_rule('filter', chain.name, rule_d)

    for chain in hpotter_chains:
        chain.flush()

    for chain in hpotter_chains:
        chain.delete()

def create_listen_rules(obj):
    proto = "tcp"

    obj.to_rule = { \
        'target': 'ACCEPT', \
        'protocol': proto, \
        proto: {'dport': str(obj.listen_port)} \
    }
    logger.debug(obj.to_rule)
    iptc.easy.insert_rule('filter', 'hpotter_input', obj.to_rule)

    obj.from_rule = { \
        'target': 'ACCEPT', \
        'protocol': proto, \
        proto: {'sport': str(obj.listen_port)} \
    }
    logger.debug(obj.from_rule)
    iptc.easy.insert_rule('filter', 'hpotter_output', obj.from_rule)


def delete_listen_rules(obj):
    logger.debug('Removing rules')

    iptc.easy.delete_rule('filter', "hpotter_input", obj.to_rule)
    iptc.easy.delete_rule('filter', "hpotter_output", obj.from_rule)

def create_container_rules(obj):
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

def delete_container_rules(obj):
    logger.debug('Removing rules')

    iptc.easy.delete_rule('filter', "hpotter_output", obj.to_rule)
    iptc.easy.delete_rule('filter', "hpotter_input", obj.from_rule)
    iptc.easy.delete_rule('filter', "hpotter_input", obj.drop_rule)

def add_connection_rules():
    iptc.easy.insert_rule('filter', 'OUTPUT', cout_rule)
    iptc.easy.insert_rule('filter', 'INPUT', cin_rule)

def delete_connection_rules():
    iptc.easy.delete_rule('filter', "OUTPUT", cout_rule)
    iptc.easy.delete_rule('filter', "INPUT", cin_rule)

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
    iptc.easy.insert_rule('filter', 'INPUT', rej_d)

    # mulitple private ip ranges
    # 10.0.0.0/8
    # 172.16.0.0/12
    # 192.168.0.0/16
    lan_d = { \
            'src':'192.168.0.0/16', \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
    }
    logger.debug(lan_d)
    ssh_rules.insert(0, lan_d)
    iptc.easy.insert_rule('filter', 'INPUT', lan_d)

    local_d = { \
            'src':'127.0.0.0/8', \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
    }
    logger.debug(local_d)
    ssh_rules.insert(0, local_d)
    iptc.easy.insert_rule('filter', 'INPUT', local_d)

def delete_ssh_rules():
    for dict in ssh_rules:
        iptc.easy.delete_rule('filter', 'INPUT', dict)

def add_dns_rules():
    logger.debug(dns_in)
    iptc.easy.insert_rule('filter', 'INPUT', dns_in)

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
        iptc.easy.insert_rule('filter', 'OUTPUT', dns_out)

def delete_dns_rules():
    iptc.easy.delete_rule('filter', "INPUT", dns_in)
    for dict in dns_list:
        iptc.easy.delete_rule('filter', "OUTPUT", dict)
    
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
