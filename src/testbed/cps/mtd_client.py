from datetime import datetime
import pprint
import subprocess
import time

import requests

from minicps.devices import Device

IP_PLC10S = ('IP_PLC10S', 1)
IP_PLC10P = ('IP_PLC10P', 1)
IP_PLC13S = ('IP_PLC13S', 1)
IP_PLC13P = ('IP_PLC13P', 1)
IP_PLCI = ('IP_PLCI', 1)
IP_BALLAST_HMI = ('IP_BALLAST_HMI', 1)
IP_MOTIONS_HMI = ('IP_MOTIONS_HMI', 1)
IP_SCADA_SERVER = ('IP_SCADA_SERVER', 1)

class ICSMTD(Device):
    def __init__(self, name, protocol, state, disk={}, memory={}):
        super().__init__(name, protocol, state, disk, memory)
        self.ip_motions_hmi = self.set(IP_MOTIONS_HMI, 10)
        self.ip_ballast_hmi = self.set(IP_BALLAST_HMI, 20)
        self.ip_scada_server = self.set(IP_SCADA_SERVER, 30)

        self.ip_plc10P = self.set(IP_PLC10P, 40)
        self.ip_plc13P = self.set(IP_PLC13P, 50)
        self.ip_plcI = self.set(IP_PLCI, 60)
        self.ip_plc13S = self.set(IP_PLC13S,70)
        self.ip_plc10S = self.set(IP_PLC10S, 80)

    def pre_loop(self):
        print(f"DEBUG ICSMTD entering pre loop")


    def main_loop(self):
        print(f"DEBUG ICSMTD entering main loop")

        while True:
            prod_ips = get_prod_hosts()

            local_prod_ips = []
            local_prod_ips.append(self.get(IP_PLC10P))
            local_prod_ips.append(self.get(IP_PLC13P))
            local_prod_ips.append(self.get(IP_PLC13S))
            local_prod_ips.append(self.get(IP_PLC10S))
            local_prod_ips.append(self.get(IP_PLCI))

            new_prod_ips = []
            new_prod_ips.append(int(prod_ips['plc10P'].split('.')[-1]))
            new_prod_ips.append(int(prod_ips['plc13P'].split('.')[-1]))
            new_prod_ips.append(int(prod_ips['plc13S'].split('.')[-1]))
            new_prod_ips.append(int(prod_ips['plc10S'].split('.')[-1]))
            new_prod_ips.append(int(prod_ips['plcI'].split('.')[-1]))

            scada_ips = get_scada_hosts()
            local_scada_ips = []
            local_scada_ips.append(self.get(IP_MOTIONS_HMI))
            local_scada_ips.append(self.get(IP_BALLAST_HMI))
            local_scada_ips.append(self.get(IP_SCADA_SERVER))

            new_scada_ips = []
            new_scada_ips.append(int(scada_ips['motionsHMI'].split('.')[-1]))
            new_scada_ips.append(int(scada_ips['ballastHMI'].split('.')[-1]))
            new_scada_ips.append(int(scada_ips['scadaServer'].split('.')[-1]))

            while local_prod_ips == new_prod_ips and local_scada_ips == new_scada_ips:
                print(f"{local_prod_ips == new_prod_ips} & {local_scada_ips == new_scada_ips}")

                prod_ips = get_prod_hosts()
                new_prod_ips = []
                new_prod_ips.append(int(prod_ips['plc10P'].split('.')[-1]))
                new_prod_ips.append(int(prod_ips['plc13P'].split('.')[-1]))
                new_prod_ips.append(int(prod_ips['plc13S'].split('.')[-1]))
                new_prod_ips.append(int(prod_ips['plc10S'].split('.')[-1]))
                new_prod_ips.append(int(prod_ips['plcI'].split('.')[-1]))

                scada_ips = get_scada_hosts()
                local_scada_ips = []
                local_scada_ips.append(self.get(IP_MOTIONS_HMI))
                local_scada_ips.append(self.get(IP_BALLAST_HMI))
                local_scada_ips.append(self.get(IP_SCADA_SERVER))

                new_scada_ips = []
                new_scada_ips.append(int(scada_ips['motionsHMI'].split('.')[-1]))
                new_scada_ips.append(int(scada_ips['ballastHMI'].split('.')[-1]))
                new_scada_ips.append(int(scada_ips['scadaServer'].split('.')[-1]))
                time.sleep(0.5)

            self.ip_plc10P = self.set(IP_PLC10P, int(prod_ips['plc10P'].split('.')[-1]))
            self.ip_plc13P = self.set(IP_PLC13P, int(prod_ips['plc13P'].split('.')[-1]))
            self.ip_plcI = self.set(IP_PLCI, int(prod_ips['plcI'].split('.')[-1]))
            self.ip_plc13S = self.set(IP_PLC13S, int(prod_ips['plc13S'].split('.')[-1]))
            self.ip_plc10S = self.set(IP_PLC10S, int(prod_ips['plc10S'].split('.')[-1]))

            print(f"{datetime.now()} ICS IPs {self.get(IP_PLC10P)} {self.get(IP_PLC13P)} {self.get(IP_PLCI)} {self.get(IP_PLC13S)} {self.get(IP_PLC10S)}")

            self.ip_motions_hmi = self.set(IP_MOTIONS_HMI, int(scada_ips['motionsHMI'].split('.')[-1]))
            self.ip_ballast_hmi = self.set(IP_BALLAST_HMI, int(scada_ips['ballastHMI'].split('.')[-1]))
            self.ip_scada_server = self.set(IP_SCADA_SERVER, int(scada_ips['scadaServer'].split('.')[-1]))

            print(f"{datetime.now()} SCADA IPs {self.get(IP_MOTIONS_HMI)} {self.get(IP_BALLAST_HMI)} {self.get(IP_SCADA_SERVER)} ")

    def _start(self):
        self.pre_loop()
        self.main_loop()

    def _stop(self):
        if self.protocol['mode'] > 0:
            self._protocol._server_subprocess.kill()

def get_prod_hosts():
    endpoint = f'http://192.168.1.1:8080/prod'
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error querying endpoint: {e}")

def get_scada_hosts():
    endpoint = f'http://192.168.1.1:8080/scada'
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error querying endpoint: {e}")

def get_req():
    endpoint = f'http://192.168.1.1:8080/is_ready'

    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            is_ready = data.get('is_ready')
            if is_ready is not None:
                print(f"Successful call to IS READY: {is_ready}")
                return is_ready
            else:
                print("Unexpected response format")
                return None
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error querying endpoint: {e}")
        return None
    return False

def ping_ip(ip_address):
    try:
        # Run the ping command
        process = subprocess.Popen(['ping', '-c', '4', ip_address], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)

        # Read and print the output line by line
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Check if the command was successful
        if process.returncode == 0:
            print(f'Ping to {ip_address} successful.')
        else:
            print(f'Ping to {ip_address} failed.')

    except Exception as e:
        print(f'An error occurred: {e}')


if __name__ == "__main__":
    mtd_client = ICSMTD(
        name="VesselBallast",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=None,
    )

