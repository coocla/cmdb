#coding:utf-8
import json
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.db import models

from operation import forms
from operation.models import Zones, Apps


class ZoneCreate(View):
    def get(self, req, app_uuid, plat_uuid):
        self._safecheck(req, app_uuid, plat_uuid)
        form = forms.ZoneCreateForm(initial={"sid": (Zones.objects.max_sid(app_uuid, plat_uuid) or 0)+1})
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("zone_create", kwargs={"app_uuid":app_uuid,"plat_uuid":plat_uuid})}))

    def post(self, req, app_uuid, plat_uuid):
        self._safecheck(req, app_uuid, plat_uuid)
        form = forms.ZoneCreateForm(req.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.alias = zone.sid
            zone.app_uuid = app_uuid
            zone.plat_uuid = plat_uuid
            zone.save()
            form.save_m2m()
            return HttpResponse(json.dumps({"success":True, "msg": unicode(_(u"区服创建成功!"))}))
        return JsonResponse({"success": True, "msg": form.errors})

    def _safecheck(self, req, app_uuid, plat_uuid):
        if not req.user.is_admin:
            try:
                app = req.user.roles.get(app__uuid=app_uuid)
            except:
                raise Http404
        else:
            try:
                app = Apps.objects.get(uuid=app_uuid)
            except:
                raise Http404
        try:
            app.platforms.filter(uuid=plat_uuid)
        except:
            raise Http404
