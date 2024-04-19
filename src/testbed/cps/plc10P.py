import time
from minicps.devices import PLC

from network.topo import VesselTopo
from tanks import Tank10P

from datetime import datetime

import plc_utils as utils


PLC_SAMPLES = 1000
PLC_PERIOD_SEC = 0.4

LVL_10P = ('10P_LVL', 2)
VALVE_IN_10P = ('10P_VALVE_IN', 2)
VALVE_OUT_10P = ('10P_VALVE_OUT', 2)
PUMP_10P = ('10P_PUMP', 2)

IP_BALLAST_HMI = ('IP_BALLAST_HMI', 1)
IP_SCADA_SERVER = ('IP_SCADA_SERVER', 1)


class PLC10P(PLC):
    physical_ip = VesselTopo.production_hosts['plc10P'][0]
    tags = (
        ('10P_LVL', 2, 'REAL'),
        ('10P_VALVE_IN', 2, 'INT'),
        ('10P_VALVE_OUT', 2, 'INT'),
        ('10P_PUMP', 2, 'INT'),
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
        print("DEBUG: PLC10P enters pre_loop")
        time.sleep(sleep)


    def main_loop(self, **kwargs):
        print("DEBUG: PLC10P enters main_loop")

        count = 0
        while count <= PLC_SAMPLES:

            tank_level = float(self.get(LVL_10P))
            print(f"{datetime.now()} PLC10P tank level {tank_level:.3f}")

            self.send(LVL_10P, tank_level, self.physical_ip)
            sent_to_server = utils.try_send(self, LVL_10P, tank_level, IP_SCADA_SERVER)
            if not sent_to_server:
                print(f"{datetime.now()} Could Not Send To Scada Server")
            sent_to_hmi = utils.try_send(self, LVL_10P, tank_level, IP_BALLAST_HMI)
            if not sent_to_hmi:
                print(f"{datetime.now()} Could Not Send To Ballast HMI")


            if tank_level >= Tank10P.levels['HH']:
                print(f"WARNING PLC10P: level over EXTREME (HH): {tank_level:.3f} >= {Tank10P.levels['HH']}")

            if tank_level >= Tank10P.levels['H']:
                print(f"INFO: PLC10P: level over HIGH -> close INPUT VALUE, open OUTPUT VALUE, turn on PUMP")
                self.set(VALVE_IN_10P, 0)
                self.send(VALVE_IN_10P, 0, self.physical_ip)
                self.set(VALVE_OUT_10P, 1)
                self.send(VALVE_OUT_10P, 1, self.physical_ip)
                self.set(PUMP_10P, 1)
                self.send(PUMP_10P, 1, self.physical_ip)

            elif tank_level <= Tank10P.levels['LL']:
                print(
                    f"WARNING PLC10P: level under EXTREME (LL): {tank_level:.3f} <= {Tank10P.levels['LL']}")
            elif tank_level <= Tank10P.levels['L']:
                print(f"INFO PLC10P: level under LOW -> close OUTPUT VALUE and shutdown PUMP, open INPUT VALVE")
                self.set(VALVE_OUT_10P, 0)
                self.send(VALVE_OUT_10P, 0, self.physical_ip)
                self.set(PUMP_10P, 0)
                self.send(PUMP_10P, 0, self.physical_ip)
                self.set(VALVE_IN_10P, 1)
                self.send(VALVE_IN_10P, 0, self.physical_ip)

            time.sleep(PLC_PERIOD_SEC)
            count += 1


if __name__ == "__main__":
    print("DEBUG PLC10P")
    plc10P = PLC10P(
        name="plc10P",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=PLC10P.protocol
    )
