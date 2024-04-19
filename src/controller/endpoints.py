import json
import pprint

from ryu.app.wsgi import ControllerBase, route
from webob import Response


class CyberDeceptionEndpoints(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(CyberDeceptionEndpoints, self).__init__(req, link, data, **config)
        self.app = data['app']

    @route('is_ready', '/is_ready', methods=['GET'])
    def is_ready(self, req, **kwargs):
        is_ready = self.app.packet_received
        # if is_ready:
        #     self.app.call_mtd()
        body = json.dumps({'is_ready': is_ready})
        return Response(content_type='application/json', body=body, charset='utf-8')

    @route('host_ips', '/hosts', methods=['GET'])
    def host_ips(self, req, **kwargs):
        prod_ips = self.app.get_production_hosts()
        scada_ips = self.app.get_scada_hosts()

        content = {}
        for k, v in prod_ips.items():
            content[v.hostname] = v.dynamic_ip
        for k,v, in scada_ips.items():
            content[v.hostname] = v.dynamic_ip

        body = json.dumps(content)
        return Response(content_type='application/json', body=body, charset='utf')

    @route('prod_ips', '/prod', methods=['GET'])
    def prod_ips(self, req, **kwargs):
        prod_ips = self.app.get_production_hosts()
        content = {}
        for k, v in prod_ips.items():
            content[v.hostname] = v.dynamic_ip
        body = json.dumps(content)
        return Response(content_type='application/json', body=body, charset='utf')

    @route('scada_ips', '/scada', methods=['GET'])
    def scada_ips(self, req, **kwargs):
        scada_ips = self.app.get_scada_hosts()
        content = {}
        for k, v in scada_ips.items():
            content[v.hostname] = v.dynamic_ip
        body = json.dumps(content)
        return Response(content_type='application/json', body=body, charset='utf')
