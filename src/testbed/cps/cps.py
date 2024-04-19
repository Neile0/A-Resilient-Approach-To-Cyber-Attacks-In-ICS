import sys
import time

from minicps.mcps import MiniCPS
from mininet.clean import Cleanup
from mininet.cli import CLI
from mininet.log import info
from mininet.link import Intf

import cps.network.controller as controller


class VesselCPS(MiniCPS):
    name = "vessel_cps"
    path = "/vagrant/vessel_cps_db.sqlite"

    def __init__(self, name, net):
        self.name = name
        self.net = net

        net.start()

        h1, h2 = self.net.get('h1', 'h2')

        h1.cmd('ping -c 1 %s' % h2.IP())

        info("Waiting for controller...")
        count = 1
        while not controller.is_ready():
            if count % 2 == 0:
                info(".")
            time.sleep(1)
            count += 1
        info('\n')

        s1 = self.net.get('s1')
        s1.cmd(sys.executable + ' -u ' + ' cps/mtd_client.py &> logs/mtd.log &')

        plc10P, plc13P, plcI, plc13S, plc10S, s3 = self.net.get('h4', 'h5', 'h6', 'h7', 'h8', 's3')

        plc10P.cmd(sys.executable + ' -u ' + ' cps/plc10P.py &> logs/plc10P.log &')
        plc13P.cmd(sys.executable + ' -u ' + ' cps/plc13P.py &> logs/plc13P.log &')
        plc13S.cmd(sys.executable + ' -u ' + ' cps/plc13S.py &> logs/plc13S.log &')
        plc10S.cmd(sys.executable + ' -u ' + ' cps/plc10S.py &> logs/plc10S.log &')

        plcI.cmd(sys.executable + ' -u ' + ' cps/plcI.py &> logs/plcI.log &')
        #
        #
        s3.cmd(sys.executable + ' -u ' + ' cps/physical_process.py &> logs/process.log &')

        motionsHMI_honey, ballastHMI_honey, scadaServer_honey, plc10P_honey, plc13P_honey, plcI_honey, plc13S_honey, plc10S_honey = self.net.get('h9', 'h10', 'h11', 'h12', 'h13', 'h14', 'h15', 'h16')

        motionsHMI_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/motions_honey.log &')
        ballastHMI_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/ballast_honey.log &')
        scadaServer_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/scada_honey.log &')
        plc10P_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/plc10P_honey.log &')
        plc13P_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/plc13P_honey.log &')
        plcI_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/plcI_honey.log &')
        plc13S_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/plc13S.log &')
        plc10S_honey.cmd(sys.executable + ' -u ' + ' cps/honeypot_host.py &> logs/plc10S.log &')

        CLI(self.net)

        net.stop()
        Cleanup()
