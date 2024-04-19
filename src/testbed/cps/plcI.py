import time
from socket import socket

from minicps.devices import PLC

from network.topo import VesselTopo
from datetime import datetime

import plc_utils as utils

PLC_SAMPLES = 1000
PLC_PERIOD_SEC = 0.4

CONTROLLER_IP = '192.168.1.1'
IP_PLC10P = ('IP_PLC10P', 1)
IP_PLC13P = ('IP_PLC13P', 1)
IP_PLC13S = ('IP_PLC13S', 1)
IP_PLC10S = ('IP_PLC10S', 1)
IP_MOTIONS_HMI = ('IP_MOTIONS_HMI', 1)

LVL_10P_REMOTE = ('10P_LVL', 2)
LVL_10P_LOCAL = ('10P_LVL', 4)

LVL_13P_REMOTE = ('13P_LVL', 3)
LVL_13P_LOCAL = ('13P_LVL', 4)

LVL_13S_REMOTE = ('13S_LVL', 5)
LVL_13S_LOCAL = ('13S_LVL', 4)

LVL_10S_REMOTE = ('10S_LVL', 6)
LVL_10S_LOCAL = ('10S_LVL', 4)

ROLL_ANGLE = ('ROLL_ANGLE', 4)
PITCH_ANGLE = ('PITCH_ANGLE', 4)



class PLCI(PLC):
    physical_ip = VesselTopo.production_hosts['plcI'][0]
    tags = (
        ('ROLL_ANGLE', 4, 'REAL'),
        ('PITCH_ANGLE', 4, 'REAL'),

        ('10P_LVL', 4, 'REAL'),
        ('13P_LVL', 4, 'REAL'),
        ('13S_LVL', 4, 'REAL'),
        ('10S_LVL', 4, 'REAL')
    )

    server = {
        'address': physical_ip,
        'tags': tags
    }

    protocol = {
        'name': 'enip',
        'mode': 1,
        'server': server
    }


    def pre_loop(self, sleep=0.1):
        print("DEBUG: PLCI enters pre_loop")
        time.sleep(sleep)

    def try_receive(self, tag, ip_tag):
        tries = 0
        while tries < 100:
            try:
                value = self.receive(tag, f"192.168.1.{self.get(ip_tag)}")
                time.sleep(0.1)
                return value
            except OSError as e:
                print(f"DEBUG OS Error in try receive: {e}")
                tries += 1
            except Exception as e:
                print(f"DEBUG Error in try receive: {e}")
                tries += 1
        return None

    def get_tank_lvl(self, local_tag, remote_tag, remote_ip):
        lvl = None
        while lvl is None:
            try:
                print(f"DEBUG: Receiving {local_tag[0]} from 192.168.1.{self.get(remote_ip)}")
                lvl = float(self.try_receive(remote_tag, remote_ip))
                print(f"DEBUG: Received {lvl}")
                self.send(local_tag, lvl, self.physical_ip)
                time.sleep(0.1)
                return lvl
            except OSError as os_e:
                print(f"DEBUG: OS Error {os_e}")
                time.sleep(0.1)
            except Exception as e:
                print(f"DEBUG: Error lvl is {lvl} and Error {e}")
                time.sleep(0.1)
    def main_loop(self, **kwargs):
        print("DEBUG: PLCI enters main_loop")

        count = 0
        while count <= PLC_SAMPLES:
            lvl_10P, lvl_13P, lvl_13S, lvl_10S = None, None, None, None

            lvl_10P = self.get_tank_lvl(LVL_10P_LOCAL, LVL_10P_REMOTE, IP_PLC10P)
            lvl_13P = self.get_tank_lvl(LVL_13P_LOCAL, LVL_13P_REMOTE, IP_PLC13P)
            lvl_13S = self.get_tank_lvl(LVL_13S_LOCAL, LVL_13S_REMOTE, IP_PLC13S)
            lvl_10S = self.get_tank_lvl(LVL_10S_LOCAL, LVL_10S_REMOTE, IP_PLC10S)

            roll_angle = float(self.get(ROLL_ANGLE))
            pitch_angle = float(self.get(PITCH_ANGLE))

            sent_to_hmi = utils.try_send(self, ROLL_ANGLE, roll_angle, IP_MOTIONS_HMI)
            if not sent_to_hmi:
                print(f"{datetime.now()} Could Not Send To Motions HMI")

            sent_to_hmi = utils.try_send(self, PITCH_ANGLE, pitch_angle, IP_MOTIONS_HMI)
            if not sent_to_hmi:
                print(f"{datetime.now()} Could Not Send To Motions HMI")


            print(f"{datetime.now()}: Roll: {roll_angle:.3f}° Pitch: {pitch_angle:.3f}° | Levels are 10P: {lvl_10P:.3f}, 13P: {lvl_13P:.3f}, 13S: {lvl_13S:.3f}, 10S: {lvl_10S:.3f}")

            time.sleep(PLC_PERIOD_SEC)
            count += 1


if __name__ == "__main__":
    plcI = PLCI(
        name="plcI",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=PLCI.protocol
    )
