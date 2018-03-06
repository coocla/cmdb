#coding:utf-8
import json
import logging
import django_filters
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db import transaction
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404

from djcelery.models import PeriodicTask, CrontabSchedule

from rest_framework import generics
from rest_framework import status
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from asset.models import Assets
from surge.celery import celery
from surge.models import AuthRoles
from surge.common import utils
from surge.common.pagination import PagePagination, ZonePagination
from operation.models import (Apps, Scripts, WorkFlows, Zones, PlatGroups, \
        Tasks, TaskSteps, TaskResults, PeriodicTaskMeta, QueueNodes, PlatGroups)

from rest_api import filters as Prifilters
from rest_api.authentication import IsOwnerResource, AdminResource
from rest_api.account.serializer import RoleSerializer
from rest_api.core.serializer import PlatFormSerializer
from rest_api.cmdb.serializer import OpsHostSerializer
from rest_api.app.serializer import (ScriptSerializer, WorkFlowSerializer, ZoneSerializer, \
        TaskSerializer, TaskStepSerializer, TaskResultSerializer, TaskResultDetailSerializer, \
        ExecuteWorkFlowSerializer, ModifyZoneSerializer, CronJobSerializer, NodeSerializer)
logger = logging.getLogger(__name__)

def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404
    if the filter_kwargs don't match the required types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError):
        raise Http404

# Tree
@api_view(['GET'])
@permission_classes((IsOwnerResource,))
def AppTree(req, tab, app_uuid):
    if tab not in  ('hosts', 'zones'):
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    try:
        if req.user.is_admin:
            app = Apps.objects.get(uuid=app_uuid)
        else:
            app = req.user.roles.filter(app_id=app_uuid)[0].app
    except Exception,e:
        logger.error(e, exc_info=True)
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    Tree = []
    in_group = set()
    for child in req.user.groups.all():
        group = {"title": child.name, "key": child.uuid, "url": \
                reverse("api_%s_group" % tab, kwargs={"app_uuid": app.uuid, "group_uuid": child.uuid}), \
                "folder": True, "children": []}
        children = []
        for plat in child.platforms.all():
            children.append({"title":  plat.platname, "key": plat.uuid, "url": \
                    reverse("api_%s" % tab, kwargs={"app_uuid": app.uuid, "plat_uuid": plat.uuid})})
            in_group.add(plat.platid)
        group["children"] = sorted(children, key=lambda x:x["title"])
        Tree.append(group)

    _Tree = []
    for plat in app.platforms.all():
        if plat.platid in in_group:
            continue
        _Tree.append({"title": plat.platname, "key": plat.uuid, "url": \
                reverse("api_%s" % tab, kwargs={"app_uuid": app.uuid, "plat_uuid": plat.uuid})})

    _Tree = sorted(_Tree, key=lambda x:x["title"])
    Tree += _Tree
    if tab == "hosts":
        Tree.append({"title": u"闲置池", "key":"free", "url": \
                reverse("api_%s" % tab, kwargs={"app_uuid": app.uuid, "plat_uuid": "None"})})
    return Response(Tree)

# Zone
@api_view(['POST'])
@permission_classes((IsOwnerResource,))
def AppZoneCreate(req, app_uuid, plat_uuid):
    try:
        data = ModifyZoneSerializer(data=req.data)
        if data.is_valid():
            if Zones.objects.exist_zone(app_uuid, plat_uuid, data.validated_data["sid"]) > 0:
                return Response({"success": False, "msg": _(u'请求创建的区服已存在!')})
            with transaction.atomic():
                host = Assets.objects.get(pk=data.validated_data["host"])
                for _sid in data.validated_data["sid"]:
                    zone = Zones(sid=_sid, alias=_sid, app_uuid=app_uuid, plat_uuid=plat_uuid, host=host)
                    zone.save()
                ########### 联动修改服务器的app_detail ############
                app_detail = sorted([i for i in host.app_detail.split(",") if i])
                app_detail += data.validated_data["sid"]
                host.app_detail = ",".join(sorted(map(str, app_detail)))
                host.save(update_fields=['app_detail'])
                ########### 联动修改app_detail结束 ############

                return Response({"success": True, "msg": _(u'区服创建成功!')})
            return Response({"success": False, "msg": _(u'区服创建失败!')})
        else:
            return Response({"success": False, "msg": data.errors})
    except Exception,e:
        logger.error(e, exc_info=True)
        return Response({"success": False, "msg": _(u'区服创建失败!')})
    return Response({"success": True, "msg": _(u'区服创建成功!')},
            status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((IsOwnerResource,))
def AppZoneMerge(req, app_uuid, plat_uuid):
    try:
        data = ModifyZoneSerializer(data=req.data)
        if data.is_valid():
            if Zones.objects.exist_zone(app_uuid, plat_uuid, data.validated_data["sid"]) != len(data.validated_data["sid"]):
                return Response({"success": False, "msg": _(u'请求合并的区服不存在!')})
            with transaction.atomic():
                post_sid = map(int, data.validated_data["sid"])
                zone = Zones.objects.get(app_uuid=app_uuid, plat_uuid=plat_uuid, sid=min(post_sid))
                if zone.contain(max(post_sid)):
                    base_host = zone.host
                    app_detail = sorted([i for i in base_host.app_detail.split(",") if i])
                    for detail in app_detail:
                        if detail == zone.alias or detail.startswith("%s-" % zone.sid):
                            app_detail.remove(detail)
                    zone.alias = "%s-%s" % (min(post_sid), max(post_sid))
                    zone.save(update_fields=["alias"])
                    print zone.alias, zone.sid
                    ########### 联动修改服务器的app_detail ############
                    app_detail.append("%s-%s" % (min(post_sid), max(post_sid)))
                    base_host.app_detail = ",".join(sorted(map(str, app_detail)))
                    base_host.save(update_fields=['app_detail'])
                    print app_detail
                    ########### 联动修改app_detail结束 ############

                post_sid = sorted(post_sid)

                ########### 联动修改服务器的app_detail ############
                drop_set = Zones.objects.filter(app_uuid=app_uuid, plat_uuid=plat_uuid, sid__in=post_sid[1:])
                for drop_zone in drop_set.all():
                    host = drop_zone.host
                    d_app_detail = sorted([i for i in host.app_detail.split(",") if i])
                    print "Before:", d_app_detail
                    for d_detail in d_app_detail:
                        if str(d_detail) == str(drop_zone.alias) or str(d_detail) == str(drop_zone.sid):
                            d_app_detail.remove(d_detail)
                    print "After:", d_app_detail
                    host.app_detail = ",".join(sorted(map(str, d_app_detail)))
                    host.save(update_fields=['app_detail'])
                ########### 联动修改app_detail结束 ############
                drop_set.delete()
                return Response({"success": True, "msg": _(u'区服合并成功!')})
        return Response({"success": False, "msg": data.errors})
    except Exception,e:
        logger.error(e, exc_info=True)
        return Response({"success": False, "msg": _(u'区服合并失败!')})


class ZoneFilter(filters.FilterSet):
    min_sid = django_filters.NumberFilter(name="sid", lookup_type='gte')
    max_sid = django_filters.NumberFilter(name="sid", lookup_type='lte')

    class Meta:
        model = Zones
        fields = ['min_sid', 'max_sid']

class AppZone(generics.ListAPIView):
    serializer_class = ZoneSerializer
    pagination_class = ZonePagination
    permission_classes = (IsOwnerResource,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ZoneFilter

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        plat_uuid = self.kwargs['plat_uuid']
        query = Zones.objects.safe_select(self.request.user, app_uuid, plat_uuid=plat_uuid)
        return query

class AppGroupZone(generics.ListAPIView):
    serializer_class = ZoneSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ZoneFilter

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        group_uuid = self.kwargs['group_uuid']
        try:
            group = PlatGroups.objects.get(user=self.request.user.uuid, app=app_uuid, uuid=group_uuid)
        except Exception,e:
            return []
        return Zones.objects.filter(app_uuid=app_uuid, plat_uuid__in=group.platforms.all()).all()

# Host
class AppHost(generics.ListAPIView):
    serializer_class = OpsHostSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)
    
    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        plat_uuid = self.kwargs['plat_uuid']
        if plat_uuid == "None":
            return Assets.objects.filter(app_id=app_uuid).all()
        return Assets.objects.filter(app_id=app_uuid, platform_id=plat_uuid).all()

class AppHostSearch(generics.ListAPIView):
    serializer_class = OpsHostSerializer
    pagination_class = PagePagination
    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('remote_ip', 'public_ip', 'virtual_ip', 'app_detail',\
            'idc_location__idc_region', 'idc_cabinet__name')

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        if self.request.user.is_admin:
            return Assets.objects.filter(app_id=app_uuid).all()
        try:
            role = self.request.roles.get(app_id=app_uuid)
        except:
            return []
        ps = [i.uuid for i in role.platforms.all()]
        query = Assets.objects.filter(app_id=app_uuid, platform_id__in=ps).all()
        return query + Assets.objects.filter(app_id=app_uuid, platform_id__isnull=True).all()

class AppGroupHost(generics.ListAPIView):
    serializer_class = OpsHostSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        group_uuid = self.kwargs['group_uuid']
        try:
            group = PlatGroups.objects.get(user=self.request.user.uuid, app=app_uuid, uuid=group_uuid)
        except Exception,e:
            return []
        return Assets.objects.filter(app=app_uuid, platform__in=group.platforms.all()).all()

# script and jobs
class ScriptList(generics.ListAPIView):
    serializer_class = ScriptSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('userid',)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        private = Scripts.objects.filter(userid=self.request.user.uuid, mode=1).all()
        return Scripts.objects.filter(app=app_uuid, mode=2).all() | private

class ScriptDelete(generics.DestroyAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "script_uuid"

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        return Scripts.objects.filter(app_id=app_uuid).all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        if not self.request.user.cmd_written_ready(obj.app.uuid):
            return Response({"success":False, "msg":u"您没有权限删除此脚本"})
        s = Scripts.objects.get(pk=self.kwargs["script_uuid"])
        if s.scriptflow.first():
            return Response({"success":False, "msg":u"此脚本被编排在作业中,无法删除"})
        return obj

class PlatGroupDelete(generics.DestroyAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "group_uuid"
    
    def get_queryset(self):
        return PlatGroups.objects.filter(user=self.request.user).all()

class WorkFlowList(generics.ListAPIView):
    queryset = WorkFlows.objects.all()
    serializer_class = WorkFlowSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

class WorkFlowDelete(generics.DestroyAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "workflow_uuid"

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        return WorkFlows.objects.filter(app__uuid=app_uuid).all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        if not self.request.user.cmd_written_ready(obj.app.uuid):
            return Response({"success":False,"msg":u"您没有权限删除此脚本"})
        return obj

# Plat
class PlatFormList(generics.ListAPIView):
    serializer_class = PlatFormSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        app = Apps.objects.get(uuid=app_uuid)
        return app.platforms.all()

# Role
class RoleList(generics.ListAPIView):
    serializer_class = RoleSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        app = Apps.objects.get(uuid=app_uuid)
        return app.roles.all()

class RolesDelete(generics.DestroyAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "role_uuid"

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        return AuthRoles.objects.filter(app_id=app_uuid).all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        if not self.request.user.is_admin:
            roles = self.request.user.roles.filter(app__uuid=app_uuid).first()
            if roles and roles.staff == "1":
                pass
            else:
                return Response({"success":False,"msg":u"您没有权限删除此角色"})

# Task
class TaskList(generics.ListAPIView):
    serializer_class = TaskSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status',)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        return Tasks.objects.filter(app__uuid=app_uuid).all()

class TaskStepList(generics.ListAPIView):
    serializer_class = TaskStepSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status',)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        task_uuid = self.kwargs['task_uuid']

        return Tasks.objects.get(app__uuid=app_uuid, pk=task_uuid).steps.all()

class TaskResultList(generics.ListAPIView):
    serializer_class = TaskResultSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

    def get_queryset(self):
        app_uuid = self.kwargs['app_uuid']
        task_uuid = self.kwargs['task_uuid']
        step_uuid = self.kwargs['step_uuid']

        rs = Tasks.objects.get(app__uuid=app_uuid, pk=task_uuid).\
                steps.get(pk=step_uuid).results

        if self.request.user.is_admin:
            return rs.all()
        else:
            has_plats = self.request.user.roles.get(app__uuid=app_uuid).platforms.\
                    values_list('uuid', flat=True)
            return rs.filter(plat_uuid__in=has_plats).all()

class TaskResultDetail(generics.RetrieveAPIView):
    queryset = TaskResults.objects.all()
    serializer_class = TaskResultDetailSerializer
    permission_classes = (IsOwnerResource,)

    lookup_url_kwarg = "result_uuid"
    lookup_field = "uuid"

@api_view(['POST'])
@permission_classes((IsOwnerResource,))
def TaskClose(req, app_uuid):
    uuids = req.data.get("uuids", "")
    if uuids:
        uuids = [i for i in uuids.split(",") if i]
    else:
        return Response({"success":False, "msg":_(u"缺少参数uuids")})
    target = Tasks.objects.filter(pk__in=uuids)
    if set([i[0] for i in target.values_list('user_id') if i[0]]) != set([req.user.uuid]):
        return Response({"success":False, "msg":_(u"您没有权限关闭别人的任务!")})
    try:
        target.update(status=3)
        celery.send_task('close_task', 
                args=[req.user.account, uuids])
        return Response({"success":True, "msg":_(u"任务关闭成功!")})
    except Exception,e:
        logger.exception(e)
        return Response({"success":False, "msg":_(u"任务关闭失败!")})

@api_view(['POST'])
@permission_classes((IsOwnerResource,))
def ExecuteFlow(req, app_uuid, tab, uuid):
    if tab not in ("plat", "group"):
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    try:
        target_app = Apps.objects.get(pk=app_uuid)
    except:
        return Response({"success": False, "msg": _(u'应用不存在!')})
    data = ExecuteWorkFlowSerializer(data=req.data)
    if data.is_valid():
        if data.validated_data["kind"] == "zone":
            if not data.validated_data.get("region", None):
                return Response({"success": False, "msg": _(u"缺少区域ID!")})
            if data.validated_data["region"] != '__all__':
                if not cache.get(utils.REDIS_REGION % (req.user.uuid, app_uuid, data.validated_data["region"])):
                    return Response({"success": False, "msg": _(u"区域ID不存在!")})

            if tab == "plat":
                if not Zones.objects.safe_range(req.user, app_uuid,
                        data.validated_data["uuids"], plat_uuid=uuid):
                    return Response({}, status=status.HTTP_403_FORBIDDEN)
            else:
                if not Zones.objects.safe_range(req.user, app_uuid,
                        data.validated_data["uuids"], group_uuid=uuid):
                    return Response({}, status=status.HTTP_403_FORBIDDEN)
            target_map = ("Zones", data.validated_data["uuids"])
        else:
            target_map = ("Assets", data.validated_data["uuids"])
        if data.validated_data.get("cronExpression", None):
            crontab = CrontabSchedule.objects.filter(**data.validated_data["cronExpression"]).first()
            if not crontab:
                crontab = CrontabSchedule(**data.validated_data["cronExpression"])
                crontab.save()
            periodic_task = PeriodicTask(
                    name=data.validated_data["name"],
                    task='exec_workflow',
                    crontab=crontab,
                    args=json.dumps([
                        req.user.account,
                        data.validated_data["workflow_uuid"],
                        target_map,
                    ]),
                    exchange='surge',
                    routing_key='senders',
                    kwargs=json.dumps({
                        "inject_env": data.validated_data.get("inject_env", None),
                        "app_uuid": app_uuid,
                        "first": True,
                        "trigger": 2,
                        "tab": tab,
                        "uuid": uuid,
                        "region": data.validated_data["region"],
                        "timeout": data.validated_data.get("timeout", None)
                        }))
            periodic_task.save()
            periodic_task_meta = PeriodicTaskMeta(periodictask=periodic_task, 
                    userid=req.user.uuid, user=req.user.name, app_uuid=app_uuid,
                    appalias=target_app.appalias)
            periodic_task_meta.save()

            return Response({"success": True, "msg": _(u'定时成功!')})
            

        print data.validated_data
        celery.send_task('exec_workflow', 
                args=[
                    req.user.account,
                    data.validated_data["workflow_uuid"],
                    target_map],
                exchange='surge',
                routing_key='senders',
                kwargs={
                    "inject_env": data.validated_data.get("inject_env", None),
                    "app_uuid": app_uuid,
                    "first": True,
                    "trigger": 1,
                    "tab": tab,
                    "uuid": uuid,
                    "region": data.validated_data["region"],
                    "timeout": data.validated_data.get("timeout", None)
                    })
    else:
        return Response({"success": False, "msg": data.errors}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"success": True, "msg": _(u'指令发送成功,请等候!')})


class CronJob(generics.ListAPIView):
    serializer_class = CronJobSerializer
    pagination_class = PagePagination
    permission_classes = (IsOwnerResource,)

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        return PeriodicTaskMeta.objects.filter(app_uuid=app_uuid, periodictask__enabled=True).all()

@api_view(['DELETE'])
@permission_classes((IsOwnerResource,))
def CronJobDelete(req, app_uuid, job_id):
    try:
        Job = PeriodicTaskMeta.objects.filter(app_uuid=app_uuid).get(pk=job_id)
    except:
        return Response({"success": False, "msg": _(u"指定的任务不存在!")})
    try:
        Job.periodictask.delete()
        cid = Job.crontab_id
        Job.delete()
        CrontabSchedule.objects.filter(pk=cid).delete()
    except:
        return Response({"success": False, "msg": _(u"删除定时任务失败!")})
    return Response({"success": True, "msg": _(u"删除定时任务成功!")})

class NodesList(generics.ListAPIView):
    serializer_class = NodeSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)

    def get_queryset(self):
        if self.request.user.is_admin:
            return QueueNodes.objects.all()
        return []

class NodeSearch(generics.ListAPIView):
    serializer_class = NodeSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'rabbitmq_host')

    def get_queryset(self):
        if self.request.user.is_admin:
            return QueueNodes.objects.all()
        return []

@api_view(['GET'])
def RegionList(req, app_uuid, sub_uuid):
    regions = cache.keys(utils.REDIS_REGION_RE % (req.user.uuid, app_uuid))
    results = []
    for key in regions:
        region = json.loads(cache.get(key))
        try:
            PlatGroups.objects.get(pk=sub_uuid, user=req.user)
            url = "%s?min_sid=%s&max_sid=%s" % (reverse("api_zones_group", \
                    kwargs={"app_uuid":app_uuid, "group_uuid": sub_uuid}), region["min_value"], region["max_value"])
        except:
            url = "%s?min_sid=%s&max_sid=%s" % (reverse("api_zones", \
                    kwargs={"app_uuid":app_uuid, "plat_uuid": sub_uuid}), region["min_value"], region["max_value"])

        region["url"] = url
        region["region_uuid"] = key.split(":")[-1]
        results.append(region)
    return Response({"count": len(regions), "results": results})

@api_view(['DELETE'])
def RegionDelete(req, app_uuid, region_uuid):
    if cache.delete(utils.REDIS_REGION % (req.user.uuid, app_uuid, region_uuid)):
        return Response({"success": True, "msg": _(u"区域删除成功!!")})
    return Response({"success": False, "msg": _(u"区域不存在!")})
