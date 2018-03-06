#coding:utf-8
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from django import forms

from operation.models import (Apps, PlatForms, ScriptFlow, Scripts,
        WorkFlows, Zones, PlatGroups, QueueNodes)

class AppCreateForm(forms.ModelForm):
    class Meta:
        model = Apps
        fields = ("appid","appname","appalias","icon","online","external_port","appform","platforms")
        widgets = {
            "appid": forms.NumberInput(attrs={"class": "form-control"}),
            "appname": forms.TextInput(attrs={"class": "form-control"}),
            "appalias": forms.TextInput(attrs={"class": "form-control"}),
            "icon": forms.FileInput(attrs={"class": "form-control"}),
            "appform": forms.Select(attrs={"class": "form-control"}),
            "external_port": forms.TextInput(attrs={"class": "form-control"}),
            "platforms": forms.SelectMultiple(attrs={"class": "form-control", "style": "height:300px"}),
        }
        help_texts = {
            "appname": _(u"应用的英文名,拼音会么?"),
            "appalias": _(u"应用的中文名"),
            "external_port": _(u"端口规则,用来监控的. 可用变量  %(sid)s  ,例如: 8000+%(sid)s"),
        }

    def has_file(self):
        return True

class PlatCreateForm(forms.ModelForm):
    class Meta:
        model = PlatForms
        fields = ("platid","platname", "platalias","officials","virtdomain")
        widgets = {
            "platid": forms.NumberInput(attrs={"class": "form-control"}),
            "platname": forms.TextInput(attrs={"class": "form-control"}),
            "platalias": forms.TextInput(attrs={"class": "form-control"}),
            "officials": forms.TextInput(attrs={"class": "form-control"}),
            "virtdomain": forms.TextInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "platname": _(u"平台的英文名"),
            "platalias": _(u"平台的中文名"),
            "virtdomain": _(u"平台业务的域名,如:admin.3xwan.ate.cn"),
        }

class PlatGroupCreateForm(forms.ModelForm):
    platforms = forms.ModelMultipleChoiceField(required=True, label=u'包含的平台', \
            widget=forms.SelectMultiple(attrs={"class": "form-control", "style":"height:260px"}), queryset=PlatForms.objects.order_by('platname'))

    class Meta:
        model = PlatGroups
        exclude = ('uuid', 'app', 'user')

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "platforms": forms.SelectMultiple(attrs={"class": "form-control", "style": "height:300px"}),
        }

class AppPlatCreateForm(forms.ModelForm):
    platforms = forms.ModelMultipleChoiceField(required=True, label=u'接入平台', \
            widget=forms.SelectMultiple(attrs={"class": "form-control", "style":"height:260px"}), queryset=PlatForms.objects.order_by('platname'))

    class Meta:
        model = Apps
        fields = ('platforms',)

class ZoneCreateForm(forms.ModelForm):
    class Meta:
        model = Zones
        fields = ('sid', 'host')

    def __init__(self, *args, **kwargs):
        self.app_uuid = kwargs.pop("app_uuid", None)
        self.plat_uuid = kwargs.pop("plat_uuid", None)
        super(ZoneCreateForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.cleaned_data["sid"] < 0:
            raise forms.ValidationError(_(u"非法的区服ID"))
        if Zones.objects.filter(app_uuid=self.app_uuid, plat_uuid=self.plat_uuid, sid=self.cleaned_data["sid"]):
            raise forms.ValidationError(_(u"区服已存在"))
        return super(ZoneCreateForm, self).clean()


class ScriptForm(forms.ModelForm):
    class Meta:
        model = Scripts
        fields = ('name', 'mode', 'storage', 'param', 'content')

        widgets = {
            'name': forms.TextInput(attrs={"class": "form-control"}),
            'mode': forms.Select(attrs={"class": "form-control"}),
            'storage': forms.Select(attrs={"class": "form-control"}),
            'param': forms.TextInput(attrs={"class": "form-control"}),
            'content': forms.Textarea(attrs={"class": "form-control"}),
        }

class ScriptFlowForm(forms.ModelForm):
    class Meta:
        model = ScriptFlow
        exclude = ('workflow',)
        widgets = {
            "script": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "uuid": forms.HiddenInput(attrs={'readonly':'readonly'}),
        }
        validators = {
            "stepid": [MinValueValidator(1)],
        }

class WorkFlowForm(forms.ModelForm):
    class Meta:
        model = WorkFlows
        fields = ('name', 'mode')

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "mode": forms.Select(attrs={"class": "form-control"})
        }
        help_texts = {
            "mode": _(u"公有作业中不能包含私有脚本"),
        }

class NodesForm(forms.ModelForm):
    class Meta:
        model = QueueNodes
        exclude = ('uuid', 'create_user', )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "rabbitmq_host": forms.TextInput(attrs={"class": "form-control"}),
            "queue_username": forms.TextInput(attrs={"class": "form-control"}),
            "queue_password": forms.TextInput(attrs={"class": "form-control", "type":"password"}),
            "rabbitmq_port": forms.TextInput(attrs={"class": "form-control"}),
            "rabbitmq_vhost": forms.TextInput(attrs={"class": "form-control"}),
            "rabbitmq_down_exchange": forms.TextInput(attrs={"class": "form-control"}),
            "rabbitmq_up_exchange": forms.TextInput(attrs={"class": "form-control"}),
            "uniq_id": forms.TextInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "uniq_id": _(u"节点对应的服务器的唯一ID, 请填写对应服务器的`uniq_id`字段"),
        }

class RegionForm(forms.Form):
    name = forms.CharField(label=_(u"区域名"), widget=forms.TextInput(attrs={"class": "form-control"}), help_text=u"区域名字,用以标识分辨!")
    min_value = forms.CharField(label=_(u"区域临界最小值"), widget=forms.TextInput(attrs={"class": "form-control"}), help_text=u"sid 大于等于该值的区服将会被划分到该区域!")
    max_value = forms.CharField(label=_(u"区域临界最大值"), widget=forms.TextInput(attrs={"class": "form-control"}), help_text=u"sid 小于等于该值的区服将会被划分到该区域!")

    def clean_min_value(self):
        try:
            value = int(self.cleaned_data["min_value"])
        except:
            raise forms.ValidationError(_(u"区域临界最小值应该是个整数"))
        return value

    def clean_max_value(self):
        try:
            value = int(self.cleaned_data["max_value"])
        except:
            raise forms.ValidationError(_(u"区域临界最大值应该是个整数"))
        return value

    def clean(self):
        if self.cleaned_data["min_value"] > self.cleaned_data["max_value"]:
            raise forms.ValidationError(_(u"最小值大于最大值?是不是缺心眼!!!"))
