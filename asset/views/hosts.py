#coding:utf-8
import xlrd
from django import forms as djforms
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.conf import settings
from excel_response3 import ExcelResponse

from asset import forms
from asset.pyzabbix import Zabbix
from asset.models import (Assets, Divisions, Contracts)
from asset.agentData import GetHostConfig

from surge.common import utils

class HostCreate(View):
    def get(self, req):
        form = forms.AssetCreateForm(initial={"idc_cabinet":[]})
        return render_to_response('cmdb/hosts.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("host_create")}))

    def post(self, req):
        form = forms.AssetCreateForm(req.POST)
        if form.is_valid():
            host = form.save(commit=False)
            host.remote_ip = form.cleaned_data["public_ip"].split(",")[0]
            host.uniq_id = utils.uniq_id(form.cleaned_data["public_ip"], form.cleaned_data.get("private_ip", ""))
            host.save()
            return JsonResponse({"success": True, "msg": u"服务器创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class HostInput(View):
    def get(self, req, idc_uuid):
        '''
        单台录入
        '''
        data = "export master_url=%s; export idc_uuid=%s; export key=%s; wget --tries=2 --waitretry=1 --timeout=10 -O /tmp/importVMsInBatches.sh \
%s/static/repo/importVMsInBatches.sh;bash /tmp/importVMsInBatches.sh" % (settings.DOMAIN, idc_uuid, req.user.apikey, settings.DOMAIN)
        return HttpResponse(data)

class HostInputDownload(View):
    def get(self, req):
        data = [
            ['remote_ip(外网IP)', 'ssh_password(root密码)', 'ssh_port'],
            ['42.51.161.109', 'root_password', '22'],
            ['42.51.161.110', 'root_password', '22'],
            ['42.51.161.111', 'root_password', '22'],
            ['42.51.161.112', 'root_password', '22'],
        ]
        return ExcelResponse(data, 'surge_example')


class HostBulkInput(View):
    def get(self, req):
        '''
        excel导入
        '''
        form = forms.InputForm()
        form.fields["excel"].help_text = mark_safe(u'<a href="%s" target="_blank">示例下载</a>' % reverse('host_input_download'))
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("host_bulk_input")}))

    def post(self, req):
        form = forms.InputForm(req.POST)
        if "excel" in req.FILES and req.FILES['excel']:
            input_excel = req.FILES['excel']
            book = xlrd.open_workbook(file_contents=input_excel.read())
            data = []
            idc_uuid = req.POST.get("idc_uuid", None)
            if not idc_uuid:
                return JsonResponse({"success":False,"msg":u"请选择要导入服务器所在的机房!"})
            try:
                table = book.sheet_by_index(0)
                for i in range(1, table.nrows):
                    tr = table.row_values(i)
                    data.append((tr[0], {"ansible_ssh_user":"root", "ansible_ssh_port":int(tr[2]), "ansible_ssh_pass":tr[1], "idc_uuid":idc_uuid}))
            except:
                return JsonResponse({"success":False,"msg":u"Excel格式不正确"})
            celery.send_task('BulkInputHost', args=[req.user.uuid, data])
            return JsonResponse({"success":True,"msg":u"批量导入提交成功,请等候!"})
        return JsonResponse({"success":False,"msg":u"请上传Excel文件"})

        

class HostUpdate(View):
    def get(self, req, host_uuid=None):
        try:
            host = Assets.objects.get(uuid=host_uuid)
        except:
            host = None
        form = forms.AssetCreateForm(instance=host)
        return render_to_response('cmdb/hosts.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("host_update", kwargs={"host_uuid": host_uuid})}))

    def post(self, req, host_uuid=None):
        try:
            host = Assets.objects.get(uuid=host_uuid)
            form = forms.AssetCreateForm(req.POST, instance=host)
            if form.is_valid():
                host = form.save(commit=False)
                host.remote_ip = form.cleaned_data["public_ip"].split(",")[0]
                host.uniq_id = utils.uniq_id(form.cleaned_data["public_ip"], form.cleaned_data.get("private_ip", ""))
                host.save()
                return JsonResponse({"success": True, "msg": u"服务器更新成功!"})
            return JsonResponse({"success": False, "msg": form.errors})
        except Exception as e:
            return JsonResponse({"success": False, "msg": u"内部错误!"})

class HostBulkUpdate(View):
    def get(self, req):
        form = forms.BulkAssetUpdateForm(initial={"idc_cabinet":[]})
        return render_to_response('cmdb/hosts.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("api_hosts_bulk_update")}))


class HostBulkMonitor(View):
    def get(self, req):
        zabbix = Zabbix()
        form = forms.BulkMonitorForm(initial={"groupid": zabbix.group_list(), 
                                              "templateids": zabbix.template_list(),
                                              "proxyid": zabbix.proxy_list()})
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("host_bulk_update")}))

class HostAgentData(View):
    def get(self, req, host_uuid):
        try:
            host = Assets.objects.get(pk=host_uuid)
        except Exception,e:
            return HttpResponse("")
        data = GetHostConfig(host).config
        return HttpResponse(data)

class ContractCreate(View):
    def get(self, req):
        form = forms.ContractsCreateForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("contract_create")}))

    def post(self, req):
        form = forms.ContractsCreateForm(req.POST)
        if form.is_valid():
            c = form.save()
            return JsonResponse({"success": True, "msg": u"合同创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class ContractUpdate(View):
    def get(self, req, contract_uuid):
        try:
            instance = Contracts.objects.get(pk=contract_uuid)
        except:
            raise Http404
        form = forms.ContractsCreateForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("contract_update", kwargs={"contract_uuid":contract_uuid})}))

    def post(self, req):
        try:
            instance = Contracts.objects.get(pk=contract_uuid)
        except:
            raise Http404
        form = forms.ContractsCreateForm(req.POST, instance=instance)
        if form.is_valid():
            c = form.save()
            return JsonResponse({"success": True, "msg": u"合同更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class DivisionCreate(View):
    def get(self, req):
        form = forms.DivisionsCreateForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("division_create")}))

    def post(self, req):
        form =  forms.DivisionsCreateForm(req.POST)
        if form.is_valid():
            c = form.save()
            return JsonResponse({"success": True, "msg": u"事业部创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class DivisionUpdate(View):
    def get(self, req, division_uuid):
        try:
            instance = Divisions.objects.get(pk=division_uuid)
        except:
            raise Http404
        form = forms.DivisionsCreateForm(instance=instance)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("division_update", kwargs={"division_uuid": division_uuid})}))

    def post(self, req, division_uuid):
        try:
            instance = Divisions.objects.get(pk=division_uuid)
        except:
            raise Http404
        form = forms.DivisionsCreateForm(instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "msg": u"事业部更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})


#class HostGroupCreate(View): 
#    def get(self, req):
#        form = forms.AssetGroupsCreateForm()
#        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
#                {"form": form, "url": reverse("hostgroup_create")}))
#
#    def post(self, req):
#        form = forms.AssetGroupsCreateForm(req.POST)
#        if form.is_valid():
#            c = form.save()
#            return JsonResponse({"success": True, "msg": u"主机组创建成功!"})
#        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
#                {"form": form, "url": reverse("hostgroup_create")}))
#
#class HostGroupUpdate(View): 
#    def get(self, req, group_uuid):
#        try:
#            instance = AssetGroups.objects.get(pk=group_uuid)
#        except:
#            raise Http404
#        form = forms.AssetGroupsCreateForm(instance=instance)
#        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
#                {"form": form, "url": reverse("hostgroup_update", kwargs={"group_uuid":group_uuid})}))
#
#    def post(self, req, group_uuid):
#        try:
#            instance = AssetGroups.objects.get(pk=group_uuid)
#        except:
#            raise Http404
#        form = forms.AssetGroupsCreateForm(req.POST, instance=instance)
#        if form.is_valid():
#            c = form.save()
#            return JsonResponse({"success": True, "msg": u"主机组更新成功!"})
#        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
#                {"form": form, "url": reverse("hostgroup_update", kwargs={"group_uuid":group_uuid})}))
