#coding:utf-8
import time
import json
import datetime

from django_redis import get_redis_connection

from surge.models import UserAccounts
from surge.celery import celery

from asset.models import Assets
from asset.pyzabbix import Zabbix

from operation.models import Apps, PlatForms

channel = get_redis_connection('default')

def unicast(userid, msg, success):
    channel.publish('TASK.NOTIFICATION', json.dumps({"userid": userid, "success": success, "msg": msg, "time": datetime.datetime.now().strftime('%H:%M:%S')}))

@celery.task(name="EnableMonitor", ignore_result=True)
def EnableMonitor(userid, uuids):
    zabbix = Zabbix()
    for instance in Assets.objects.filter(deleted=False).filter(pk__in=uuids).all():
        if zabbix.enable_monitor(instance.uuid) is None:
            _msg = u"[监控] %s 启用失败" % instance.remote_ip
            unicast(userid, _msg, False)
        else:
            _msg = u"[监控] %s 启用成功" % instance.remote_ip
            unicast(userid, _msg, True)

@celery.task(name="DisableMonitor", ignore_result=True)
def DisableMonitor(userid, uuids):
    zabbix = Zabbix()
    for instance in Assets.objects.filter(deleted=False).filter(pk__in=uuids).all():
        if zabbix.disable_monitor(instance.uuid) is None:
            _msg = u"[监控] %s 禁用失败" % instance.remote_ip
            unicast(userid, _msg, False)
        else:
            _msg = u"[监控] %s 禁用成功" % instance.remote_ip
            unicast(userid, _msg, True)


@celery.task(name="DeleteUsers", ignore_result=True)
def DeleteUsers(userid, uuids):
    if not isinstance(uuids, list):
        uuids = uuids.split(",")
    users = UserAccounts.objects.filter(pk__in=uuids)
    try:
        users.delete()
        _msg = u"[用户] %s 删除成功" % users.account
        unicast(userid, _msg, True)
    except Exception,e:
        _msg = u"[用户] %s 删除失败" % users.account
        unicast(userid, _msg, False)

@celery.task(name="DeleteApps", ignore_result=True)
def DeleteApps(userid, uuids):
    if not isinstance(uuids, list):
        uuids = uuids.split(",")
    for uuid in uuids:
        try:
            app = Apps.objects.get(pk=uuid)
        except:
            continue
        if app.online:
            # 已经上线,不能删除
            _msg = u"[应用] %s 已经上线,不能删除" % app.appalias
            unicast(userid, _msg, False)
            continue
        if app.hosts.first():
            # 还有服务器,不能删除
            _msg = u"[应用] %s 下还有服务器资产,不能删除" % app.appalias
            unicast(userid, _msg, False)
            continue
        app.delete()
        _msg = u"[应用] %s 删除成功" % app.appalias
        unicast(userid, _msg, True)

@celery.task(name="DeletePlatForms", ignore_result=True)
def DeletePlatForms(userid, uuids):
    if not isinstance(uuids, list):
        uuids = uuids.split(",")
    for uuid in uuids:
        try:
            plat = PlatForms.objects.get(pk=uuid)
        except:
            continue
        if plat.hosts.first():
            # 还有服务器,不能删除
            _msg = u"[平台] %s 下还有服务器资产,不能删除" % plat.platalias
            unicast(userid, _msg, False)
            continue
        plat.delete()
        _msg = u"[平台] %s 删除成功" % plat.platalias
        unicast(userid, _msg, True)

@celery.task(name="DeleteAccelerate", ignore_result=True)
def DeleteAccelerate(userid, uuids):
    if not isinstance(uuids, list):
        uuids = uuids.split(",")
    try:
        accs = AccelerateCDN.objects.get(pk__in=uuids)
        accs.delete()
        _msg = u"[CDN域名] 删除成功"
        unicast(userid, _msg, True)
    except:
        _msg = u"[CDN域名] 删除失败"
        unicast(userid, _msg, False)

@celery.task(name="DeleteCDN", ignore_result=True)
def DeleteCDN(userid, uuids):
    if not isinstance(uuids, list):
        uuids = uuids.split(",")
    for uuid in uuids:
        try:
            cdn = CDNCompany.objects.get(pk=uuid)
            if cdn.cdn.first():
                _msg = u"[CDN厂商] %s 还有域名加速,不能删除"
                unicast(userid, _msg, False)
                continue
            else:
                cdn.delete()
                _msg = u"[CDN厂商] %s 删除成功"
                unicast(userid, _msg, True)
        except:
            _msg = u"[CDN域名] 删除失败"
            unicast(userid, _msg, False)

@celery.task(name="BulkMonitor", ignore_result=True)
def BulkMonitor(userid, hostids, templateids, groupid, proxyid):
    zabbix = Zabbix()
    for hostid in hostids:
        try:
            host = Assets.objects.get(pk=hostid)
        except:
            continue
        if zabbix.create_monitor(hostid, groupid, proxyid, templateids):
            _msg = u"[监控] %s 创建成功" % host.public_ip.split(",")[0]
            unicast(userid, _msg, True)
        else:
            _msg = u"[监控] %s 创建失败" % host.public_ip.split(",")[0]
            unicast(userid, _msg, False)
