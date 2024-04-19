from pprint import pprint

from mininet.topo import Topo
from mininet.link import Intf

class VesselTopo(Topo):
    NETMASK = '/24'

    # Define scada_hosts dictionary
    scada_hosts = {
        'motionsHMI': ('192.168.1.10', '00:1D:9C:B6:AA:18'),
        'ballastHMI': ('192.168.1.20', '00:1D:9C:B6:AE:42'),
        'scadaServer': ('192.168.1.30', '00:1D:9C:B6:A4:09'),
    }

    scada_honey_hosts = {
        'motionsHMI_honey': '192.168.1.90',
        'ballastHMI_honey': '192.168.1.100',
        'scadaServer_honey': '192.168.1.110',
    }

    # Define production_hosts dictionary
    production_hosts = {
        'plc10P': ('192.168.1.40', '00:1D:9C:C8:BC:12'),
        'plc13P': ('192.168.1.50', '00:1D:9C:C8:B6:22'),
        'plcI': ('192.168.1.60', '00:1D:9C:C6:BA:54'),
        'plc13S': ('192.168.1.70', '00:1D:9C:C8:B1:89'),
        'plc10S': ('192.168.1.80', '00:1D:9C:C7:B0:70'),
    }

    production_hosts_honey = {
        'plc10P_honey': '192.168.1.120',
        'plc13P_honey': '192.168.1.130',
        'plcI_honey': '192.168.1.140',
        'plc13S_honey': '192.168.1.150',
        'plc10S_honey': '192.168.1.160',
    }

    all_hosts = {}

    def __init__(self):
        super(VesselTopo, self).__init__()



        s1, s2, s3, s4, s5, s6, s7, s8 = [self.addSwitch(s, stp=True, failMode='standalone') for s in
                                          ('s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8')]



        ## Link SCADA + Production Network
        self.addLink(s1, s2)
        self.addLink(s2, s3)

        # Scada Hosts
        host_counter = 1
        for host, (ip, mac) in self.scada_hosts.items():
            self.all_hosts[host] = self.addHost(f"h{host_counter}", ip=ip + self.NETMASK, mac=mac)
            host_counter += 1

        # Scada links in star topology
        self.addLink(self.all_hosts['motionsHMI'], s1)
        self.addLink(self.all_hosts['ballastHMI'], s1)
        self.addLink(self.all_hosts['scadaServer'], s1)

        # Production Network Hosts
        for host, (ip, mac) in self.production_hosts.items():
            self.all_hosts[host] = self.addHost(f"h{host_counter}", ip=ip + self.NETMASK, mac=mac)
            host_counter += 1

        ## Production Links in ring topology

        self.addLink(s3, s4)
        self.addLink(s4, s5)
        self.addLink(s5, s6)
        self.addLink(s6, s7)
        self.addLink(s7, s8)
        self.addLink(s8, s3)

        self.addLink(self.all_hosts['plc10P'], s4)
        self.addLink(self.all_hosts['plc13P'], s5)
        self.addLink(self.all_hosts['plcI'], s6)
        self.addLink(self.all_hosts['plc13S'], s7)
        self.addLink(self.all_hosts['plc10S'], s8)

        ## HONEY POTS OFF FROM S2
        s1_h, s2_h, s3_h, s4_h, s5_h, s6_h, s7_h, s8_h = [self.addSwitch(s, stp=True, failMode='standalone') for s in
                                                          ['s9', 's10', 's11', 's12', 's13', 's14', 's15', 's16']]

        # Link Real Net with HoneyNet
        self.addLink(s2, s2_h)

        ## Link SCADA + Production Network
        self.addLink(s1_h, s2_h)
        self.addLink(s2_h, s3_h)

        for host, ip in self.scada_honey_hosts.items():
            self.all_hosts[host] = self.addHost(f"h{host_counter}", ip=ip + self.NETMASK)
            host_counter += 1

        self.addLink(self.all_hosts['motionsHMI_honey'], s1_h)
        self.addLink(self.all_hosts['ballastHMI_honey'], s1_h)
        self.addLink(self.all_hosts['scadaServer_honey'], s1_h)

        # Production Network Hosts
        for host, ip in self.production_hosts_honey.items():
            self.all_hosts[host] = self.addHost(f"h{host_counter}", ip=ip + self.NETMASK)
            host_counter += 1

        ## Production Links (HONEY_NET) in ring topology
        self.addLink(s3_h, s4_h)
        self.addLink(s4_h, s5_h)
        self.addLink(s5_h, s6_h)
        self.addLink(s6_h, s7_h)
        self.addLink(s7_h, s8_h)
        self.addLink(s8_h, s3_h)

        self.addLink(self.all_hosts['plc10P_honey'], s4_h)
        self.addLink(self.all_hosts['plc13P_honey'], s5_h)
        self.addLink(self.all_hosts['plcI_honey'], s6_h)
        self.addLink(self.all_hosts['plc13S_honey'], s7_h)
        self.addLink(self.all_hosts['plc10S_honey'], s8_h)

        pprint(self.all_hosts)
