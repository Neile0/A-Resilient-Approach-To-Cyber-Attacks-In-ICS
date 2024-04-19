import logging
import pprint
from random import seed, sample

import zmq
from ryu.app.wsgi import WSGIApplication
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import ether_types
import time

from datetime import datetime
from attack_detected_event import AttackDetectedEvent
from endpoints import CyberDeceptionEndpoints
from host import Host, NetworkType
from mtd_event import MTDEvent


def empty_flow_table(datapath):
    ofProto = datapath.ofproto
    parser = datapath.ofproto_parser
    match = parser.OFPMatch()
    flow_mod = datapath.ofproto_parser.OFPFlowMod(datapath, 0, 0, 0, ofProto.OFPFC_DELETE, 0, 0, 1,
                                                  ofProto.OFPCML_NO_BUFFER, ofProto.OFPP_ANY, ofProto.OFPG_ANY, 0,
                                                  match=match, instructions=[])
    datapath.send_msg(flow_mod)


class CyberDeceptionController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _EVENTS = [MTDEvent, AttackDetectedEvent]

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }
    SAME_SEED = True
    ENABLE_MTD = True
    MTD_PERIOD_SECONDS = 60
    random_seed = 2024

    def call_mtd(self):
        self.logger.info("MTD Call from REST API")

    def _setup_endpoints(self, wsgi):
        wsgi.register(CyberDeceptionEndpoints, {'app': self})

    def start(self):
        super(CyberDeceptionController, self).start()
        if self.ENABLE_MTD:
            self.threads.append(hub.spawn(self._periodic_MTD_worker))
        else:
            self.logger.warn("MTD is DISABLED")

    def _periodic_MTD_worker(self):
        while True:
            self.send_event_to_observers(MTDEvent("MTD"))
            hub.sleep(self.MTD_PERIOD_SECONDS)

    @staticmethod
    def _get_hosts(path):
        hosts = []
        with open(path) as file:
            for line in file:
                host, on_network, ip = line.strip().split(',')
                hosts.append(Host(host, ip, network=on_network))
        return hosts

    def get_production_hosts(self):
        return {h.hostname: h for h in self.hosts_on_network if h.network is NetworkType.PRODUCTION}

    def get_scada_hosts(self):
        return {h.hostname: h for h in self.hosts_on_network if h.network is NetworkType.SCADA}

    def __init__(self, *args, **kwargs):
        super(CyberDeceptionController, self).__init__(*args, **kwargs)
        self.stats = {}
        self.flow_stats = {}
        self.flow_speed = {}
        self.detected_attacks = []
        self.detected_attack_redirect = {}
        self.dynamic_ip_queue = None

        self.logger.setLevel(logging.WARN)
        print(f"Logger set to: {self.logger.level}")

        self.mac_to_port = {}

        self.packet_received = False

        self.datapaths = set()

        self.hosts_on_network = self._get_hosts("/vagrant/ip_addresses.txt")

        self.ip_to_host_lookup = {h.physical_ip: h for h in self.hosts_on_network}
        self.hostname_lookup = {h.hostname : h for h in self.hosts_on_network}

        self.physical_ips = self.ip_to_host_lookup.keys()


        self.physical_to_dynamic_ip_mappings = {}
        self.dynamic_to_physical_ip_mappings = {}

        self.available_dynamic_ips = [f"192.168.1.{x}" for x in range(3, 254) if
                                      f"192.168.1.{x}" not in self.physical_ips]

        if self.ENABLE_MTD:
            self.logger.info(f"Available dynamic {self.available_dynamic_ips}")

        self.monitor_thread = hub.spawn(self._monitor)

        self.host_connections = {}

        # Setup API Endpoints
        self._setup_endpoints(kwargs['wsgi'])

        # Setup messaging
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5555")

    def _monitor(self):
        while True:
            for dp in self.datapaths:
                self._request_stats(dp)
            hub.sleep(0.5)

            # self.flow_predict()


    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)



    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        icmp_code = -1
        icmp_type = -1
        tp_src = 0
        tp_dst = 0

        #need to filter out arp flows or else a key error will occur from using 'ipv4_src'
        ip_flows = []
        for flow in body:
            if not flow.priority == 1:
                pass
            try:
                ip_flow = flow.match['ipv4_src']
                if ip_flow is not None:
                    ip_flows.append(flow)
            except:
                pass

        if len(ip_flows) == 0:
            return


        for stat in sorted(ip_flows, key=lambda flow: (flow.match['ipv4_src'], flow.match['ipv4_dst'])):
            ip_src = stat.match['ipv4_src']
            ip_dst = stat.match['ipv4_dst']

            try:
                packet_count_per_second = stat.packet_count / stat.duration_sec
                packet_count_per_nsecond = stat.packet_count / stat.duration_nsec
            except:
                packet_count_per_second = 0
                packet_count_per_nsecond = 0

            try:
                byte_count_per_second = stat.byte_count / stat.duration_sec
                byte_count_per_nsecond = stat.byte_count / stat.duration_nsec
            except:
                byte_count_per_second = 0
                byte_count_per_nsecond = 0

            src_hostname = self.ip_to_host_lookup[ip_src].hostname if self.is_physical_ip(ip_src) else self.ip_to_host_lookup[self.dynamic_to_physical_ip_mappings[ip_src]].hostname if self.is_dynamic_ip(ip_src) else "Unknown"
            dst_hostname = self.ip_to_host_lookup[ip_dst].hostname if self.is_physical_ip(ip_dst) else \
            self.ip_to_host_lookup[self.dynamic_to_physical_ip_mappings[ip_dst]].hostname if self.is_dynamic_ip(
                ip_dst) else "Unknown"


            if byte_count_per_second > 3000000:
                print(f"{datetime.now()} {src_hostname} -> {dst_hostname} with {packet_count_per_second:.3f}pkt/s {byte_count_per_second:.3f}byte/s")

                if "_honey" in dst_hostname:
                    print(f"{datetime.now()} Attack Targeting Honey. IGNORE")
                else:
                    honey_pot_hostname = f"{dst_hostname}_honey"
                    print(f"{datetime.now()} Starting Redirecting to {honey_pot_hostname}")
                    self.detected_attacks.append((ip_src, ip_dst))
                    self.detected_attack_redirect[(ip_src, ip_dst)] = self.hostname_lookup[honey_pot_hostname].dynamic_ip
                    self.send_event_to_observers(AttackDetectedEvent(self.hostname_lookup[dst_hostname].physical_ip))

    @set_ev_cls(AttackDetectedEvent)
    def move_target(self, ev):
        host = self.ip_to_host_lookup[ev.target]
        was_at = host.dynamic_ip
        print(f"{datetime.now()} Moving target {host.hostname}")
        host.dynamic_ip = self.dynamic_ip_queue.pop()

        self.physical_to_dynamic_ip_mappings = {h.physical_ip: h.dynamic_ip for h in self.hosts_on_network}
        self.dynamic_to_physical_ip_mappings = {v: k for k, v in self.physical_to_dynamic_ip_mappings.items()}

        for current_switch in self.datapaths:
            parser = current_switch.ofproto_parser
            match = parser.OFPMatch()
            empty_flow_table(current_switch)
            ofproto = current_switch.ofproto
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(current_switch, 0, match, actions)

        now_at = self.ip_to_host_lookup[ev.target].dynamic_ip
        print(f"{datetime.now()} {host.hostname} was at {was_at} now at {now_at}")

    @set_ev_cls(MTDEvent)
    def update(self, ev):
        print(f"Performing MTD at {datetime.now()}")
        seed(self.random_seed)
        if not self.SAME_SEED:
            self.random_seed += 1

        self.dynamic_ip_queue = sample(self.available_dynamic_ips, len(self.available_dynamic_ips))

        for host in self.hosts_on_network:
            host.dynamic_ip = self.dynamic_ip_queue.pop()

        self.physical_to_dynamic_ip_mappings = {h.physical_ip: h.dynamic_ip for h in self.hosts_on_network}
        self.dynamic_to_physical_ip_mappings = {v: k for k, v in self.physical_to_dynamic_ip_mappings.items()}

        for current_switch in self.datapaths:
            parser = current_switch.ofproto_parser
            match = parser.OFPMatch()
            empty_flow_table(current_switch)
            ofproto = current_switch.ofproto
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(current_switch, 0, match, actions)

        print(f"IP Mappings at {datetime.now()}")
        print(self.physical_to_dynamic_ip_mappings)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.datapaths.add(datapath)

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def is_physical_ip(self, ip):
        if ip in self.physical_to_dynamic_ip_mappings.keys():
            return True

    def is_dynamic_ip(self, ip):
        if ip in self.physical_to_dynamic_ip_mappings.values():
            return True

    def is_host_connected_to_switch(self, datapath, ip):
        if ip in self.host_connections.keys():
            if self.host_connections[ip] == datapath:
                self.logger.debug(f"{ip} is connected to {datapath}")
                return True
            else:
                return False
        return True

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, hard_timeout=None):
        '''
            Adds flow rules to the switch
            Reference: Simple_Switch
            http://ryu.readthedocs.io/en/latest/writing_ryu_app.html
        '''
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            if hard_timeout == None:
                mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                        priority=priority, match=match,
                                        instructions=inst)
            else:
                mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                        priority=priority, match=match,
                                        instructions=inst, hard_timeout=hard_timeout)
        else:
            if hard_timeout == None:
                mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                        match=match, instructions=inst)
            else:
                mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                        match=match, instructions=inst, hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    def simple_switch_handle_packet_in(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def handlePacketInEvents(self, ev):
        if self.packet_received is False:
            self.packet_received = True
        '''
            Handles Incoming Packets & implements Random Host mutation technique
            by changing src & dst IP addresses of the incoming packets.
            Some part of the code is inspired by Simple_Switch
            http://ryu.readthedocs.io/en/latest/writing_ryu_app.html
        '''
        if not self.ENABLE_MTD:
            self.simple_switch_handle_packet_in(ev)
            return

        actions = []
        pktDrop = False

        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)


        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)  # Extract ARP object from packet
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)  # Extract ICMP object packet

        match = None

        if arp_pkt:
            '''Handles ARP packets'''
            src = arp_pkt.src_ip
            dst = arp_pkt.dst_ip

            '''
                To Implement a Learning MTD, there is a need to know, to which switch, the host is directly connected to.
                So the first time an ARP packet comes in who's src address is real, we store the IP addr-Switch DPID mapping
                into the member variable HostAttachments.
            '''
            if self.is_physical_ip(src) and src not in self.host_connections.keys():
                self.host_connections[src] = datapath.id

            '''
                Learning MTD implementation
                if src is real change it to virtual no matter wat.
                if dest doesn't have a mapping in my table change to real and flood.
                    This happens only for the first time when we donot know
                    to which switch, the destination host is directly connected to.
                if dst is virtual check if dest is directly connected then change it to real
                else let it pass unchanged.
            '''

            if self.is_physical_ip(src):
                match = parser.OFPMatch(eth_type=0x0806, in_port=in_port, arp_spa=src, arp_tpa=dst)
                spa = self.physical_to_dynamic_ip_mappings[src]
                self.logger.info("Changing SRC REAL IP " + src + "---> Virtual SRC IP " + spa)
                actions.append(parser.OFPActionSetField(arp_spa=spa))

            if self.is_dynamic_ip(dst):
                if dst == src:
                    # LAND ATTACK
                    self.logger.critical("ARP LAND ATTACK DETECTED")

                    pktDrop = True
                    self.logger.info(f"Dropping from {datapath.id}")



                match = parser.OFPMatch(eth_type=0x0806, in_port=in_port, arp_tpa=dst, arp_spa=src)
                if self.is_host_connected_to_switch(datapath=datapath.id, ip=self.dynamic_to_physical_ip_mappings[dst]):
                    keys = self.dynamic_to_physical_ip_mappings.keys()
                    tpa = self.dynamic_to_physical_ip_mappings[dst]
                    self.logger.info("Changing DST Virtual IP " + dst + "---> REAL DST IP " + tpa)
                    self.logger.debug(f"{dst} Connected directly to {datapath.id}")
                    actions.append(parser.OFPActionSetField(arp_tpa=tpa))

            elif self.is_physical_ip(dst):
                '''Learn MTD From Flood'''
                match = parser.OFPMatch(eth_type=0x0806, in_port=in_port, arp_spa=src, arp_tpa=dst)
                if not self.is_host_connected_to_switch(datapath=datapath.id, ip=dst):
                    pktDrop = True
                    self.logger.info(f"Dropping from {datapath.id}")
            else:
                pktDrop = True
        elif ipv4_pkt:
            '''Handles ICMP packets'''
            src = ipv4_pkt.src
            dst = ipv4_pkt.dst

            if (src, dst) in self.detected_attacks:
                # print(f"Recurring attack packet {src} -> {dst}")
                redirected_ip = self.detected_attack_redirect[(src,dst)]
                actions.append(parser.OFPActionSetField(ipv4_dst=redirected_ip))
                dst = redirected_ip


            if self.is_physical_ip(src) and src not in self.host_connections.keys():
                self.host_connections[src] = datapath.id

            '''
                Learning MTD implementation
                if src is real change it to virtual no matter wat.
                if dest doesn't have a mapping in my table change to real and flood.
                    This happens only for the first time when we donot know
                    to which switch, the destination host is directly connected to.
                if dst is virtual check if dest is directly connected then change it to real
                else let it pass unchanged.
            '''

            if self.is_physical_ip(src):
                match = parser.OFPMatch(eth_type=0x0800, in_port=in_port, ipv4_src=src, ipv4_dst=dst)
                ipSrc = self.physical_to_dynamic_ip_mappings[src]
                self.logger.info("Changing SRC REAL IP " + src + "---> Virtual SRC IP " + ipSrc)
                actions.append(parser.OFPActionSetField(ipv4_src=ipSrc))
            if self.is_dynamic_ip(dst):
                if dst == src:
                    # LAND ATTACK
                    print(f"LAND ATTACK DETECTED at {datetime.now()}")

                    target_physical_ip = self.dynamic_to_physical_ip_mappings[dst]
                    target_host = self.ip_to_host_lookup[target_physical_ip]

                    if "_honey" not in target_host.hostname:
                        print(f"{datetime.now()} LAND ATTACK TARGETING {target_host.hostname}")
                        honeypot_host = f"{target_host.hostname}_honey"
                        honey_ip = self.hostname_lookup[honeypot_host].dynamic_ip
                        print(f"{datetime.now()} Redirecting to Honeypot {honeypot_host} at {honey_ip}")
                        actions.append(parser.OFPActionSetField(ipv4_dst=honey_ip))

                        self.detected_attacks.append((src, dst))
                        self.detected_attack_redirect[(src,dst)] = honey_ip
                        self.send_event_to_observers(AttackDetectedEvent(target_physical_ip))
                        dst = honey_ip
                    else:
                        print(f"{datetime.now()} Attack Targeting Honeypot. IGNORE")

                match = parser.OFPMatch(eth_type=0x0800, in_port=in_port, ipv4_dst=dst, ipv4_src=src)

                if self.is_host_connected_to_switch(datapath=datapath.id, ip=self.dynamic_to_physical_ip_mappings[dst]):
                    ipDst = self.dynamic_to_physical_ip_mappings[dst]
                    self.logger.info("Changing DST Virtual IP " + dst + "---> Real DST IP " + ipDst)
                    self.logger.debug(f"{ipDst} Connected directly to {datapath.id}")
                    actions.append(parser.OFPActionSetField(ipv4_dst=ipDst))


            elif self.is_physical_ip(dst):
                '''Learn From Flood'''
                match = parser.OFPMatch(eth_type=0x0806, in_port=in_port, arp_spa=src, arp_tpa=dst)
                if not self.is_host_connected_to_switch(datapath=datapath.id, ip=dst):
                    self.logger.debug(self.host_connections)
                    pktDrop = True
                    self.logger.info("Dropping from", dpid)
            else:
                print(f"{dst} dst is neither physical or dynamic")
                pktDrop = True

        '''Extract Ethernet Object from packet'''
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        '''Store the incoming packet source address, switch & the port combination to be used to learn the packet switching'''
        self.mac_to_port.setdefault(dpid, {})

        self.logger.debug("packet in %s %s %s %s", dpid, src, dst, in_port)

        '''learn a mac address to avoid FLOOD next time.'''

        self.mac_to_port[dpid][src] = in_port
        '''Learning Mac implemention to avoid flood'''

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        if dst in self.mac_to_port[dpid]:
            self.logger.debug(f"Dst ({dst}) In Port: {self.mac_to_port[dpid]} on {dpid} (pkt drop is {pktDrop})")
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        '''Append the outport action to the action set'''
        if not pktDrop:
            actions.append(parser.OFPActionOutput(out_port))
        '''install a flow to avoid packet_in next time'''
        if out_port != ofproto.OFPP_FLOOD:
            if match is None:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            '''
                verify if we have a valid buffer_id, if yes avoid to send both flow_mod & packet_out
                Install Flow rules to avoid the packet in message for similar packets.
            '''
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        '''
            Build a packet out message & send it to the switch with the action set,
            Action set includes all the IP addres changes & out port actions.
        '''
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        '''Send the packet out message to the switch'''
        datapath.send_msg(out)

