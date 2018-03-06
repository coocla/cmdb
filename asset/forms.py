#coding:utf-8
from django import forms
from django.utils.translation import ugettext_lazy as _

from asset import dnspod
from asset.models import (Assets, IdcRegions, IdcCabinets, \
        Contracts, Divisions, CDNCompany, AccelerateCDN, RegisterDomain)
from operation.models import (Apps, PlatForms)


class InputForm(forms.Form):
    idc_uuid = forms.ModelChoiceField(required=True, label=u"所属机房", \
            widget=forms.Select(attrs={"class": "form-control"}), queryset=IdcRegions.objects.order_by('idc_region').all())
    excel = forms.FileField(required= True, label=u"Excel文件")

class AssetCreateForm(forms.ModelForm):
    app = forms.ModelChoiceField(required=True, label=u"所属应用", \
            widget=forms.Select(attrs={"class": "form-control"}), queryset=Apps.objects.order_by('appname').all())
    platform = forms.ModelChoiceField(required=True, label=u"所属平台", \
            widget=forms.Select(attrs={"class": "form-control"}), queryset=PlatForms.objects.order_by('platname').all())

    class Meta:
        model = Assets
        exclude = ('uuid', 'hostid', 'uniq_id', 'agent_status', 'remote_ip', 'deleted', 'ipv4')
        widgets = {
            "control": forms.Select(attrs={"class": "form-control"}),
            "public_ip": forms.TextInput(attrs={"class": "form-control"}),
            "private_ip": forms.TextInput(attrs={"class": "form-control"}),
            "virtual_ip": forms.TextInput(attrs={"class": "form-control"}),
            "drac_ip": forms.TextInput(attrs={"class": "form-control"}),
            "disk_number": forms.TextInput(attrs={"class": "form-control", "type":"number"}),
            "disk_capacity": forms.TextInput(attrs={"class": "form-control"}),
            "raid_type": forms.TextInput(attrs={"class": "form-control"}),
            "memory_capacity": forms.TextInput(attrs={"class": "form-control"}),
            "cpu_brand": forms.TextInput(attrs={"class": "form-control"}),
            "cpu_core": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "asset_model": forms.TextInput(attrs={"class": "form-control"}),
            "asset_family": forms.Select(attrs={"class": "form-control"}),
            "os_family": forms.TextInput(attrs={"class": "form-control"}),
            "cost_person": forms.TextInput(attrs={"class": "form-control"}),
            "launch_person": forms.TextInput(attrs={"class": "form-control"}),
            "asset_group": forms.Select(attrs={"class": "form-control"}),
            "expire_date": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "purchase_cost": forms.TextInput(attrs={"class": "form-control"}),
            "contract": forms.Select(attrs={"class": "form-control"}),
            "source": forms.Select(attrs={"class": "form-control"}),
            "division": forms.Select(attrs={"class": "form-control"}),
            "app": forms.Select(attrs={"class": "form-control"}),
            "app_mode": forms.Select(attrs={"class": "form-control"}),
            "app_detail": forms.TextInput(attrs={"class": "form-control"}),
            "idc_location": forms.Select(attrs={"class": "form-control", "onchange": "getCabinet(this.value)"}),
            "idc_cabinet": forms.Select(attrs={"class": "form-control"})
        }
        help_texts = {
            "control": u"修改控制服务器,一定要联动修改客户端配置并重启!",
            "virtual": u"又名:浮动IP,常出现在lvs,keepalive架构中!"
        }

class ListField(forms.Field):
    def clean(self, value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [i.strip() for i in value.split() if i.strip()]


class BulkAssetUpdateForm(forms.ModelForm):
    app = forms.ModelChoiceField(required=False, label=u"所属应用", \
            widget=forms.Select(attrs={"class": "form-control"}), queryset=Apps.objects.order_by('appname').all())
    platform = forms.ModelChoiceField(required=False, label=u"所属平台", \
            widget=forms.Select(attrs={"class": "form-control"}), queryset=PlatForms.objects.order_by('platname').all())

    class Meta:
        model = Assets
        exclude = ('uuid', 'agent_status', 'hostid', 'remote_ip', 'public_ip', 'private_ip', 'virtual_ip', 'drac_ip',
                'uniq_id', 'deleted')
        widgets = {
            "control": forms.Select(attrs={"class": "form-control"}),
            "disk_number": forms.TextInput(attrs={"class": "form-control", "type":"number"}),
            "disk_capacity": forms.TextInput(attrs={"class": "form-control"}),
            "raid_type": forms.TextInput(attrs={"class": "form-control"}),
            "memory_capacity": forms.TextInput(attrs={"class": "form-control"}),
            "cpu_brand": forms.TextInput(attrs={"class": "form-control"}),
            "cpu_core": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "asset_model": forms.TextInput(attrs={"class": "form-control"}),
            "asset_family": forms.Select(attrs={"class": "form-control"}),
            "os_family": forms.TextInput(attrs={"class": "form-control"}),
            "cost_person": forms.TextInput(attrs={"class": "form-control"}),
            "launch_person": forms.TextInput(attrs={"class": "form-control"}),
            "asset_group": forms.Select(attrs={"class": "form-control"}),
            "expire_date": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "purchase_cost": forms.TextInput(attrs={"class": "form-control"}),
            "contract": forms.Select(attrs={"class": "form-control"}),
            "source": forms.Select(attrs={"class": "form-control"}),
            "division": forms.Select(attrs={"class": "form-control"}),
            "app": forms.Select(attrs={"class": "form-control"}),
            "app_mode": forms.Select(attrs={"class": "form-control"}),
            "app_detail": forms.TextInput(attrs={"class": "form-control"}),
            "idc_location": forms.Select(attrs={"class": "form-control", "onchange": "getCabinet(this.value)"}),
            "idc_cabinet": forms.Select(attrs={"class": "form-control"})
        }

class BulkMonitorForm(forms.Form):
    groupid = forms.ChoiceField(required=True, label=u"所属服务器组", \
            widget=forms.Select(attrs={"class": "form-control"}))
    proxyid = forms.ChoiceField(required=True, label=u"监控代理", \
            widget=forms.Select(attrs={"class": "form-control"}))
    templateids = forms.MultipleChoiceField(required=True, label=u"监控模版", \
            widget=forms.Select(attrs={"class": "form-control"}))


class IdcRegionsCreateForm(forms.ModelForm):
    class Meta:
        model = IdcRegions
        exclude = ('uuid', )
        widgets = {
            "idc": forms.TextInput(attrs={"class": "form-control"}),
            "idc_region": forms.TextInput(attrs={"class": "form-control"}),
            "idc_address": forms.TextInput(attrs={"class": "form-control"}),
            "idc_area": forms.TextInput(attrs={"class": "form-control"}),
            "remark": forms.Textarea(attrs={"class": "form-control"}),
            "cost": forms.Textarea(attrs={"class": "form-control"}),
        }

class IdcCabinetsCreateForm(forms.ModelForm):
    class Meta:
        model = IdcCabinets
        exclude = ('uuid',)
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "idc": forms.Select(attrs={"class": "form-control"}),
            "remark": forms.Textarea(attrs={"class": "form-control"}),
        }


class ContractsCreateForm(forms.ModelForm):
    class Meta:
        model = Contracts
        exclude = ('uuid',)
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "number": forms.TextInput(attrs={"class": "form-control"}),
            "expire_date": forms.TextInput(attrs={"class": "form-control"}),
        }

class DivisionsCreateForm(forms.ModelForm):
    class Meta:
        model = Divisions
        exclude = ('uuid',)
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }

#class AssetGroupsCreateForm(forms.ModelForm):
#    class Meta:
#        model = AssetGroups
#        exclude = ('uuid',)

class CDNCompanyForm(forms.ModelForm):
    class Meta:
        model = CDNCompany
        exclude = ('uuid', 'created_at')
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "manage": forms.TextInput(attrs={"class": "form-control"}),
            "remark": forms.Textarea(attrs={"class": "form-control"}),
        }

class AccelerateCDNForm(forms.ModelForm):
    class Meta:
        model = AccelerateCDN
        exclude = ('uuid', 'created_at')
        widgets = {
            "domain": forms.TextInput(attrs={"class": "form-control"}),
            "division": forms.Select(attrs={"class": "form-control"}),
            "app": forms.Select(attrs={"class": "form-control"}),
            "company": forms.Select(attrs={"class": "form-control"}),
            "cname": forms.TextInput(attrs={"class": "form-control"}),
            "source": forms.TextInput(attrs={"class": "form-control"}),
            "remark": forms.Textarea(attrs={"class": "form-control"}),
        }

class DomainForm(forms.ModelForm):
    class Meta:
        model = RegisterDomain
        exclude = ('uuid', 'created_at')
        widgets = {
            "domain": forms.TextInput(attrs={"class": "form-control"}),
            "register_site": forms.TextInput(attrs={"class": "form-control"}),
            "register_company": forms.TextInput(attrs={"class": "form-control"}),
            "register_subject": forms.TextInput(attrs={"class": "form-control"}),
            "register_date": forms.TextInput(attrs={"class": "form-control"}),
            "expire_date": forms.TextInput(attrs={"class": "form-control"}),
            "ipc_name": forms.TextInput(attrs={"class": "form-control"}),
            "ipc_id": forms.TextInput(attrs={"class": "form-control"}),
            "ipc_ip": forms.TextInput(attrs={"class": "form-control"}),
            "ipc_phone": forms.TextInput(attrs={"class": "form-control"}),
            "ipc_email": forms.TextInput(attrs={"class": "form-control"}),
            "resolve_driver": forms.TextInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "resolve_driver": u"域名解析提供商",
        }

class DNSPodForm(forms.Form):
    record = forms.CharField(label=_(u"域名"), widget=forms.TextInput(attrs={"class": "form-control"}), help_text=u"要解析的完整域名,例如: www.baidu.com")
    value = forms.CharField(label=_(u"解析地址"), widget=forms.TextInput(attrs={"class": "form-control"}), help_text=u"如要是CNAME,最后字符应该是一个`.`")
    record_line = forms.ChoiceField(label=_(u"解析线路"), choices=dnspod.LINE, widget=forms.Select(attrs={"class": "form-control"}))
    record_type = forms.ChoiceField(label=_(u"记录类型"), choices=dnspod.TYPE, widget=forms.Select(attrs={"class": "form-control"}))

    def clean(self):
        if self.cleaned_data["record_type"] == 'CNAME':
            if not self.cleaned_data["value"].endswith('.'):
                raise forms.ValidationError(_(u"CNAME格式错误,最后一个字符应该是`.`"))
        if self.cleaned_data["value"] in ['*', '@']:
            raise forms.ValidationError(_(u"危险,不支持泛域名解析!"))
        if self.cleaned_data["record"].count('.') < 2:
            raise forms.ValidationError(_(u"域名格式错误!"))
        self.cleaned_data["sub_domain"] = ".".join(self.cleaned_data["record"].split(".")[:-2])
        self.cleaned_data["domain"] = ".".join(self.cleaned_data["record"].split(".")[-2:])
        return super(DNSPodForm, self).clean()
