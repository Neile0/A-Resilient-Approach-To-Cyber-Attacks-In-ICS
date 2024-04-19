import argparse
import os

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch

import init_minicps as init
from cps import VesselCPS
from cps.network.controller import RyuController
from cps.network.topo import VesselTopo

# Sets DISPLAY environment variable for Xterm
# to use Xterm, when SSHing into todolist.txt bed from vagrant use
# vagrant -X ssh testbed
os.environ["DISPLAY"] = "_gateway:0.0"

parser = argparse.ArgumentParser()
parser.add_argument("name")

args = parser.parse_args()

name = args.name

print(f"Running Simulation for {name}")

init.run()

setLogLevel('info')

topo = VesselTopo()

net = Mininet(topo=topo, controller=RyuController(), waitConnected=True, cleanup=True, switch=OVSSwitch)

net_cps = VesselCPS(
    name=name,
    net=net,
)
