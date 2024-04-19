from sqlite3 import OperationalError

from minicps.states import SQLiteState

from cps import VesselCPS

SCHEMA = """
CREATE TABLE vessel_cps (
    name TEXT NOT NULL,
    pid INTEGER NOT NULL,
    value TEXT,
    PRIMARY KEY (name, pid)
);
"""
SCHEMA_INIT = """
    INSERT INTO vessel_cps VALUES ('IP_MOTIONS_HMI', 1, '10');
    INSERT INTO vessel_cps VALUES ('IP_BALLAST_HMI', 1, '20');
    INSERT INTO vessel_cps VALUES ('IP_SCADA_SERVER', 1, '30');

    INSERT INTO vessel_cps VALUES ('IP_PLC10P', 1, '40');
    INSERT INTO vessel_cps VALUES ('IP_PLC13P', 1, '50');
    INSERT INTO vessel_cps VALUES ('IP_PLCI', 1, '60');
    INSERT INTO vessel_cps VALUES ('IP_PLC13S', 1, '70');
    INSERT INTO vessel_cps VALUES ('IP_PLC10S', 1, '80');
    
    INSERT INTO vessel_cps VALUES ('10P_LVL', 2, '5');
    INSERT INTO vessel_cps VALUES ('10P_VALVE_IN', 2, '0');
    INSERT INTO vessel_cps VALUES ('10P_VALVE_OUT', 2, '0');
    INSERT INTO vessel_cps VALUES ('10P_PUMP', 2, '0');
    
    INSERT INTO vessel_cps VALUES ('13P_LVL', 3, '5');
    INSERT INTO vessel_cps VALUES ('13P_VALVE_IN', 3, '0');
    INSERT INTO vessel_cps VALUES ('13P_VALVE_OUT', 3, '0');
    INSERT INTO vessel_cps VALUES ('13P_PUMP', 3, '0');
    
    INSERT INTO vessel_cps VALUES ('ROLL_ANGLE', 4, '0');
    INSERT INTO vessel_cps VALUES ('PITCH_ANGLE', 4, '0');
    
    INSERT INTO vessel_cps VALUES ('13S_LVL', 5, '5');
    INSERT INTO vessel_cps VALUES ('13S_VALVE_IN', 5, '0');
    INSERT INTO vessel_cps VALUES ('13S_VALVE_OUT', 5, '0');
    INSERT INTO vessel_cps VALUES ('13S_PUMP', 5, '0');
    
    
    INSERT INTO vessel_cps VALUES ('10S_LVL', 6, '5');
    INSERT INTO vessel_cps VALUES ('10S_VALVE_IN', 6, '0');
    INSERT INTO vessel_cps VALUES ('10S_VALVE_OUT', 6, '0');
    INSERT INTO vessel_cps VALUES ('10S_PUMP', 6, '0');
"""


def run():
    try:
        SQLiteState._create(VesselCPS.path, SCHEMA)
        print(f"Database Created")
        SQLiteState._init(VesselCPS.path, SCHEMA_INIT)
        print("Database Initialised")
        print(f"{VesselCPS.path} successfully created.")
    except OperationalError:
        print(f"{VesselCPS.path} already exists")


if __name__ == '__main__':
    run()
