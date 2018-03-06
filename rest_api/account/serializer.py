#coding:utf-8
from rest_framework import serializers

from asset.models import UserWidgets
from surge.models import (UserAccounts, AuthRoles)
from rest_api.serializer import HyperLinkField

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccounts
        fields = ('uuid', 'account', 'email', 'created_user', 'created_at', \
                'wechat', 'is_admin', 'is_active')

class RoleSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField()
    rexec = serializers.SerializerMethodField()
    url = HyperLinkField(view_name='role_update', 
                     read_only=True,
                     lookup_mapping={
                         "app_uuid": "app",
                         "role_uuid": "self"})

    class Meta:
        model = AuthRoles
        fields = ('uuid', 'name', 'staff', 'rexec', 'idrange', 'created_user', \
                'created_at', 'app', 'url', 'platforms', 'users')

    def get_staff(self, obj):
        return obj.get_staff_display()

    def get_rexec(self, obj):
        maps = {"1": u"执行", "2": u"读", "4": u"写"}
        display = []
        for i in obj.rexec.split():
            display.append(maps.get(i, ""))
        return "".join(display)

class AddWidgetSerializer(serializers.Serializer):
    widget_id = serializers.IntegerField(min_value=1)
    appid = serializers.CharField()

class UserWidgetSerializer(serializers.ModelSerializer):
    url = HyperLinkField(view_name="api_report",
                         read_only=True,
                         lookup_mapping={
                             "widget_id": "widget",
                         })
    class Meta:
        model = UserWidgets
