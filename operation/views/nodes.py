#coding:utf8
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import JsonResponse, Http404
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.forms.models import modelformset_factory, inlineformset_factory
from django.views.generic import View

from operation import forms
from operation.models import *


class NodeCreate(View):
    def get(self, req):
        form = forms.NodesForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse('nodes_create')}))

    def post(self, req):
        form = forms.NodesForm(req.POST)
        if form.is_valid():
            node = form.save(commit=False)
            node.create_user = req.user.name
            node.save()
            return JsonResponse({"success": True, "msg": u"节点创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class NodeUpdate(View):
    def get(self, req, node_uuid):
        try:
            instance = QueueNodes.objects.get(pk=node_uuid)
        except:
            raise Http404
        form = forms.NodesForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse('nodes_update', kwargs={"node_uuid":node_uuid})}))

    def post(self, req, node_uuid):
        try:
            instance = QueueNodes.objects.get(pk=node_uuid)
        except:
            raise Http404
        form = forms.NodesForm(req.POST, instance=instance)
        if form.is_valid():
            node = form.save()
            return JsonResponse({"success": True, "msg": u"节点更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})
