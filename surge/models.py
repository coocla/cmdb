#coding:utf-8
from datetime import datetime
from collections import defaultdict

from django.db import models
from django.forms import ModelForm
from django.db.models.base import Model
from django.core.validators import MinValueValidator

from surge.common import utils
from operation.models import (PlatForms, Apps)
from asset.models import Assets

UPLOAD = utils.upload_rule('/icon')

class UserAccountManager(models.Manager):
    def create_user(self, name, account, password, created_user, is_admin=False):
        '''
        创建新的用户
        '''
        user = self.model(name=name, account=account, 
                created_user=created_user,
                is_admin=is_admin)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_user(self, username=None, apikey=None):
        if username:
            return self.get(**{"account": username})
        return self.get(**{"apikey": apikey})

class UserAccounts(models.Model):
    VACANCY = (
        (1, u"运维"),
        (2, u"运营"),
    )

    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"昵称", max_length=50)
    email = models.EmailField(u"邮箱地址", blank=True, unique=False, db_index=True)
    account = models.CharField(u"账号", max_length=50, db_index=True, unique=True)
    password = models.CharField(u"密码", max_length=128)
    is_admin = models.BooleanField(u"是否为管理员", default=False)
    vacancy = models.IntegerField(u"所属职位", choices=VACANCY, default=1)
    created_user = models.CharField(u"创建人", max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)
    apikey = models.CharField(u"API KEY", max_length=100, default=utils.UUID, unique=True, db_index=True)
    wechat = models.CharField(u"微信ID", max_length=255, unique=False, blank=True)
    dataer = models.BooleanField(u"是否为数据专员", default=False, help_text=u"数据专员拥有CMDB的管理权限")
    is_active = models.BooleanField(u"是否启用该账户", default=False)

    objects = UserAccountManager()

    class Meta:
        app_label = "surge"

    def __unicode__(self):
        return self.name

    def set_password(self, password):
        self.password = utils.make_password(password)

    def check_password(self, raw_password):
        return self.password == utils.make_password(raw_password)

    def is_authenticated(self):
        return True

    def is_staff(self):
        return True

    def owner_app(self):
        return [r.app.uuid for r in self.roles.all() if r]

    def owner_division(self):
        return [i["division"] for i in Assets.objects.filter(app__uuid__in=self.owner_app()).values('division').distinct()]

    def owner_idc(self):
        return [i["idc_location"] for i in Assets.objects.filter(app__uuid__in=self.owner_app()).values('idc_location').distinct()]

    def is_app_admin(self, app_uuid):
        if self.is_admin:
            return True
        return self.roles.get(app_id=app_uuid).staff == 1

    def cmd_execute_ready(self, app_uuid):
        if self.is_admin: return True
        try:
            if "1" in self.roles.get(app_id=app_uuid).rexec:
                return True
        except:
            pass
        return False

    def cmd_lookup_ready(self, app_uuid):
        if self.is_admin: return True
        try:
            if "2" in self.roles.get(app_id=app_uuid).rexec:
                return True
        except:
            pass
        return False

    def cmd_written_ready(self, app_uuid):
        if self.is_admin: return True
        try:
            if "4" in self.roles.get(app_id=app_uuid).rexec:
                return True
        except:
            pass
        return False

class ExternalApps(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"应用名", max_length=100, default="app")
    icon = models.ImageField(u"应用Logo", upload_to=utils.upload_rule("icon"))
    user = models.ForeignKey(UserAccounts, verbose_name="创建人", related_name='external_apps')
    url = models.URLField(u"应用链接")
    formid = models.IntegerField(u"桌面ID", default=0)
    public = models.BooleanField(u"是否公有", default=True)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "surge"

    def __unicode__(self):
        return self.name


class AuthRoles(models.Model):
    STAFF_CHOICE = (
        (0, u"应用协作者"),
        (1, u"应用管理员")
    )

    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"角色名", max_length=50)
    staff = models.IntegerField(u"角色权限位", choices=STAFF_CHOICE, default=0)
    rexec = models.CharField(u"脚本权限位", max_length=128)  #是否可以创建命令,执行命令,查看命令,如果是管理员角色忽略此字段
    idrange = models.CharField(u"区服范围", max_length=255, blank=True)  # Example: 1-100,103-160,998
    created_user = models.CharField(u"创建人", max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)
    app = models.ForeignKey(Apps, verbose_name="所属应用", related_name="roles")
    platforms = models.ManyToManyField(PlatForms, verbose_name=u"可管理的平台", related_name="roles")
    users = models.ManyToManyField(UserAccounts, verbose_name=u"关联的用户", help_text=u"每个用户在同一个应用中只能属于一个角色", related_name="roles")

    class Meta:
        app_label = "surge"
        ordering = ['-created_at']

    def __unicode__(self):
        return self.name

class AppOrganizer(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"区域名", max_length=50)
    icon = models.ImageField(u"区域Logo", upload_to=utils.upload_rule("icon"))
    formid = models.PositiveIntegerField(u"区域ID", unique=True, db_index=True, validators=[MinValueValidator(1)])

    def __unicode__(self):
        return self.name

