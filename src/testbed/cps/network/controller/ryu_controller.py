import requests
from mininet.node import RemoteController

IP = "192.168.1.1"
PORT = 6653


def RyuController():
    print(f"Ryu Controller at {IP}:{PORT}")
    return RemoteController("controller", ip=IP, port=PORT, protocols="OpenFlow13")


def is_ready():
    endpoint = f'http://{IP}:8080/is_ready'

    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            is_ready = data.get('is_ready')
            if is_ready is not None:
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
