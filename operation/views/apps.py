#coding:utf-8
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.db import models

from asset import reports
from surge.common import utils

from operation.forms import AppCreateForm
from operation.models.apps import Apps

class AppCreate(View):
    def get(self, req):
        max_appid = Apps.objects.all().aggregate(models.Max('appid'))
        form = AppCreateForm(initial={"appid":  (max_appid["appid__max"] or 0) +1,
            "appform": 1})
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("app_create")}))

    def post(self, req):
        form = AppCreateForm(req.POST, req.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.create_user = req.user.account
            app.save()
            form.save_m2m()
            return JsonResponse({"success": True, "msg": u"应用创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class AppUpdate(View):
    def get(self, req, app_uuid):
        try:
            instance = Apps.objects.get(uuid=app_uuid)
        except:
            instance = None
        form = AppCreateForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("app_update", kwargs={"app_uuid":app_uuid})}))

    def post(self, req, app_uuid):
        try:
            instance = Apps.objects.get(uuid=app_uuid)
            form = AppCreateForm(req.POST, req.FILES, instance=instance)
            if form.is_valid():
                app = form.save(commit=False)
                app.save()
                form.save_m2m()
            else:
                return JsonResponse({"success": False, "msg": form.errors})
        except Exception as e:
            return JsonResponse({"success": False, "msg": u"应用更新失败!"})
        return JsonResponse({"success": True, "msg": u"应用更新成功!"})

def AppLoad(req, app_uuid):
    Nav = [
            {"name": u"概览", "en": "dashboard", "url": reverse("api_user_widgets", kwargs={"app_uuid": app_uuid})},
            {"name": u"服务器", "en": "host", "url": reverse("api_ops_tree", kwargs={"app_uuid":app_uuid, "tab": "hosts"})}, 
            {"name": u"区服", "en": "srv", "url": reverse("api_ops_tree", kwargs={"app_uuid":app_uuid, "tab": "zones"})}, \
            {"name": u"脚本", "en": "script", "url": reverse("api_scripts", kwargs={"app_uuid":app_uuid})}, \
            {"name": u"作业", "en": "workflow", "url": reverse("api_workflows", kwargs={"app_uuid":app_uuid})}, \
            {"name": u"定时作业", "en": "cronjob", "url": reverse("api_cronjob", kwargs={"app_uuid":app_uuid})}, \
            {"name": u"日志", "en": "log", "url": reverse("api_tasks", kwargs={"app_uuid":app_uuid})}
        ]

    if req.user.is_admin:
        Nav.append({"name": u"接入平台", "en": "plat", "url": reverse("api_app_platforms", kwargs={"app_uuid":app_uuid})})
        Nav.append({"name": u"应用角色", "en": "role", "url": reverse("api_app_roles", kwargs={"app_uuid":app_uuid})})
    else:
        try:
            role = req.user.roles.get(app__uuid=app_uuid)
            if str(role.staff) == "1":
                Nav.append({"name": u"平台", "en": "plat", "url": reverse("api_app_platforms", kwargs={"app_uuid":app_uuid})})
                Nav.append({"name": u"角色", "en": "role", "url": reverse("api_app_roles", kwargs={"app_uuid":app_uuid})})
        except:
            pass

    return render_to_response('ops/app_desktop.html', context_instance=RequestContext(req, {"Navs": Nav}))
