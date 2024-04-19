import time
import random
import os
import sys
import logging

from minicps.devices import HMI


class MotionsHMI(HMI):
    tags = (
        ('ROLL_ANGLE', 7, 'REAL'),
        ('PITCH_ANGLE', 7, 'REAL'),
    )

    server = {
        'address': '192.168.1.10',
        'tags': tags
    }

    protocol = {
        'name': 'enip',
        'mode': 1,
        'server': server
    }

    def pre_loop(self, sleep=0.1):
        time.sleep(sleep)

    def main_loop(self, **kwargs):
        clear = lambda: os.system('clear')
        try:
            while True:
                # Get live value
                live_value = get_live_value()

                # Print live value without newline

                logging.info(f"\rLive Value: {live_value}")
                

                # Flush the output to make sure it's printed immediately

                sys.stdout.flush()

                # Wait for some time before printing the next value
                time.sleep(1)


        except KeyboardInterrupt:
            # Handle Ctrl+C to exit the loop
            print("\nExiting...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename='/vagrant/src/testbed/logs/motions_hmi.log', filemode="w")
    client = MotionsHMI(
        name="motionsHMI",
        state={'name': "vessel_cps", 'path': "/vagrant/vessel_cps_db.sqlite"},
        protocol=MotionsHMI.protocol
    )