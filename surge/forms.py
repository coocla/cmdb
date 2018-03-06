#coding:utf-8
from django import forms
from django.utils.translation import ugettext_lazy as _

from surge.models import UserAccounts, AuthRoles, AppOrganizer, ExternalApps
from operation.models import Apps

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(required=True, label=u'密码', max_length=128, widget=forms.PasswordInput(
        attrs={"class": "form-control"}))
    password_confirm = forms.CharField(required=True, label=u'确认密码', max_length=128, widget=forms.PasswordInput(
        attrs={"class": "form-control"}))

    class Meta:
        model = UserAccounts
        fields = ('name', 'account', 'password', 'password_confirm', 'is_admin', 'dataer')
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "account": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        try:
            user = UserAccounts.objects.get_user(self.cleaned_data["account"])
        except UserAccounts.DoesNotExist:
            user = None
        if user:
            raise forms.ValidationError(_(u"该账户已经被注册"))
        if self.cleaned_data["password"] != self.cleaned_data["password_confirm"]:
            raise forms.ValidationError(_(u"两次输入的密码不一样"))
        else:
            cleaned_data = super(UserCreateForm, self).clean()
        return cleaned_data

class UserSettingForm(forms.ModelForm):
    class Meta:
        model = UserAccounts
        fields = ("wechat", "email", "apikey")
        widgets = {
            "wechat": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.TextInput(attrs={"class": "form-control"}),
            "apikey": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
        }

class ChangePasswordForm(forms.ModelForm):
    old_password = forms.CharField(required=True, label=u'旧密码', max_length=128, widget=forms.PasswordInput(
        attrs={"class": "form-control"}))
    new_password = forms.CharField(required=True, label=u'新密码', max_length=128, widget=forms.PasswordInput(
        attrs={"class": "form-control"}))
    password_confirm = forms.CharField(required=True, label=u'确认密码', max_length=128, widget=forms.PasswordInput(
        attrs={"class": "form-control"}))

    class Meta:
        model = UserAccounts
        fields = ("old_password", "new_password", "password_confirm")

    def clean(self):
        try:
            user = UserAccounts.objects.get_user(self.instance.account)
        except UserAccounts.DoesNotExist:
            raise forms.ValidationError(u"非法提交!!!")
        if self.cleaned_data.get("old_password", None) or self.cleaned_data.get("new_password", None) or \
                self.cleaned_data.get("password_confirm", None):
            if user.check_password(self.cleaned_data.get("old_password", None)):
                if self.cleaned_data["new_password"] != self.cleaned_data["password_confirm"]:
                    raise forms.ValidationError(_(u"两次输入的密码不一样"))
            else:
                raise forms.ValidationError(_(u"旧密码不正确!"))
        cleaned_data = super(ChangePasswordForm, self).clean()
        return cleaned_data


class GrantAppForm(forms.Form):
    user = forms.ModelChoiceField(required=True, label=u'选择用户', widget=forms.Select(),
            queryset=UserAccounts.objects.all())
    roles = forms.ModelMultipleChoiceField(required=True, label=u'用户所属角色', \
            widget=forms.SelectMultiple(attrs={"class": "form-control"}), queryset=AuthRoles.objects.all())

class RoleCreateForm(forms.ModelForm):
    EXEC_CHOICE = (
        (1, u"执行命令"),
        (2, u"查看命令"),
        (4, u"创建/删除命令"),
    )
    rexec = forms.MultipleChoiceField(required=True, label=u'脚本权限', \
            widget=forms.CheckboxSelectMultiple(), choices=EXEC_CHOICE)

    class Meta:
        model = AuthRoles
        fields = ('name', 'staff', 'rexec', 'idrange', 'platforms', 'users')
        help_texts = {
            "idrange": _(u"请填写1-998这样的范围,多个范围使用逗号隔开"),
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "idrange": forms.TextInput(attrs={"class": "form-control"}),
            "platforms": forms.SelectMultiple(attrs={"class": "form-control", "style": "width:300px"}),
            "users": forms.SelectMultiple(attrs={"class": "form-control", "style": "width:300px"}),
        }

    def clean_rexec(self):
        return "".join(self.cleaned_data["rexec"])

class AppOrganizerForm(forms.ModelForm):
    class Meta:
        model = AppOrganizer
        fields = ('name', 'icon', 'formid')

    def has_file(self):
        return True

class ExternalAppForm(forms.ModelForm):
    class Meta:
        model = ExternalApps
        exclude = ('uuid', 'user', 'created_at', 'formid', 'appid')
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.TextInput(attrs={"class": "form-control"}),
        }

    def has_file(Self):
        return True
