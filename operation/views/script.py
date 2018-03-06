#coding:utf8
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.forms.models import modelformset_factory, inlineformset_factory
from django.views.generic import View

from operation import forms
from operation.models import *

class WorkFlowCreate(View):
    def get(self, req, app_uuid):
        flowtitle = forms.WorkFlowForm()
        stepset = modelformset_factory(ScriptFlow, exclude=('uuid', 'workflow'))
        flowstep = stepset(queryset=ScriptFlow.objects.none())
        return render_to_response('common/formset.html', context_instance=RequestContext(req, \
                {"forms": flowstep, "form": flowtitle, "url": reverse("workflow_create", kwargs={"app_uuid": app_uuid})}))

    def post(self, req, app_uuid):
        flowtitle = forms.WorkFlowForm(req.POST)
        stepset = modelformset_factory(ScriptFlow, exclude=('uuid', 'workflow'))
        flowstep = stepset(req.POST)
        if flowtitle.is_valid() and flowstep.is_valid():
            safe_check(req, flowtitle, flowstep, view_name="workflow_create", app_uuid=app_uuid)
            workflow = flowtitle.save(commit=False)
            workflow.create_user = req.user.name
            workflow.userid = req.user.uuid
            workflow.app = Apps.objects.get(pk=app_uuid)
            workflow.save()

            scriptflow = flowstep.save(commit=False)
            for i in scriptflow:
                i.workflow_id = workflow.uuid
                i.save()
            return JsonResponse({"success": True, "msg": u"作业创建成功!"})
        return JsonResponse({"success": False, "msg": forms.errors})

def safe_check(req, flowtitle, flowstep, view_name='workflow_create', **kwargs):
    if flowtitle.is_valid() and flowtitle.cleaned_data["mode"] == "2":
        for form in flowstep:
            if form.is_valid() and Scripts.objects.get(uuid=form.cleaned_data["script"]).mode == 1:
                return render_to_response('common/formset.html', context_instance=RequestContext(req, \
                        {"forms": flowstep, "form": flowtitle, "url": reverse(view_name, kwargs=kwargs)}))


class WorkFlowUpdate(View):
    def get(self, req, app_uuid, workflow_uuid):
        workflow = WorkFlows.objects.get(pk=workflow_uuid)
        flowtitle = forms.WorkFlowForm(instance=workflow)

        stepset = modelformset_factory(ScriptFlow, exclude=('uuid', 'workflow'), max_num=1)
        flowstep = stepset(queryset=workflow.flow.all())
        return render_to_response('common/formset.html', context_instance=RequestContext(req, \
                {"forms": flowstep, "form": flowtitle, "url": reverse("workflow_update", \
                kwargs={"app_uuid": app_uuid, "workflow_uuid":workflow_uuid})}))


    def post(self, req, app_uuid, workflow_uuid):
        workflow = WorkFlows.objects.get(pk=workflow_uuid)
        flowtitle = forms.WorkFlowForm(req.POST, instance=workflow)

        stepset = modelformset_factory(ScriptFlow, exclude=('uuid', 'workflow'))
        flowstep = stepset(req.POST)

        if flowtitle.is_valid() and flowstep.is_valid():
            safe_check(req, flowtitle, flowstep, view_name="workflow_update", app_uuid=app_uuid, workflow_uuid=workflow_uuid)

            workflow_new = flowtitle.save(commit=False)
            workflow_new.save()

            scriptflow = flowstep.save(commit=False)
            for i in scriptflow:
                i.workflow = workflow_new
                i.save()
            return JsonResponse({"success": True, "msg": u"作业更新成功!"})
        return JsonResponse({"success": True, "msg": flowstep.error})
        #return render_to_response('common/formset.html', context_instance=RequestContext(req, \
        #        {"forms": flowstep, "form": flowtitle, "url": reverse("workflow_update", \
        #        kwargs={"app_uuid": app_uuid, "workflow_uuid":workflow_uuid})}))

class ScriptCreate(View):
    def get(self, req, app_uuid):
        form = forms.ScriptForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("script_create", kwargs={"app_uuid": app_uuid})}))
        
    def post(self, req, app_uuid):
        try:
            app = Apps.objects.get(uuid=app_uuid)
            form = forms.ScriptForm(req.POST)
            if form.is_valid():
                script = form.save(commit=False)
                script.userid = req.user.uuid
                script.create_user = req.user.name
                script.app = app
                script.save()
                return JsonResponse({"success": True, "msg": u"脚本创建成功!"})
            return JsonResponse({"success": False, "msg": form.errors})
        except:
            return JsonResponse({"success": True, "msg": u"不太对劲儿,内部错误!"})

class ScriptUpdate(View):
    def get(self, req, app_uuid, script_uuid):
        instance = Scripts.objects.get(pk=script_uuid)
        form = forms.ScriptForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("script_update", kwargs={"app_uuid": app_uuid, "script_uuid":script_uuid})}))

    def post(self, req, app_uuid, script_uuid):
        try:
            instance = Scripts.objects.get(pk=script_uuid, app__uuid=app_uuid)
            form = forms.ScriptForm(req.POST, instance=instance)
            if form.is_valid():
                script = form.save()
                return JsonResponse({"success": True, "msg": u"脚本更新成功!"})
            return JsonResponse({"success": False, "msg": form.errors})
        except:
            return JsonResponse({"success": True, "msg": u"不太对劲儿,内部错误!"})
