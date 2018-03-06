#coding:utf-8
'''
用来生成用户桌面应用
'''
import json

from django.core.urlresolvers import reverse
from django.conf import settings

from surge.models import AppOrganizer, ExternalApps
from operation.models import Apps

class DeskTop(object):
    def __init__(self, request):
        self.request = request

    @property
    def menu(self):
        """
        开始菜单
        """
        if self.request.user.is_admin:
            menu = {"profile": {"name":u"修改个人信息", "url":reverse("user_profile"), "zooms": False, "ismax":False, "ct": "html"},
                    "change-password": {"name":u"修改密码", "url":reverse("change_password"), "zooms":False,"ismax":False,"ct":"html"},
                    "users": {"name": u"用户管理", "url":reverse("api_users"), "zooms": False, "ismax":False, "ct": "json"},
                    "platforms": {"name": u"平台管理", "url":reverse("api_platform"), "zooms": False, "ismax":False, "ct": "json"},
                    "apps": {"name": u"应用管理", "url":reverse("api_apps"), "zooms": False, "ismax":False, "ct": "json"},
                    "nodes": {"name": u"节点管理", "url":reverse("api_nodes"), "zooms": False, "ismax": False, "ct": "json"},
                    }
        else:
            is_project_admin = filter(lambda x: x.staff,self.request.user.roles.all())
            menu = {"profile": {"name":u"修改个人配置", "url":reverse("user_profile"), "zooms": False, "ismax":False, "ct": "html"},
                    "change-password": {"name":u"修改密码", "url":reverse("change_password"), "zooms":False,"ismax":False,"ct":"html"},
                    }
        return menu

    @property
    def dock(self):
        dock = []
        if self.request.user.is_admin:
            organizers = AppOrganizer.objects.all()
        else:
            organizers = set()
            for role in self.request.user.roles.all():
                organizers.add(role.app.appform)

        for desk in organizers:
            dock.append({"pageid": desk.formid, "name": desk.name, "icon": desk.icon.url})
        dock.insert(0, {"pageid": 0, "name": u"开始", "icon": "upload/icon/start.png"})
        return json.dumps(dock)

    @property
    def menutoJSON(self):
        return json.dumps(self.menu)

    def _app(self):
        quikeapp = {}
        if self.request.user.is_admin:
            apps = Apps.objects.filter(online=True).all()
        else:
            apps = set()
            for role in self.request.user.roles.all():
                if role.app.online:
                    apps.add(role.app)
        data = []
        index = 1
        for app in apps:
            data.append({"name":app.appalias, "icon":app.icon.url, "url": reverse("app_load", args=[app.uuid]), \
                    "appid": app.uuid, "formid": app.appform.formid})

        for external in ExternalApps.objects.filter(public=True).exclude(user__uuid=self.request.user.uuid).all():
            data.append({"name":external.name, "icon":external.icon.url, "url": reverse("3papp_load", args=[external.uuid]), "appid":external.uuid, "formid":external.formid})

        for self_app in self.request.user.external_apps.all():
            data.append({"name":self_app.name, "icon":self_app.icon.url, "url": reverse("3papp_load", args=[self_app.uuid]), "appid":self_app.uuid, "formid":self_app.formid})

        data.append({"name":u"资产管理", "icon":"upload/icon/cmdb.png", "url": reverse("api_cmdb_menu"), "appid": "1","formid": 0})
        return json.dumps(data), json.dumps(quikeapp)

    @property
    def app(self):
        # 桌面应用声明
        return self._app()[0]

    @property
    def ops(self):
        # 向桌面注册应用
        return self._app()[1]
