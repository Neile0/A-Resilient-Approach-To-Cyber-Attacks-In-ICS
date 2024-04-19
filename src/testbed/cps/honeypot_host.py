import logging
from scapy.all import sniff, IP
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to log incoming IP packets
def log_incoming_packets(packet):
    if IP in packet:
        logging.info(f"{datetime.now()} Incoming packet from {packet[IP].src} to {packet[IP].dst} - Protocol: {packet[IP].proto}")

if __name__ == "__main__":
    try:
        logging.info("Starting packet capture. Press Ctrl+C to stop...")
        sniff(filter="ip", prn=log_incoming_packets, store=0)
    except KeyboardInterrupt:
        logging.info("Packet capture stopped.")