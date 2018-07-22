#!/usr/bin/python

"""
Example network of Quagga routers
(QuaggaTopo + QuaggaService)
"""

import sys
import atexit

# patch isShellBuiltin
import mininet.util
import mininext.util
mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules['mininet.util'] = mininet.util

from mininet.util import dumpNodeConnections
from mininet.node import OVSController
from mininet.log import setLogLevel, info

from mininext.cli import CLI
from mininext.net import MiniNExT

from topo import QuaggaTopo

net = None


def startNetwork():
    "instantiates a topo, then starts the network and prints debug information"

    info('** Creating Quagga network topology\n')
    topo = QuaggaTopo()

    info('** Starting the network\n')
    global net
    net = MiniNExT(topo, controller=OVSController)
    net.start()

    info('** Dumping host connections\n')
    dumpNodeConnections(net.hosts)
    
    info('** Dumping host processes\n')
    for host in net.hosts:
        host.cmdPrint("ps aux")	

    net.hosts[0].cmdPrint("echo 1 > /proc/sys/net/ipv4/ip_forward")
    net.hosts[1].cmdPrint("echo 1 > /proc/sys/net/ipv4/ip_forward")
    router2 = ['ip addr add 183.0.0.2/20 dev R1-eth1', 
		'ip addr add 184.0.0.2/20 dev R1-eth2']
    router3 = ['ip addr add 185.0.0.2/20 dev R2-eth1']
    router4 = ['ip addr add 186.0.0.2/20 dev R3-eth1']
    router5 = ['ip addr add 185.0.0.1/20 dev R4-eth1', 
		'ip addr add 186.0.0.1/20 dev R4-eth2']
    ip_addr = {2 : router2, 3 : router3, 4: router4, 5:router5}
    info('** Setting up ip address\n')
    for k, v in ip_addr.items():
        for e in v:
            net.hosts[k].cmdPrint("echo 1 > /proc/sys/net/ipv4/ip_forward")
            net.hosts[k].cmdPrint(e)

    router_H1 = ['ip route add 183.0.0.0/20 via 182.0.0.2 dev H1-eth0',
		'ip route add 184.0.0.0/20 via 182.0.0.2 dev H1-eth0',
		'ip route add 185.0.0.0/20 via 182.0.0.2 dev H1-eth0',
		'ip route add 186.0.0.0/20 via 182.0.0.2 dev H1-eth0',
		'ip route add 187.0.0.0/20 via 182.0.0.2 dev H1-eth0']
    for r in router_H1:
        net.hosts[0].cmdPrint(r)

    router_H2 = ['ip route add 182.0.0.0/20 via 187.0.0.2 dev H2-eth0', 
		'ip route add 183.0.0.0/20 via 187.0.0.2 dev H2-eth0',
		'ip route add 184.0.0.0/20 via 187.0.0.2 dev H2-eth0',
		'ip route add 185.0.0.0/20 via 187.0.0.2 dev H2-eth0',
		'ip route add 186.0.0.0/20 via 187.0.0.2 dev H2-eth0']
    for r in router_H2:
        net.hosts[1].cmdPrint(r)

    router_R1 = ['ip route add 185.0.0.0/20 via 183.0.0.1 dev R1-eth1',
		'ip route add 186.0.0.0/20 via 184.0.0.1 dev R1-eth2',
		'ip route add 187.0.0.0/20 via 183.0.0.1 dev R1-eth1']
    for r in router_R1:
        net.hosts[2].cmdPrint(r)
    
    router_R2 = ['ip route add 182.0.0.0/20 via 183.0.0.2 dev R2-eth0',
		'ip route add 184.0.0.0/20 via 183.0.0.2 dev R2-eth0',
		'ip route add 186.0.0.0/20 via 185.0.0.1 dev R2-eth1',
		'ip route add 187.0.0.0/20 via 185.0.0.1 dev R2-eth1']
    for r in router_R2:
        net.hosts[3].cmdPrint(r)
    
    router_R3 = ['ip route add 182.0.0.0/20 via 184.0.0.2 dev R3-eth0',
		'ip route add 183.0.0.0/20 via 184.0.0.2 dev R3-eth0',
		'ip route add 185.0.0.0/20 via 186.0.0.1 dev R3-eth1',
		'ip route add 187.0.0.0/20 via 186.0.0.1 dev R3-eth1']
    for r in router_R3:
        net.hosts[4].cmdPrint(r)

    router_R4 = ['ip route add 182.0.0.0/20 via 186.0.0.2 dev R4-eth2',
		'ip route add 183.0.0.0/20 via 185.0.0.2 dev R4-eth1',
		'ip route add 184.0.0.0/20 via 186.0.0.2 dev R4-eth2']
    for r in router_R4:
        net.hosts[5].cmdPrint(r)

    FR = ['iptables -t nat -A POSTROUTING -o R1-eth1 -j MASQUERADE',
	'iptables -t nat -A POSTROUTING -o R1-eth2 -j MASQUERADE']
    for r in FR:
        net.hosts[2].cmdPrint(r)

    FR = ['iptables -t nat -A POSTROUTING -o R2-eth1 -j MASQUERADE',
	'iptables -t nat -A POSTROUTING -o R2-eth0 -j MASQUERADE']
    for r in FR:
        net.hosts[3].cmdPrint(r)

    RR = ['iptables -t nat -A POSTROUTING -o R3-eth1 -j MASQUERADE',
	'iptables -t nat -A POSTROUTING -o R3-eth0 -j MASQUERADE']
    for r in RR:
        net.hosts[4].cmdPrint(r)

    RR = ['iptables -t nat -A POSTROUTING -o R4-eth0 -j MASQUERADE',
	'iptables -t nat -A POSTROUTING -o R4-eth1 -j MASQUERADE',
	'iptables -t nat -A POSTROUTING -o R4-eth2 -j MASQUERADE']
    for r in RR:
        net.hosts[5].cmdPrint(r)

    info('** Testing network connectivity\n')
    net.ping(net.hosts)

    info('** Running CLI\n')
    CLI(net)


def stopNetwork():
    "stops a network (only called on a forced cleanup)"

    if net is not None:
        info('** Tearing down Quagga network\n')
        net.stop()

if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()