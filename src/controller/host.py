from enum import Enum
from pprint import pformat


class NetworkType(Enum):
    CORPORATE = 1
    SCADA = 2
    PRODUCTION = 3

    @staticmethod
    def parse_string(string):
        if string == "CORP":
            return NetworkType.CORPORATE
        if string == "SCADA":
            return NetworkType.SCADA
        if string == "PROD":
            return NetworkType.PRODUCTION

        raise ValueError("")


class Host:
    def __init__(self, name, ip, network=NetworkType.CORPORATE):
        self.hostname = name
        self.physical_ip = ip
        self.network = NetworkType.parse_string(network)
        self.dynamic_ip = ""

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)
