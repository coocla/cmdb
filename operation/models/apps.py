#coding:utf-8
from django.db import models
from django.core.validators import MinValueValidator

from surge.common import utils

class PlatForms(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    platid = models.PositiveIntegerField(u"平台id", unique=True, db_index=True, validators=[MinValueValidator(1)])
    platname = models.CharField(u"平台名", max_length=50)
    platalias = models.CharField(u"平台别名", max_length=50, unique=True, db_index=True)
    officials = models.CharField(u"平台负责人", max_length=128)
    virtdomain = models.CharField(u"业务域名", max_length=128, help_text=u"该平台下业务的域名后缀,如: kugou.ate.cn")
    create_user = models.CharField(u"创建人", max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "operation"
        ordering = ['platname']

    def __unicode__(self):
        return self.platname

class Apps(models.Model):
    AppForms = (
        (1, u"页游"),
        (2, u"手游"),
        (3, u"端游"),
        (4, u"配置管理"),
    )
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    appid = models.PositiveIntegerField(u"应用ID", unique=True, db_index=True, validators=[MinValueValidator(1)])
    appname = models.CharField(u"应用名", max_length=50)
    appalias = models.CharField(u"应用别名", max_length=50, unique=True, db_index=True)
    online = models.BooleanField(u"是否上线", default=True)
    icon = models.ImageField(u"应用Logo", upload_to=utils.upload_rule("icon"))
    create_user = models.CharField(u"创建人", max_length=100)
    external_port = models.CharField(u"端口规则", max_length=100)
    appform = models.ForeignKey('surge.AppOrganizer', verbose_name=u"所属桌面")
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)
    platforms = models.ManyToManyField(PlatForms, verbose_name=u"接入的平台", related_name="apps")

    class Meta:
        app_label = "operation"
        ordering = ['appname']

    def __unicode__(self):
        return self.appalias

class PlatGroups(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"组名", max_length=50)
    app = models.ForeignKey(Apps, verbose_name=u"所属应用", related_name="groups")
    platforms = models.ManyToManyField(PlatForms, verbose_name=u"包含的平台", related_name="groups")
    user = models.ForeignKey('surge.UserAccounts', verbose_name=u"所属用户", related_name="groups")

    class Meta:
        app_label = "operation"
        ordering = ['name']

    def __unicode__(self):
        return self.name
