#coding:utf-8
from datetime import datetime
from collections import defaultdict

from django.db import models
from django.db.models.base import Model

from surge.common import utils

class Audit(models.Model):
    ACTION_TYPE=(
        (1, u"创建"),
        (2, u"修改"),
        (3, u"删除"),
    )
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    resource_id = models.CharField(u'资源ID', max_length=50)
    resource_type = models.CharField(u'资源类型', max_length=100)
    created_at = models.DateTimeField(u'操作时间', default=utils.NOW)
    action = models.IntegerField(u'操作类型', choices=ACTION_TYPE)
    user = models.CharField(u"操作者", max_length=128)
    before = models.TextField(u'修改之前')
    after = models.TextField(u'修改之后')

    class Meta:
        app_label = "asset"
