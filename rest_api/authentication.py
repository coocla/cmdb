#coding:utf-8
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication

from surge.common import utils
from surge.models import UserAccounts

class IsOwnerResource(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_admin:
            return True
        app_uuid = view.kwargs.get("app_uuid", None)

        if app_uuid:
            if app_uuid != "1":
                roles = request.user.roles.filter(app__uuid=app_uuid)
                if not roles:
                    return False
                if roles[0].staff == "1": # 是应用管理员
                    return True

        plat_uuid = view.kwargs.get("plat_uuid", None)
        if plat_uuid:
            if roles and roles[0].app.platforms.filter(uuid=plat_uuid):
                return True
            return False

        group_uuid = view.kwargs.get("group_uuid", None)
        if group_uuid:
            if request.user.groups.filter(app_id=app_uuid, uuid=group_uuid):
                return True
            return False
        return True

class AdminResource(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_admin:
            return True
        return False

class DataResource(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_admin or request.user.dataer:
            return True
        return False

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        msg = _("Failed to authenticate!")
        apikey = request.META.get("HTTP_APIKEY", None)
        if apikey:
            try:
                user = UserAccounts.objects.get_user(apikey=apikey)
                channel = "api"
            except UserAccounts.DoesNotExist:
                raise exceptions.AuthenticationFailed(msg)
            request.user = user
            request.channel = channel
            if not user.is_active:
                return None
            return (user, None)
        else:
            if "X-Auth-Token" in request.session:
                user = cache.get(utils.REDIS_USER_TOKEN % request.session["X-Auth-Token"])
                if user and user.is_active:
                    request.user = user
                    request.channel = "console"
                    return (user, None)
            raise exceptions.AuthenticationFailed(msg)

    def authenticate_header(self, request):
        pass
