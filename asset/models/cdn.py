#coding:utf-8
from django.db import models
from surge.common import utils

class CDNCompany(utils.AuditModel):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"CND厂商", max_length=100)
    manage = models.URLField(u"管理后台", max_length=128)
    remark = models.TextField(u"备注", blank=True)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    audit_fields = ("name", "manage", "remark")

    class Meta:
        app_label = "asset"
        ordering = ['name']

    def __unicode__(self):
        return self.name

class AccelerateCDN(utils.AuditModel):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    domain = models.CharField(u"加速域名", max_length=255)
    division = models.ForeignKey('asset.Divisions', verbose_name=u"所属事业部", related_name='cdn')
    app = models.ForeignKey('operation.Apps', verbose_name=u"所属应用", related_name='cdn')
    company = models.ForeignKey(CDNCompany, verbose_name=u"CDN厂商", related_name='cdn')
    cname = models.CharField(u"CNAME", max_length=255, blank=True)
    source = models.CharField(u"CDN源", max_length=255, blank=True)
    remark = models.TextField(u"备注", blank=True)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "asset"
        ordering = ['domain',]

    def __unicode__(self):
        return self.domain

class RegisterDomain(utils.AuditModel):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    domain = models.CharField(u"域名", max_length=255)
    register_site = models.CharField(u"注册网站", max_length=255)
    register_company = models.CharField(u"注册公司", max_length=255)
    register_subject = models.CharField(u"注册主体", max_length=255)
    register_date = models.CharField(u"注册日期", max_length=255)
    expire_date = models.CharField(u"过期日期", max_length=255)
    ipc_name = models.CharField(u"备案主体", max_length=255)
    ipc_id = models.CharField(u"备案号", max_length=255)
    ipc_ip = models.CharField(u"备案IP", max_length=255)
    ipc_phone = models.CharField(u"备案手机", max_length=255, blank=True)
    ipc_email = models.CharField(u"备案邮箱", max_length=255, blank=True)
    resolve_driver = models.CharField(u"解析驱动", max_length=255)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "asset"
        ordering = ['domain']

    def __unicode__(self):
        return self.domain


class ResolveAudit(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    userid = models.CharField(u"用户ID", max_length=50)
    username = models.CharField(u"用户名", max_length=50)
    record = models.CharField(u"DNS", max_length=255)
    description = models.CharField(u"详情", max_length=255)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "asset"
        ordering = ['-created_at',]

    def __unicode__(self):
        return self.record
