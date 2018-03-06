#coding:utf-8
from django.db import models

from surge.common import utils

class Contracts(utils.AuditModel):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"合同名", max_length=100)
    number = models.CharField(u"合同号", max_length=255)
    expire_date = models.DateTimeField(u"合同期限", help_text=u"格式:YY-MM-DD hh:mm:ss")
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "asset"
        ordering = ['name']

    def __unicode__(self):
        return self.number
