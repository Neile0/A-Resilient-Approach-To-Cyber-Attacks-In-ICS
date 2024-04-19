import time

from minicps.devices import PLC

from network.topo import VesselTopo
from tanks import Tank10S

from datetime import datetime

import plc_utils as utils

PLC_SAMPLES = 1000
PLC_PERIOD_SEC = 0.4

LVL_10S = ('10S_LVL', 6)
VALVE_IN_10S = ('10S_VALVE_IN', 6)
VALVE_OUT_10S = ('10S_VALVE_OUT', 6)
PUMP_10S = ('10S_PUMP', 6)

IP_BALLAST_HMI = ('IP_BALLAST_HMI', 1)
IP_SCADA_SERVER = ('IP_SCADA_SERVER', 1)


class PLC10S(PLC):
    physical_ip = VesselTopo.production_hosts['plc10S'][0]
    tags = (
        ('10S_LVL', 6, 'REAL'),
        ('10S_VALVE_IN', 6, 'INT'),
        ('10S_VALVE_OUT', 6, 'INT'),
        ('10S_PUMP', 6, 'INT'),
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
        print("DEBUG: PLC10S enters pre_loop")
        time.sleep(sleep)


    def main_loop(self, **kwargs):
        print("DEBUG: PLC10S enters main_loop")

        count = 0
        while count <= PLC_SAMPLES:

            tank_level = float(self.get(LVL_10S))
            print(f"{datetime.now()} PLC10S tank level {tank_level:.3f}")

            self.send(LVL_10S, tank_level, self.physical_ip)

            sent_to_server = utils.try_send(self, LVL_10S, tank_level, IP_SCADA_SERVER)
            if not sent_to_server:
                print(f"{datetime.now()} Could Not Send To Scada Server")
            sent_to_hmi = utils.try_send(self, LVL_10S, tank_level, IP_BALLAST_HMI)
            if not sent_to_hmi:
                print(f"{datetime.now()} Could Not Send To Ballast HMI")

            if tank_level >= Tank10S.levels['HH']:
                print(f"WARNING PLC10S: level over EXTREME (HH): {tank_level:.3f} >= {Tank10S.levels['HH']}")

            if tank_level >= Tank10S.levels['H']:
                print(f"INFO: PLC10S: level over HIGH -> close INPUT VALUE, open OUTPUT VALUE, turn on PUMP")
                self.set(VALVE_IN_10S, 0)
                self.send(VALVE_IN_10S, 0, self.physical_ip)
                self.set(VALVE_OUT_10S, 1)
                self.send(VALVE_OUT_10S, 1, self.physical_ip)
                self.set(PUMP_10S, 1)
                self.send(PUMP_10S, 1, self.physical_ip)

            elif tank_level <= Tank10S.levels['LL']:
                print(
                    f"WARNING PLC10S: level under EXTREME (LL): {tank_level:.3f} <= {Tank10S.levels['LL']}")
            elif tank_level <= Tank10S.levels['L']:
                print(f"INFO PLC10S: level under LOW -> close OUTPUT VALUE and shutdown PUMP, open INPUT VALVE")
                self.set(VALVE_OUT_10S, 0)
                self.send(VALVE_OUT_10S, 0, self.physical_ip)
                self.set(PUMP_10S, 0)
                self.send(PUMP_10S, 0, self.physical_ip)
                self.set(VALVE_IN_10S, 1)
                self.send(VALVE_IN_10S, 0, self.physical_ip)

            time.sleep(PLC_PERIOD_SEC)
            count += 1


if __name__ == "__main__":
    print("DEBUG PLC10S")
    plc10S = PLC10S(
        name="plc10S",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=PLC10S.protocol
    )
