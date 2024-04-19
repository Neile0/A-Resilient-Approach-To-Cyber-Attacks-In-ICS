import pprint
import subprocess
import time
import argparse
from datetime import datetime

import requests


def check_ip_reachability(ip_address):
    try:
        # Use the ping command to check if the IP address is reachable
        output = subprocess.check_output(["ping", "-c", "1", ip_address], stderr=subprocess.STDOUT, timeout=5,
                                         universal_newlines=True)
        if "1 packets transmitted, 1 received" in output:
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False

def get_hosts():
    endpoint = f'http://192.168.1.1:8080/hosts'
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error querying endpoint: {e}")


def main(host, ip_address):
    while True:
        if check_ip_reachability(ip_address):
            print(f"{datetime.now()} {ip_address} is reachable.")
        else:
            print(f"{datetime.now()} {ip_address} is not reachable.")
            hosts = get_hosts()
            ip_address = hosts[host]

        time.sleep(0.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check host reachability.")
    parser.add_argument("host", help="host to check")

    args = parser.parse_args()
    host = args.host

    hosts = get_hosts()
    # pprint.pprint(hosts)

    ip = hosts[host]

    main(host, ip)