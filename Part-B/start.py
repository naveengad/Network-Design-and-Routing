#!/usr/bin/python

"""
Example network of Quagga routers
(QuaggaTopo + QuaggaService)
"""

import sys
import atexit
import time

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

    for host in net.hosts:
        host.cmdPrint("echo 1 > /proc/sys/net/ipv4/ip_forward")

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
            net.hosts[k].cmdPrint(e)

    info('** Dumping host processes\n')
    for host in net.hosts:
        host.cmdPrint("ps aux")		

    H1 = net.hosts[0]
    H2 = net.hosts[1]

    info('Pinging for Convergence\n')    
    pingForConv(H1, H2, 5)
    getTraceroutes(H1, H2)

    info('** Testing network connectivity\n')
    net.ping(net.hosts)

    net.configLinkStatus('R1','R2','down')
    info('\nPinging for Convergence after R1-R2 link is down')
    pingForConv(H1, H2, 35)
    getTraceroutes(H1, H2)

    info('** Running CLI\n')
    CLI(net)

def pingForConv(H1, H2, count):
    t1 = time.time()
    for i in range(count):
        time.sleep(1)
        print '\nIteration ', i + 1
        print H1.cmd('ping -c1 %s' % H2.IP())
        t2 = time.time()
        print t2 - t1	

def getTraceroutes(H1, H2):
    print '\n'
    info('Traceroute from H1 to H2\n')
    print H1.cmd('traceroute %s' % H2.IP())
    info('Traceroute from H2 to H1\n')
    print H2.cmd('traceroute %s' % H1.IP())

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