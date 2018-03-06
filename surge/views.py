#coding:utf-8
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.conf import settings
from django.views.generic import View

from surge.common import (utils, desktop)
from surge.models import UserAccounts, AuthRoles, ExternalApps
from surge import forms

from operation.models import Apps

def index(request):
    desk = desktop.DeskTop(request)
    REMOTE_ADDR = request.META.get("REMOTE_ADDR", None) or request.META.get("HTTP_X_FORWARDED_FOR", u"未知").split(",")[0]
    return render_to_response("base.html", context_instance= \
            RequestContext(request, {"desktop":desk, "user": request.user, "addr": REMOTE_ADDR}))

def notify_modify_user(req, user):
    uuid = req.session["X-Auth-Token"]
    cache.set(utils.REDIS_USER_TOKEN % uuid, user, timeout=settings.SESSION_MAX_AGE)

def login(request):
    redirect_to = request.REQUEST.get("next", "/")
    message = ""
    if request.method == "POST":
        # 检查客户端浏览器是否开启cookie
        if request.session.set_test_cookie():
            request.session.delete_test_cookie()
        username = request.get_argument(request, "username", None)
        password = request.get_argument(request, "password", None)
        try:
            user = UserAccounts.objects.get_user(username)
            if user.check_password(password):
                if not user.is_active:
                    message = u"用户未激活"
                else:
                    uuid = utils.UUID()
                    request.session["X-Auth-Token"] = uuid
                    notify_modify_user(request, user)
                    response = HttpResponseRedirect(redirect_to)
                    response.set_cookie("X-Auth-Token", uuid, max_age=settings.SESSION_MAX_AGE)
                    return response
            else:
                message = u"用户名或密码错误"
        except UserAccounts.DoesNotExist:
            message = u"用户不存在"
    # 设置测试的cookie
    request.session.set_test_cookie()
    return render_to_response("login.html", context_instance=RequestContext(request, {"message": message}))

def logout(request):
    user = getattr(request, 'user', None)
    if user:
        cache.delete(utils.REDIS_USER_TOKEN % request.session["X-Auth-Token"])
        request.session.flush()
    response = HttpResponseRedirect(reverse("login"))
    response.delete_cookie("X-Auth-Token")
    return response


class OrganizerCreate(View):
    def get(self, req):
        if not req.user.is_admin:
            return JsonResponse({"success": False, "msg": u"您没有创建的权限!"})
        form = forms.AppOrganizerForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse("organizer_create")}))

    def post(self, req):
        if not req.user.is_admin:
            return JsonResponse({"success": False, "msg": u"您没有创建的权限!"})
        form = forms.AppOrganizerForm(req.POST, req.FILES)
        if form.is_valid():
            organizer = form.save()
            return JsonResponse({"success": True, "msg": u"桌面创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})


class UserCreate(View):
    def get(self, req):
        form = forms.UserCreateForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('user_create')}))

    def post(self, req):
        form = forms.UserCreateForm(req.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_user = req.user.account
            user.set_password(user.password)
            user.save()
            return JsonResponse({"success": True, "msg": u"用户创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class UserProfile(View):
    def get(self, req):
        form = forms.UserSettingForm(initial={"email": req.user.email,"wechat": req.user.wechat, "apikey":req.user.apikey})
        form.fields["apikey"].help_text = mark_safe(u'''<a onclick="ResetAPIKey('%s')">生成新的apikey</a>''' % reverse('reset_apikey'))
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('user_profile')}))

    def post(self, req):
        instance = UserAccounts.objects.get_user(req.user.account)
        form = forms.UserSettingForm(req.POST, instance=instance)
        if form.is_valid():
            user = form.save(commit=False)
            user.save(update_fields=['wechat', 'email'])
            return JsonResponse({"success": True, "msg": u"个人信息修改成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class ResetAPIKey(View):
    def get(self, req):
        new_apikey = utils.UUID()
        req.user.apikey = new_apikey
        req.user.save()
        return JsonResponse({"success": True, "msg": new_apikey})

class ChangePassword(View):
    def get(self, req):
        form = forms.ChangePasswordForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('change_password')}))

    def post(self, req):
        instance = UserAccounts.objects.get_user(req.user.account)
        form = forms.ChangePasswordForm(req.POST, instance=instance)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["new_password"])
            user.save(update_fields=['password'])
            cache.delete(utils.REDIS_USER_TOKEN % req.session["X-Auth-Token"])
            req.session.flush()
            response = HttpResponseRedirect(reverse("login"))
            response.delete_cookie("X-Auth-Token")
            return response
        return JsonResponse({"success": True, "msg": form.errors})

class GrantApp(View):
    def get(self, req):
        form = forms.GrantAppForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('grant_app')}))

    def post(self, req):
        form = forms.GrantAppForm(req.POST)
        if form.is_valid():
            for role in form.cleaned_data["roles"]:
                role.users.add(form.cleaned_data["user"])
            return HttpResponseRedirect('/')
        return HttpResponseRedirect(reverse('grant_app'))

class RoleCreate(View):
    def get(self, req, app_uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=app_uuid)
            else:
                app = req.user.roles.get(app__uuid=app_uuid).app
        except:
            raise Http404
        form = forms.RoleCreateForm(initial={"staff":"1","rexec":[1]})
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('role_create', kwargs={"app_uuid": app_uuid})}))

    def post(self, req, app_uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=app_uuid)
            else:
                app = req.user.roles.get(app__uuid=app_uuid).app
        except:
            raise Http404
        form = forms.RoleCreateForm(req.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.created_user = req.user.name
            role.app = app
            role.save()
            form.save_m2m()
            return JsonResponse({"success": True, "msg": u"角色创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class RoleUpdate(View):
    def get(self, req, app_uuid, role_uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=app_uuid)
            else:
                app = req.user.roles.get(app__uuid=app_uuid).app
            role = app.roles.get(uuid=role_uuid)
        except:
            raise Http404
        form = forms.RoleCreateForm(instance=role)
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('role_update', kwargs={"app_uuid": app_uuid, "role_uuid": role_uuid})}))

    def post(self, req, app_uuid, role_uuid):
        try:
            if req.user.is_admin:
                app = Apps.objects.get(uuid=app_uuid)
            else:
                app = req.user.roles.get(app__uuid=app_uuid).app
            role = app.roles.get(uuid=role_uuid)
        except:
            raise Http404
        form = forms.RoleCreateForm(req.POST, instance=role)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "msg": u"角色更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class ThirdAppsLoad(View):
    def get(self, req, app_uuid):
        try:
            app = ExternalApps.objects.get(pk=app_uuid)
        except Exception,e:
            print e
            raise Http404
        if app.public or app.user.uuid == req.user.uuid:
            return render_to_response("common/external_app.html", context_instance=RequestContext(req, \
                    {"url": app.url}))
        raise Http404

class ThirdAppsCreate(View):
    def get(self, req):
        form = forms.ExternalAppForm()
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('3papp_create')}))

    def post(self, req):
        form = forms.ExternalAppForm(req.POST, req.FILES)
        if form.is_valid():
            external_app = form.save(commit=False)
            external_app.user = req.user
            external_app.save()
            return HttpResponseRedirect('/')
        return JsonResponse({"success": False, "msg": form.errors})

class ThirdAppsUpdate(View):
    def get(self, req, app_uuid):
        try:
            instance = ExternalApps.objects.get(pk=app_uuid, user__uuid=req.user.uuid)
        except:
            raise Http404
        form = forms.ExternalAppForm(instance=instance)
        return render_to_response("common/forms.html", context_instance=RequestContext(req, \
                {"form": form, "url": reverse('3papp_update', kwargs={"app_uuid": app_uuid})}))

    def post(self, req, app_uuid):
        try:
            instance = ExternalApps.objects.get(pk=app_uuid, user__uuid=req.user.uuid)
        except:
            raise Http404
        form = forms.ExternalAppForm(req.POST, req.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
        return JsonResponse({"success": False, "msg": form.errors})
