#coding:utf-8
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from django.utils.translation import ugettext_lazy as _

from surge.celery import celery
from surge.common.pagination import PagePagination

from operation.models import (Apps, PlatForms)
from asset.models import Audit

from rest_api import filters
from rest_api.authentication import IsOwnerResource, AdminResource
from rest_api.core.serializer import (AppSerializer, PlatFormSerializer, AuditSerializer)

class AppList(generics.ListAPIView):
    queryset = Apps.objects.all()
    serializer_class = AppSerializer
    pagination_class = PagePagination

class AppsSearch(generics.ListAPIView):
    queryset = Apps.objects.all()
    serializer_class = AppSerializer
    pagination_class = PagePagination

    filter_backends = (filters.SearchFilter,)
    search_fields = ('appid', 'appname', 'appalias')

class AppDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Apps.objects.all()
    serializer_class = AppSerializer
    permission_classes = (IsOwnerResource,)

    lookup_url_kwarg = 'app_uuid'
    lookup_field = 'uuid'

@api_view(['POST'])
@permission_classes((AdminResource,))
def DeleteApps(req):
    try:
        uuids = req.data.get("uuids", None)
        if uuids:
            celery.send_task('DeleteApps', args=[req.user.uuid, uuids])
            return Response({"success":True,"msg":_(u"删除应用提交成功,请等候!")})
        return Response({"success":False,"msg":_(u'缺少参数uuids')})
    except Exception,e:
        print e
        return Response({"success":False,"msg":_(u'删除应用提交失败')})

@api_view(['POST'])
def AppCreate(req):
    try:
        serializer = AppSerializer(data=req.data, files=req.files, 
                context={"request": req})
        if serializer.is_valid():
            app = serializer.save()
            return Response({'success': True, "msg": _(u'应用创建成功!')},
                    status=status.HTTP_201_CREATED)
        return Response({"success": False, "msg": _(u'提交的数据不合法!'),
            'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"success": False, "msg": _(u'应用创建失败!')})

class PlatFormList(generics.ListAPIView):
    queryset = PlatForms.objects.all()
    serializer_class = PlatFormSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

class PlatFormSearch(generics.ListAPIView):
    queryset = PlatForms.objects.all()
    serializer_class = PlatFormSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

    filter_backends = (filters.SearchFilter,)
    search_fields = ('platid', 'platname', 'platalias',)

class PlatFormDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Apps.objects.all()
    serializer_class = PlatFormSerializer
    permission_classes = (IsOwnerResource,)

    lookup_url_kwarg = 'plat_uuid'
    lookup_field = 'uuid'

@api_view(['POST'])
def PlatFormCreate(req):
    try:
        serializer = PlatFormSerializer(data=req.data, context={"request": req})
        if serializer.is_valid():
            platform = serializer.save()
            return Response({'success': True, "msg": _(u'平台创建成功!')},
                    status=status.HTTP_201_CREATED)
        return Response({"success": False, "msg": _(u'提交的数据不合法!'),
            'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"success": False, "msg": _(u'平台创建失败!')})

@api_view(['POST'])
@permission_classes((AdminResource,))
def DeletePlatForm(req):
    try:
        uuids = req.data.get("uuids", None)
        if uuids:
            celery.send_task('DeletePlatForms', args=[req.user.uuid, uuids])
            return Response({"success":True,"msg":_(u"删除应用提交成功,请等候!")})
        return Response({"success":False,"msg":_(u'缺少参数uuids')})
    except Exception,e:
        print e
        return Response({"success":False,"msg":_(u'删除应用提交失败')})

class AuditList(generics.ListAPIView):
    serializer_class = AuditSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        resource_id = self.kwargs["resource_id"]
        return Audit.objects.filter(resource_id=resource_id).all()
