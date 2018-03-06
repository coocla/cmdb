#coding:utf-8
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.core.cache import cache

from surge.common import utils
from operation.models import Apps, PlatForms, PlatGroups
from operation.forms import (PlatCreateForm, PlatGroupCreateForm, AppPlatCreateForm, RegionForm)

class PlatCreate(View):
    def get(self, req):
        form = PlatCreateForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('plat_create')}))

    def post(self, req):
        form = PlatCreateForm(req.POST)
        if form.is_valid():
            plat = form.save(commit=False)
            plat.created_user = req.user.account
            plat.save()
            return JsonResponse({"success": True, "msg": u"平台创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class PlatUpdate(View):
    def get(self, req, plat_uuid):
        instance = PlatForms.objects.get(pk=plat_uuid)
        form = PlatCreateForm(instance=instance)
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('plat_update', kwargs={"plat_uuid":plat_uuid})}))

    def post(self, req, plat_uuid):
        instance = PlatForms.objects.get(pk=plat_uuid)
        form = PlatCreateForm(req.POST, instance=instance)
        if form.is_valid():
            plat = form.save()
            return JsonResponse({"success": True, "msg": u"平台更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class PlatGroupCreate(View):
    def get(self, req, app_uuid):
        self.get_app(req, app_uuid)
        form = PlatGroupCreateForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('platgroup_create', kwargs={"app_uuid":app_uuid})}))

    def post(self, req, app_uuid):
        form = PlatGroupCreateForm(req.POST)
        app = self.get_app(req, app_uuid)
        if form.is_valid():
            group = form.save(commit=False)
            group.app = app
            group.user = req.user
            group.save()
            form.save_m2m()
            return JsonResponse({"success":True, "msg": u"自定义组创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

    def get_app(self, req, uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=uuid)
            else:
                app = req.user.roles.get(app__uuid=uuid).app
        except Exception,e:
            print e
            raise Http404
        return app

class PlatGroupUpdate(View):
    def get(self, req, group_uuid):
        group = PlatGroups.objects.get(pk=group_uuid)
        form = PlatGroupCreateForm(instance=group)
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('platgroup_update', kwargs={"group_uuid":group_uuid})}))

    def post(self, req, group_uuid):
        group = PlatGroups.objects.get(pk=group_uuid)
        form = PlatGroupCreateForm(req.POST, instance=group)
        if form.is_valid():
            group.save()
            return JsonResponse({"success":True, "msg": u"自定义组更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class AppPlatCreate(View):
    def get(self, req, app_uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=app_uuid)
            else:
                app = req.user.roles.get(app__uuid=app_uuid).app
        except:
            raise Http404
        form = AppPlatCreateForm(initial={"platforms":app.platforms.order_by('platname').all()})
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('appplat_create', kwargs={"app_uuid":app_uuid})}))

    def post(self, req, app_uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=app_uuid)
            else:
                app = req.user.roles.get(app__uuid=app_uuid).app
        except:
            raise Http404
        form = AppPlatCreateForm(req.POST)
        if form.is_valid():
            for i in set(app.platforms.all()) - set(form.cleaned_data["platforms"]):
                if i.hosts.first():
                    return JsonResponse({"success":False, "msg":u"请先处理下线平台中的服务器!"})
            app.platforms.clear()
            for plat in form.cleaned_data["platforms"]:
                app.platforms.add(plat)
            return JsonResponse({"success":True, "msg": u"平台接入成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class RegionCreate(View):
    def get(self, req, app_uuid):
        form = RegionForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('region_create', kwargs={"app_uuid":app_uuid})}))

    def post(self, req, app_uuid):
        form = RegionForm(req.POST)
        if form.is_valid():
            key = utils.REDIS_REGION % (req.user.uuid, app_uuid, utils.UUID())
            cache.set(key, json.dumps(form.cleaned_data))
            cache.persist(key)
            return JsonResponse({"success":True, "msg": u"区域创建成功成功!"})
        return JsonResponse({"success":False, "msg": form.errors})
