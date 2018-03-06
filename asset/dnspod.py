#coding:utf-8
import json
import requests
import logging
from django.conf import settings

from asset.models import ResolveAudit

logger = logging.getLogger(__name__)

headers = { 
    "Content-Type":"application/x-www-form-urlencoded",
    "Accept":"text/json",
    "User-Agent":"dnspod-python/0.01 (im@chuangbo.li; DNSPod.CN API v2.8)"
} 

LINE = ((u'默认', u'默认'), (u'联通', u'联通'))
TYPE = (('A', 'A'), ('CNAME', 'CNAME'))

RETURN = {
    "-1": u"接口登录失败",
    "-2": u"接口使用超出限制",
    "-8": u"登录失败过多,暂时封禁",
    "1": u"操作成功",
    "2": u"请求方法错误",
    "3": u"接口未知错误",
    "6": u"域名ID不存在",
    "8": u"记录不存在",
    "22": u"子域名不合法",
    "23": u"子域名级数超出限制",
    "24": u"泛解析子域名错误",
    "26": u"记录线路错误",
    "27": u"记录类型错误",
    "31": u"存在冲突的记录(A记录、CNAME记录、URL记录不能共存)",
    "32": u"记录的TTL值超出了限制",
    "34": u"记录值非法",
    "36": u"@主机的NS纪录只能添加默认线路",
    "83": u"接口被锁定,无法操作",
    "85": u"账户开启了登录保护,当前IP不被允许请求",
}

def request(url, data):
    url = "%s%s" % (settings.DNSPOD_URL, url)
    data["login_email"] = settings.DNSPOD_USER
    data["login_password"] = settings.DNSPOD_PASS
    data["format"] = "json"
    logger.info("POST %s Body=%s" % (url, data))
    return requests.post(url, data=data, headers=headers)

def DomainInfo(domain):
    data = {"domain": domain}
    resp = request('/Domain.Info', data)
    return resp.json()

def RecordInfo(domain_id, record_id):
    data = {"domain_id": domain_id, "record_id": record_id}
    resp = request('/Record.Info', data)
    return resp.json()

def RecordList(domain, sub_domain):
    data = {"domain": domain, "sub_domain": sub_domain}
    resp = request('/Record.List', data)
    return resp.json()

def RecordCreate(domain, value, sub_domain, record_line, record_type="A", ttl="600", **kwargs):
    data = {"domain": domain, "sub_domain": sub_domain, "record_line": record_line, \
            "record_type": record_type, "ttl": ttl, "value": value}
    resp = request('/Record.Create', data)
    return resp.json()

def RecordModify(domain, record_id, value, sub_domain, record_line, record_type="A", ttl="600", **kwargs):
    data = {"domain": domain, "sub_domain": sub_domain, "record_line": record_line, \
            "record_id": record_id, "record_type": record_type, "ttl": ttl, "value": value}
    resp = request('/Record.Modify', data)
    return resp.json()

def RecordRemove(record_id, domain=None, domain_id=None):
    if domain_id:
        data = {"domain_id": domain_id, "record_id": record_id}
    else:
        data = {"domain": domain, "record_id": record_id}
    resp = request('/Record.Remove', data)
    return resp.json()

def veritify(result):
    code = result["status"]["code"]
    if code == "1":
        return True, RETURN.get(code, u"未知错误")
    return False, RETURN.get(code, u"未知错误")
    
def handler(request, **kwargs):
    # 解析CNAME, 默认双解析
    dr = _handler(request, **kwargs)
    dr.resolve()

class _handler(object):
    def __init__(self, request, domain, sub_domain, value, record_type="A", record_line=u"默认", ttl="600", **kwargs):
        self.request = request
        self.domain = domain
        self.sub_domain = sub_domain
        self.value = value
        self.record_type = record_type
        self.record_line = record_line
        self.ttl = ttl
        self.kwargs = kwargs

    def resolve(self):
        record_list = self._list()
        if record_list["info"]["record_total"] == "0":
            self._resolve()
        else:
            for record in record_list["records"]:
                rr = self._remove(record["id"])
                if veritify(rr)[0]:
                    ra = ResolveAudit(userid=self.request.user.uuid, username=self.request.user.name, \
                            record="%s.%s" % (record["name"], record_list["domain"]["name"]),
                            description=u"删除 %(type)s 记录 %(line)s 线路 值 %(value)s" % record)
                    ra.save()
            self._resolve()

    def _resolve(self):
        if self.record_type == "CNAME":
            rr = self._create()
            if veritify(rr)[0]:
                ra = ResolveAudit(userid=self.request.user.uuid, username=self.request.user.name, \
                        record="%s.%s" % (self.sub_domain, self.domain),
                        description=u"添加 %(type)s 记录 %(line)s 线路 值 %(value)s" % \
                                {"type":self.record_type,"line":self.record_line,"value":self.value})
                ra.save()
        else:
            for value in self.value:
                rr = self._create(value)
                if veritify(rr)[0]:
                    ra = ResolveAudit(userid=self.request.user.uuid, username=self.request.user.name, \
                            record="%s.%s" % (self.sub_domain, self.domain),
                            description=u"添加 %(type)s 记录 %(line)s 线路 值 %(value)s" % \
                                    {"type":self.record_type,"line":self.record_line,"value":value})
                    ra.save()

    def _list(self):
        return RecordList(self.domain, self.sub_domain)

    def _create(self, value=None):
        if value:
            return RecordCreate(self.domain, value, self.sub_domain, self.record_line, self.record_type)
        return RecordCreate(self.domain, self.value, self.sub_domain, self.record_line, self.record_type)

    def _remove(self, record_id):
        return RecordRemove(record_id, domain=self.domain)
