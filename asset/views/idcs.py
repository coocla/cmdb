#coding:utf-8
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import JsonResponse, Http404
from django.core.urlresolvers import reverse
from django.views.generic import View

from asset.models import (IdcCabinets, IdcRegions)
from asset.forms import (IdcRegionsCreateForm, IdcCabinetsCreateForm)

class IDCCreate(View):
    def get(self, req):
        form = IdcRegionsCreateForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("idc_create")}))

    def post(self, req):
        form = IdcRegionsCreateForm(req.POST)
        if form.is_valid():
            idc = form.save()
            return JsonResponse({"success": True, "msg": u"IDC创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class IDCUpdate(View):
    def get(self, req, idc_uuid):
        try:
            instance = IdcRegions.objects.get(pk=idc_uuid)
        except:
            raise Http404
        form = IdcRegionsCreateForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("idc_update", kwargs={"idc_uuid":idc_uuid})}))

    def post(self, req, idc_uuid):
        try:
            instance = IdcRegions.objects.get(pk=idc_uuid)
        except:
            raise Http404
        form = IdcRegionsCreateForm(req.POST, instance=instance)
        if form.is_valid():
            idc = form.save()
            return JsonResponse({"success": True, "msg": u"IDC更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class CabinetCreate(View):
    def get(self, req):
        form = IdcCabinetsCreateForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("cabinet_create")}))

    def post(self, req):
        form = IdcCabinetsCreateForm(req.POST)
        if form.is_valid():
            cabinet = form.save()
            return JsonResponse({"success": True, "msg": u"机柜创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class CabinetUpdate(View):
    def get(self, req, cabinet_uuid):
        try:
            instance = IdcCabinets.objects.get(pk=cabinet_uuid)
        except:
            raise Http404
        form = IdcCabinetsCreateForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("cabinet_update", kwargs={"cabinet_uuid":cabinet_uuid})}))

    def post(self, req, cabinet_uuid):
        try:
            instance = IdcCabinets.objects.get(pk=cabinet_uuid)
        except:
            raise Http404
        form = IdcCabinetsCreateForm(req.POST, instance=instance)
        if form.is_valid():
            cabinet = form.save()
            return JsonResponse({"success": True, "msg": u"机柜更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})
