import time

import pandas as pd
from minicps.devices import Device

from tanks import Tank10P
from tanks import Tank10S
from tanks import Tank13P
from tanks import Tank13S

from datetime import datetime


PLC_SAMPLES = 1000
PLC_PERIOD_SEC = 0.4

LVL_10P = ('10P_LVL', 2)
VALVE_IN_10P = ('10P_VALVE_IN', 2)
VALVE_OUT_10P = ('10P_VALVE_OUT', 2)
PUMP_10P = ('10P_PUMP', 2)

LVL_13P = ('13P_LVL', 3)
VALVE_IN_13P = ('13P_VALVE_IN', 3)
VALVE_OUT_13P = ('13P_VALVE_OUT', 3)
PUMP_13P = ('13P_PUMP', 3)

ROLL_ANGLE = ('ROLL_ANGLE', 4)
PITCH_ANGLE = ('PITCH_ANGLE', 4)

LVL_13S = ('13S_LVL', 5)
VALVE_IN_13S = ('13S_VALVE_IN', 5)
VALVE_OUT_13S = ('13S_VALVE_OUT', 5)
PUMP_13S = ('13S_PUMP', 5)

LVL_10S = ('10S_LVL', 6)
VALVE_IN_10S = ('10S_VALVE_IN', 6)
VALVE_OUT_10S = ('10S_VALVE_OUT', 6)
PUMP_10S = ('10S_PUMP', 6)


PP_RESCALING_HOURS = 100
PP_PERIOD_SEC = 0.2
PP_SAMPLES = int(PLC_PERIOD_SEC / PP_PERIOD_SEC) * PLC_SAMPLES
PP_PERIOD_HOURS = (PP_PERIOD_SEC / 3600.0) * PP_RESCALING_HOURS

FLOWRATE = 0.1


def calculate_angle(A, B):
    a = 1.5
    b = -2.25
    c = -12
    return a * A + b * B + c


class VesselBallast(Device):
    def __init__(self, name, protocol, state, disk={}, memory={}):
        super().__init__(name, protocol, state, disk, memory)
        self.level_10S = None
        self.level_13S = None
        self.level_13P = None
        self.level_10P = None
        self.roll_angle = None
        self.pitch_angle = None

    def pre_loop(self):
        print("DEBUG entering pre loop ")

        # Setup 10S
        self.level_10S = self.set(LVL_10S, 5)
        self.set(VALVE_IN_10S, 1)
        self.set(VALVE_OUT_10S, 0)
        self.set(PUMP_10S, 0)

        # Setup 10S
        self.level_13S = self.set(LVL_13S, 5)
        self.set(VALVE_IN_13S, 0)
        self.set(VALVE_OUT_13S, 0)
        self.set(PUMP_13S, 0)

        # Setup 10S
        self.level_13P = self.set(LVL_13P, 5)
        self.set(VALVE_IN_13P, 0)
        self.set(VALVE_OUT_13P, 0)
        self.set(PUMP_13P, 0)

        # Setup 10P
        self.level_10P = self.set(LVL_10P, 5)
        self.set(VALVE_IN_10P, 0)
        self.set(VALVE_OUT_10P, 1)
        self.set(PUMP_10P, 1)



    def main_loop(self):
        print("DEBUG entering main loop")

        count = 0
        columns = ['Time', '10S_LVL', '10S_VALVE_IN', '10S_VALVE_OUT', '10S_PUMP', '10P_LVL', '10P_VALVE_IN',
                   '10P_VALVE_OUT', '10P_PUMP']
        df = pd.DataFrame(columns=columns)
        timestamp = 0
        while count <= PP_SAMPLES:
            level_10S, level_10P = self.level_10S, self.level_10P

            # INFLOW
            valve_in_10S = self.get(VALVE_IN_10S)
            print(f"10S Valve: {valve_in_10S}")
            if int(valve_in_10S) == 1:
                level_10S = level_10S + FLOWRATE

            valve_in_10P = self.get(VALVE_IN_10P)
            if int(valve_in_10P) == 1:
                level_10P = level_10P + FLOWRATE

            # OUTFLOW
            pump_10S = self.get(PUMP_10S)
            if int(pump_10S) == 1:
                level_10S = level_10S - FLOWRATE

            pump_10P = self.get(PUMP_10P)
            if int(pump_10P) == 1:
                level_10P = level_10P - FLOWRATE

            self.level_10S = self.set(LVL_10S, level_10S)
            self.level_10P = self.set(LVL_10P, level_10P)

            self.roll_angle = self.set(ROLL_ANGLE, calculate_angle(self.level_10S, self.level_10P))

            # TODO Calculate


            print(f"{datetime.now()} Roll: {self.roll_angle:.3f} Pitch: 0 {self.level_10S:.3f}  | 10P: {self.level_10P:.3f}")

            if self.level_10S >= Tank10S.levels["HH"]:
                print("WARNING: Tank 10S is above extreme level")

            if self.level_10P >= Tank10P.levels["HH"]:
                print("WARNING: Tank 10P is above extreme level")

            new_data = pd.DataFrame(data=[
                [round(timestamp, 3), self.get(LVL_10S), self.get(VALVE_IN_10S), self.get(VALVE_OUT_10S),
                 self.get(PUMP_10S), self.get(LVL_10P), self.get(VALVE_IN_10P), self.get(VALVE_OUT_10P),
                 self.get(PUMP_10P)]], columns=columns)
            df = pd.concat([df, new_data])
            df.to_csv("logs/data.csv", index=False)
            count += 1
            time.sleep(PP_PERIOD_SEC)
            timestamp += PP_PERIOD_SEC

    def _start(self):
        self.pre_loop()
        self.main_loop()

    def _stop(self):
        if self.protocol['mode'] > 0:
            self._protocol._server_subprocess.kill()


if __name__ == "__main__":
    pp = VesselBallast(
        name="VesselBallast",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=None,
    )
