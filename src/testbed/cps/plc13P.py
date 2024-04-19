import time

from minicps.devices import PLC

from network.topo import VesselTopo
from tanks import Tank13P

from datetime import datetime

import plc_utils as utils

PLC_SAMPLES = 1000
PLC_PERIOD_SEC = 0.4

LVL_13P = ('13P_LVL', 3)
VALVE_IN_13P = ('13P_VALVE_IN', 3)
VALVE_OUT_13P = ('13P_VALVE_OUT', 3)
PUMP_13P = ('13P_PUMP', 3)

IP_BALLAST_HMI = ('IP_BALLAST_HMI', 1)
IP_SCADA_SERVER = ('IP_SCADA_SERVER', 1)

class PLC13P(PLC):
    physical_ip = VesselTopo.production_hosts['plc13P'][0]
    tags = (
        ('13P_LVL', 3, 'REAL'),
        ('13P_VALVE_IN', 3, 'INT'),
        ('13P_VALVE_OUT', 3, 'INT'),
        ('13P_PUMP', 3, 'INT'),
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
        print("DEBUG: PLC13P enters pre_loop")
        time.sleep(sleep)


    def main_loop(self, **kwargs):
        print("DEBUG: PLC13P enters main_loop")

        count = 0
        while count <= PLC_SAMPLES:

            tank_level = float(self.get(LVL_13P))
            print(f"{datetime.now()} PLC13P tank level {tank_level:.3f}")

            self.send(LVL_13P, tank_level, self.physical_ip)
            sent_to_server = utils.try_send(self, LVL_13P, tank_level, IP_SCADA_SERVER)
            if not sent_to_server:
                print(f"{datetime.now()} Could Not Send To Scada Server")
            sent_to_hmi = utils.try_send(self, LVL_13P, tank_level, IP_BALLAST_HMI)
            if not sent_to_hmi:
                print(f"{datetime.now()} Could Not Send To Ballast HMI")

            if tank_level >= Tank13P.levels['HH']:
                print(f"WARNING PLC13P: level over EXTREME (HH): {tank_level:.3f} >= {Tank13P.levels['HH']}")

            if tank_level >= Tank13P.levels['H']:
                print(f"INFO: PLC13P: level over HIGH -> close INPUT VALUE, open OUTPUT VALUE, turn on PUMP")
                self.set(VALVE_IN_13P, 0)
                self.send(VALVE_IN_13P, 0, self.physical_ip)
                self.set(VALVE_OUT_13P, 1)
                self.send(VALVE_OUT_13P, 1, self.physical_ip)
                self.set(PUMP_13P, 1)
                self.send(PUMP_13P, 1, self.physical_ip)

            elif tank_level <= Tank13P.levels['LL']:
                print(
                    f"WARNING PLC13P: level under EXTREME (LL): {tank_level:.3f} <= {Tank13P.levels['LL']}")
            elif tank_level <= Tank13P.levels['L']:
                print(f"INFO PLC13P: level under LOW -> close OUTPUT VALUE and shutdown PUMP, open INPUT VALVE")
                self.set(VALVE_OUT_13P, 0)
                self.send(VALVE_OUT_13P, 0, self.physical_ip)
                self.set(PUMP_13P, 0)
                self.send(PUMP_13P, 0, self.physical_ip)
                self.set(VALVE_IN_13P, 1)
                self.send(VALVE_IN_13P, 0, self.physical_ip)

            time.sleep(PLC_PERIOD_SEC)
            count += 1


if __name__ == "__main__":
    print("DEBUG PLC13P")
    plc13P = PLC13P(
        name="plc13P",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=PLC13P.protocol
    )
