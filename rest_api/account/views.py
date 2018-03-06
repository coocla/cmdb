#coding:utf-8
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from asset.models import (Widgets, UserWidgets)
from surge.celery import celery
from surge.models import (UserAccounts, AuthRoles)
from surge.common.pagination import PagePagination

from rest_api import filters
from rest_api.authentication import AdminResource
from rest_api.account.serializer import (UserSerializer, RoleSerializer, \
        UserWidgetSerializer, AddWidgetSerializer)

class UserList(generics.ListAPIView):
    queryset = UserAccounts.objects.all()
    serializer_class = UserSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)

class UserSearch(generics.ListAPIView):
    queryset = UserAccounts.objects.all()
    serializer_class = UserSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)

    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'email', 'account', 'wechat')

class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserAccounts.objects.all()
    serializer_class = UserSerializer

@api_view(['POST'])
@permission_classes((AdminResource,))
def delete_user(request):
    try:
        uuids = request.data.get('uuids', None)
        if not uuids:
            return Response({"success": False, "msg": _(u'缺少参数uuids')})
        celery.send_task('DeleteUsers', args=[request.user.uuid, request.data["uuids"]])
        return  Response({"success": True, "msg": _(u'删除用户提交成功,请等候!')})
    except Exception,e:
        print e
        return Response({"success": False, "msg": _(u'删除用户提交失败!')})

@api_view(['POST'])
@permission_classes((AdminResource,))
def activate_user(request):
    try:
        pk = request.data.get('uuid', None)
        user = UserAccounts.objects.get(uuid=pk)
        user.is_active = True
        user.save()
    except Exception as e:
        return Response({"success": False, "msg": _(u'用户激活失败!')})
    return Response({"success": True, "msg": _(u'用户激活成功!')},
                     status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AdminResource,))
def deactivate_user(request):
    try:
        pk = request.data.get("uuid", None)
        user = UserAccounts.objects.get(uuid=pk)
        user.is_active = False
        user.save()
    except Exception as e:
        return Response({"success": False, "msg": _(u'用户禁用失败!')})
    return Response({"success": True, "msg": _(u'用户禁用成功!')},
                     status=status.HTTP_200_OK)

@api_view(['POST'])
def WidgetAdd(request):
    data = AddWidgetSerializer(data=request.data)
    if data.is_valid():
        if UserWidgets.objects.filter(widget_id=data.validated_data["widget_id"], \
                user=request.user, appid=data.validated_data["appid"]).all():
            return Response({"success": False, "msg": _(u'该图表已存在!')})
        try:
            widget = Widgets.objects.get(pk=data.validated_data["widget_id"])
        except Exception,e:
            print e
            return Response({"success": False, "msg": _(u'图表不存在!')})
        if data.validated_data["appid"] != "1" and not request.user.is_admin:
            try:
                request.user.roles.get(app_id=appid)
            except:
                return Response({"success": False, "msg": _(u'非法的应用ID!')})
        uw = UserWidgets(widget=widget, user=request.user, appid=data.validated_data["appid"])
        uw.save()
        return Response({"success": True, "msg": _(u'图表添加成功!')})
    return Response({"success": False, "msg": data.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def WidgetRemove(request, widget_id):
    try:
        widget = UserWidgets.objects.filter(user_id=request.user.uuid, pk=widget_id)
        widget.delete()
    except:
        return Response({"success": False, "msg": _(u'图表删除失败!')})
    return Response({"success":  True, "msg": _(u'图表删除成功!')})


class WidgetList(generics.ListAPIView):
    serializer_class = UserWidgetSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        return UserWidgets.objects.filter(user=self.request.user, appid=app_uuid).all()


class RoleList(generics.ListAPIView):
    queryset = AuthRoles.objects.all()
    serializer_class = RoleSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)
