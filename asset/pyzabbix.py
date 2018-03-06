#coding:utf-8
import json
import urllib
import requests
import logging
from StringIO import StringIO
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surge.settings')

from django.conf import settings
from django.core.cache import cache

from asset.models import Assets
logger = logging.getLogger(__name__)

class Zabbix(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        self.api = settings.ZABBIX_URL + "/api_jsonrpc.php"
        self.grap = settings.ZABBIX_URL + "/chart2.php"
        self.data = {"jsonrpc":"2.0","method":"","params":{},"id":1,"auth":""}
        self.http = requests.post

    def login(self):
        token = cache.get("zabbix:%s:token" % settings.ZABBIX_USER)
        if token:
            return token
        data = self.data.copy()
        data["method"] = "user.login"
        data["params"] = {"user": settings.ZABBIX_USER, "password": settings.ZABBIX_PASSWORD}
        token = self.http(self.api, headers=self.headers, data=json.dumps(data)).json()["result"]
        cache.set("zabbix:%s:token" % settings.ZABBIX_USER, token, timeout=3600)
        return token

    def api_call(self, data):
        try:
            logger.info("POST %s Body=%s" % (self.api, data))
            data["auth"] = self.login()
            req = self.http(self.api, headers=self.headers, data=json.dumps(data)).json()
        except Exception,e:
            logger.error(e, exc_info=True)
            return None
        logger.info("Response=%s" % req)
        return req.get("result", None)

    def instance(self, uuid):
        return Assets.objects.get(pk=uuid)

    def hostid(self, uuid):
        instance = self.instance(uuid)
        if instance:
            if instance.hostid:
                return instance.hostid
            data = self.data.copy()
            data["method"] = "host.get"
            data["params"] = {"output":"hostid","filter":{"name":instance.remote_ip}}
            msg = self.api_call(data)
            if msg:
                instance.hostid = msg[0]["hostid"]
                instance.save(update_fields=["hostid"])
                return msg[0]["hostid"]
        logger.error("Can not found host by uuid=%s" % uuid)
        return ""

    def used_template(self, uuid):
        data = self.data.copy()
        data["method"] = "template.get"
        data["params"] = {"output":["name", "templateid"], "hostids":self.hostid(uuid)}
        return self.api_call(data)

    def template_list(self):
        data = self.data.copy()
        data["method"] = "template.get"
        data["params"] = {"output":["name", "templateid"]}
        return self.api_call(data)

    def proxy_list(self):
        data = self.data.copy()
        data["method"] = "proxy.get"
        data["params"] = {"output":["host", "proxyid"]}
        return self.api_call(data)

    def group_list(self):
        data = self.data.copy()
        data["method"] = "hostgroup.get"
        data["params"] = {"output":["groupid","name"]}
        return self.api_call(data)

    def exists_monitor(self, uuid):
        data = self.data.copy()
        instance = self.instance(uuid)
        if instance:
            data["method"] = "host.exists"
            if instance.hostid:
                data["params"] = {"hostid": instance.hostid}
            else:
                data["params"] = {"host": instance.remote_ip}
            return self.api_call(data)
        logger.error("Can not found host by uuid=%s" % uuid)
        return False
    
    def create_monitor(self, uuid, groupid, proxy_hostid, templateids):
        data = self.data.copy()
        if self.exists_monitor(uuid):
            logger.warning("host %s already monitor, not do this" % uuid)
            return
        instance = self.instance(uuid)
        if not instance:
            logger.warning("host %s not exists, not do this" % uuid)
            return
        data["method"] = "host.create"
        data["params"] = {"host": instance.remote_ip,
                          "interfaces": [{"type":1,"main":1,"useip":1,"ip":instance.remote_ip,"dns":"","port":"10050"}],
                          "groups": [{"groupid": groupid}],
                          "proxy_hostid": proxy_hostid,
                          "templates": [{"templateid":tid} for tid in templateids],
                         }
        data = self.api_call(data)
        if "hostids" in data:
            instance.hostid = data["hostids"][0]
            instance.save(update_fields=["hostid"])
        return data

    def delete_monitor(self, uuids):
        data = self.data.copy()
        data["method"] = "host.delete"
        data["params"] = uuids
        return self.api_call(data)

    def update_host_template(self, uuid, groupid, proxy_hostid, templateids):
        data = self.data.copy()
        data["method"] = "host.update"
        data["params"] = {"hostid": self.hostid(uuid), 
                          "groups": [{"groupid": groupid}],
                          "proxy_hostid": proxy_hostid,
                          "templates": [{"templateid":tid} for tid in templateids]}
        return self.api_call(data)

    def graph_info(self, uuid):
        data = self.data.copy()
        data["method"] = "graph.get"
        data["params"] = {"output":["name", "templateid", "height", "width", "graphid", "hosts", "show_triggers", "show_legend"], "hostids": self.hostid(uuid)}
        return self.api_call(data)

    def graph(self, query_params):
        cookies = dict(zbx_sessionid="%s" % self.login())
        try:
            r = self.http("%s?%s" % (self.grap, query_params), cookies=cookies)
            data = StringIO(r.content)
            return data.read()
        except Exception,e:
            logger.error(e, exc_info=True)
            return ""

    def disable_monitor(self, uuid):
        data = self.data.copy()
        data["method"] = "graph.get"
        data["params"] = {"hostid": self.hostid(uuid), "status": 1}
        return self.api_call(data)

    def enable_monitor(self, uuid):
        data = self.data.copy()
        data["method"] = "graph.get"
        data["params"] = {"hostid": self.hostid(uuid), "status": 0}
        return self.api_call(data)

    def monitor_exists(self, uuid):
        data = self.data.copy()
        data["method"] = "host.exists"
        data["params"] = {"host": uuid}
        return self.api_call(data)

    def monitor_status(self, uuid):
        data = self.data.copy()
        data["method"] = "host.get"
        data["params"] = {"hostids": self.hostid(uuid), "output":["status"]}
        return self.api_call(data)


if __name__ == '__main__':
    zabbix = Zabbix()
    print zabbix.login()
