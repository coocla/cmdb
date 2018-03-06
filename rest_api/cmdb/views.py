#coding:utf-8
import logging
from django.forms.models import model_to_dict
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse
from django.views.generic import View

import django_filters
from rest_framework import generics
from rest_framework import status
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from surge.common import utils
from surge.celery import celery
from surge.common.pagination import PagePagination

from operation.models import Apps, PlatForms
from asset import dnspod
from asset.pyzabbix import Zabbix
from asset.models import (Assets, IdcRegions, IdcCabinets, Divisions, AppMode, AccelerateCDN,
        CDNCompany, Contracts, RegisterDomain, ResolveAudit)

from rest_api import filters as Prifilters
from rest_api.authentication import AdminResource, DataResource
from rest_api.cmdb.serializer import (HostSerializer, DivisionSerializer, IdcRegionSerializer,
        IdcCabinetSerializer, AppModeSerializer, AccelerateSerializer, CDNSerializer,
        HostCreateSerializer, ContractSerializer, DomainSerializer, ResolverSerializer,
        ResolverTempSerializer, BulkSerializer)

logger = logging.getLogger(__name__)



@api_view(['GET'])
def BaseMenu(req):
    Menu = [
        {"name": u"概览", "en": "dashboard", "url": reverse("api_user_widgets", kwargs={"app_uuid": 1}), "icon": "glyphicon glyphicon-dashboard"},
        {"name": u"业务", "en": "instance", "url": reverse("api_cmdb_tree", kwargs={"root":"division"}), "icon": "glyphicon glyphicon-cloud"},
        {"name": u"机房", "en": "location", "url": reverse("api_cmdb_tree", kwargs={"root":"idc"}), "icon":"glyphicon glyphicon-lamp"},
        {"name": u"CDN域名", "en": "accelerate", "url": reverse("api_accelerates"), "icon": "glyphicon glyphicon-flash"},
        {"name": u"域名解析", "en": "resolve", "url": reverse("api_resolves"), "icon": "glyphicon glyphicon-hourglass"},
    ]
    if req.user.is_admin or req.user.dataer:
        Menu += [
            {"name": u"CDN厂商", "en": "cdn", "url": reverse("api_cdns"), "icon": "glyphicon glyphicon-phone-alt"},
            {"name": u"域名注册", "en": "domain", "url": reverse("api_domains"), "icon": "glyphicon glyphicon-pencil"},
            {"name": u"组织架构", "en": "division", "url": reverse("api_divisions"), "icon": "glyphicon glyphicon-education"},
            {"name": u"合作机房", "en": "idc", "url": reverse("api_idcs"), "icon": "glyphicon glyphicon-yen"},
            {"name": u"合同管理", "en": "contract", "url": reverse("api_contract"), "icon": "glyphicon glyphicon-duplicate"},
        ]
    return Response(Menu)


@api_view(['GET'])
def BaseTree(req, root):
    Tree = GenerateTree(req, root)
    return Response(Tree.tree())

class GenerateTree(object):
    def __init__(self, req, root):
        self.req = req
        self.root = root

        self.base = self._initial()

    def _initial(self):
        if self.req.user.is_admin:
            self.instances = Assets.objects.filter(deleted=False)
            if self.root == "idc":
                return IdcRegions.objects.all()
            return Divisions.objects.all()
        self.instances = Assets.objects.filter(app_id__in=self.req.user.owner_app()).filter(deleted=False)
        if self.root == "idc":
            return IdcRegions.objects.filter(pk__in=self.req.user.owner_idc())
        return Divisions.objects.filter(pk__in=self.req.user.owner_division()).all()

    def division(self):
        Tree = []
        for division in self.base:
            if not Assets.objects.filter(division_id=division.uuid).first():
                continue
            level = {"title":division.name,"tooltip":division.name,"key":division.uuid,"folder":True,"url": "%s%s" % (
                reverse("api_hosts_all"),"?division_id=%s" % division.uuid),"children":[]}
            app_in_tree = []
            for app_info in self.instances.filter(division_id=division.uuid).values("app").distinct():
                if app_info["app"] in app_in_tree:
                    continue
                app_in_tree.append(app_info["app"])
                if app_info["app"] == None:
                    app = utils.Free()
                else:
                    app = Apps.objects.get(pk=app_info["app"])
                level_2 = {"title":app.appalias,"tooltip":app.appalias,"key":app.uuid,"folder":True,"children":[],"url":"%s%s" % (
                    reverse("api_hosts_all"),"?division_id=%s&app_id=%s" % (division.uuid,app.uuid))}
                if app.uuid == None:
                    continue
                plat_in_app = []

                if not self.req.user.is_app_admin(app.uuid):
                    limit_plats = self.req.user.roles.get(app_id=app.uuid).platforms.all()
                else:
                    limit_plats = None

                if limit_plats:
                    owner_plats = self.instances.filter(division_id=division.uuid, app_id=app.uuid, platform_id__in=limit_plats).values("platform").distinct()
                else:
                    owner_plats = self.instances.filter(division_id=division.uuid, app_id=app.uuid).values("platform").distinct()
                for plat_info in owner_plats:
                    if plat_info["platform"] in plat_in_app:
                        continue
                    plat_in_app.append(plat_info["platform"])

                    if plat_info["platform"] == None:
                        plat = utils.Free()
                    else:
                        plat = PlatForms.objects.get(pk=plat_info["platform"])

                    level_2["children"].append({"title":plat.platalias,"tooltip":plat.platalias,"key":plat.uuid, "url":"%s%s" % (
                        reverse("api_hosts_all"),"?division_id=%s&app_id=%s&platform_id=%s" % (
                            division.uuid,app.uuid,plat.uuid))})
                level["children"].append(level_2)
            _free = utils.Free()
            Tree.append(level)
        Tree.append({"title":_free.appalias,"tooltip":_free.appalias,"key":utils.UUID(),"folder":True,"children":[],"url":"%s%s" % (
            reverse("api_hosts_all"),"?division_id=%s" % (_free.uuid))})
        return sorted(Tree, key=lambda x:x["title"])

    def idc(self):
        Tree = []
        has_free = False
        for idc in self.base:
            if not Assets.objects.filter(idc_location_id=idc.uuid).first():
                continue
            level = {"title":"[%s] %s" % (idc.idc, idc.idc_region),"tooltip":"[%s] %s" % (idc.idc, idc.idc_region),"key":idc.uuid,"folder":True,
                    "url":"%s%s" % (reverse("api_hosts_all"),"?idc_location_id=%s" % idc.uuid),"children":[]}
            for cabinet_info in self.instances.filter(idc_location__uuid=idc.uuid).values("idc_cabinet").distinct():
                if cabinet_info["idc_cabinet"] == None:
                    if has_free:
                        continue
                    cabinet = utils.Free()
                    has_free = True
                else:
                    cabinet = IdcCabinets.objects.get(pk=cabinet_info["idc_cabinet"])
                level["children"].append({"title":cabinet.name,"tooltip":cabinet.name,"key":cabinet.uuid,"url":"%s%s" % (
                    reverse("api_hosts_all"),"?idc_location_id=%s&idc_cabinet_id=%s" % (idc.uuid, cabinet.uuid))})
            Tree.append(level)
        return sorted(Tree, key=lambda x:x["title"])

    def tree(self):
        return getattr(self, self.root, "division")()


class HostFilter(django_filters.FilterSet):
    division_id = django_filters.MethodFilter()
    app_id = django_filters.MethodFilter()
    platform_id = django_filters.MethodFilter()
    idc_location_id = django_filters.MethodFilter()
    idc_cabinet_id = django_filters.MethodFilter()


    class Meta:
        model = Assets
        fields = ['division_id', 'app_id', 'platform_id', 'idc_location_id', 'idc_cabinet_id']

    def filter_division_id(self, queryset, value):
        if value == "None":
            return queryset.filter(division_id__isnull=True).all()
        return queryset.filter(division_id=value).all()

    def filter_app_id(self, queryset, value):
        if value == "None":
            return queryset.filter(app_id__isnull=True).all()
        return queryset.filter(app_id=value).all()

    def filter_idc_cabinet_id(self, queryset, value):
        if value == "None":
            return queryset.filter(idc_cabinet_id__isnull=True).all()
        return queryset.filter(idc_cabinet_id=value).all()

    def filter_idc_location_id(self, queryset, value):
        if value == "None":
            return queryset.filter(idc_location_id__isnull=True).all()
        return queryset.filter(idc_location_id=value).all()

    def filter_platform_id(self, queryset, value):
        if value == "None":
            return queryset.filter(platform_id__isnull=True).all()
        return queryset.filter(platform_id=value).all()

class HostSearch(generics.ListAPIView):
    serializer_class = HostSerializer
    pagination_class = PagePagination
    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('remote_ip', 'public_ip', 'virtual_ip', 'serial_number', 'app__appname', \
            'platform__platname', 'idc_location__idc_region', 'idc_cabinet__name')

    def get_queryset(self):
        if self.request.user.is_admin:
            return Assets.objects.all()
        return Assets.objects.filter(app_id__in=self.request.user.owner_app()).all()

class HostList(generics.ListAPIView):
    serializer_class = HostSerializer
    pagination_class = PagePagination

    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = HostFilter
    ordering_fields = '__all__'
    ordering = ('public_ip', )

    def get_queryset(self):
        if self.request.user.is_admin:
            return Assets.objects.all()
        return Assets.objects.filter(app_id__in=self.request.user.owner_app()).all()

@api_view(['POST'])
def HostCreate(request):
    seria = HostCreateSerializer(data=request.data, context={"request": request})
    if seria.is_valid():
        host = seria.save()
        if isinstance(host, unicode):
            return Response({"success": False, "msg": host})
        data = model_to_dict(host, exclude=['launch_date', 'expire_date'])
        return Response({"success": True, "msg": data})
    return Response({"success": False, "msg": seria.errors})

@api_view(['POST'])
def HostBulkUpdate(request):
    seria = BulkSerializer(data=request.data)
    seria.is_valid()
    if request.data["uuids"]:
        try:
            uuids = map(int, request.data["uuids"].split(","))
            data = seria.data.copy()
            for k,v in data.items():
                if not v:
                    data.pop(k)
            Assets.objects.filter(pk__in=uuids).update(**data)
        except Exception,e:
            logger.error(e, exc_info=True)
            return Response({"success": False, "msg": _(u'批量更新失败!')})
        return Response({"success": True, "msg": _(u'批量更新成功!')})
    return Response({"success": False, "msg": _('Field uuid is required!')})

@api_view(['POST'])
def HostBulkDelete(request):
    if request.data.get("uuids", None):
        if not isinstance(request.data["uuids"], list):
            uuids = request.data["uuids"].split(",")
        try:
            uuids = map(int, uuids)
        except:
            Response({"success": False, "msg": _(u'参数格式错误!')}, status=status.HTTP_400_BAD_REQUEST)
        try:
            Assets.objects.filter(pk__in=uuids).update({"source": 1, "deleted": True})
        except Exception,e:
            logger.error(e, exc_info=True)
            return Response({"success": False, "msg": _(u'批量下架失败!')})
        return Response({"success": True, "msg": _(u'批量下架成功!')})
    return Response({"success": False, "msg": _('Field uuid is required!')})

@api_view(['POST'])
def HostBulkMonitor(request):
    if req.POST.get("templateids", None):
        templateids = req.POST["templateids"].split(",")
    else:
        return JsonResponse({"success": False, "msg": u"参数不完整!"})
    if req.POST.get("hostids", None):
        hostids = req.POST["hostids"].split(",")
    else:
        return JsonResponse({"success": False, "msg": u"参数不完整!"})
    if req.POST.get("groupid", None) and req.POST.get("proxy_hostid", None):
        return JsonResponse({"success": False, "msg": u"参数不完整!"})
    try:
        celery.send_task('BulkMonitor', args=[req.user.uuid, hostids, templateids, \
                req.POST["groupid"], req.POST["proxy_hostid"]])
        return JsonResponse({"success": True, "msg":_(u'批量添加监控提交成功, 请等候!')})
    except Exception,e:
        logger.error(e, exc_info=True)
        return JsonResponse({"success": False, "msg":_(u'批量添加监控失败')})


class HostMonitor(View):
    def get(self, req, host_uuid):
        try:
            instance = Assets.objects.get(pk=host_uuid)
        except:
            return JsonResponse({})
        zabbix = Zabbix()
        return JsonResponse({"linked_templates": zabbix.used_template(host_uuid),
                             "graphs": zabbix.graph_info(host_uuid)})

    def post(self, req, host_uuid):
        if req.POST.get("templateids", None):
            templateids = req.POST["templateids"].split(",")
            if isinstance(templateids, list):
                try:
                    instance = Assets.objects.get(pk=host_uuid)
                except:
                    return JsonResponse({"success": False, "msg": u"服务器不存在!"})
                if not (req.POST.get("groupid", None) and req.POST.get("proxy_hostid", None)):
                    return JsonResponse({"success": False, "msg": u"参数格式不正确!"})

                zabbix = Zabbix()
                data = zabbix.create_monitor(host_uuid, req.POST["groupid"], \
                        req.POST["proxy_hostid"], templateids)
                if data:
                    return JsonResponse({"success": True, "msg": u"监控创建成功!"})
                return JsonResponse({"success": False, "msg": u"监控创建失败!"})
        return JsonResponse({"success": False, "msg": u"参数格式不正确!"})

    def put(self, req, host_uuid):
        if req.POST.get("templateids", None):
            templateids = req.POST["templateids"].split(",")
            if isinstance(templateids, list):
                try:
                    instance = Assets.objects.get(pk=host_uuid)
                except:
                    return JsonResponse({"success": False, "msg": u"服务器不存在!"})
                if not (req.POST.get("groupid", None) and req.POST.get("proxy_hostid", None)):
                    return JsonResponse({"success": False, "msg": u"参数格式不正确!"})

                zabbix = Zabbix()
                data = zabbix.update_host_template(host_uuid, req.POST["groupid"], \
                        req.POST["proxy_hostid"], templateids)
                if data:
                    return JsonResponse({"success": True, "msg": u"监控模版更新成功!"})
                return JsonResponse({"success": False, "msg": u"监控模版更新失败!"})
        return JsonResponse({"success": False, "msg": u"参数格式不正确!"})


@api_view(['GET'])
def HostMonitorInfo(request):
    zabbix = Zabbix()
    return JsonResponse({"templates": zabbix.template_list(),
                         "proxys": zabbix.proxy_list(),
                         "groups": zabbix.group_list()})

@api_view(['GET'])
def HostMonitorStatus(request, host_uuid):
    zabbix = Zabbix()
    return Response(zabbix.monitor_status(host_uuid)[0])

@api_view(['POST'])
def HostEnableMonitor(request):
    if request.data.get("uuids", None):
        try:
            uuids = map(int, request.data["uuids"].split(","))
        except:
            Response({"success": False, "msg": _(u'参数格式错误!')}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(uuids, list):
            celery.send_task('EnableMonitor', args=[request.user.uuid, uuids],
                    exchange='surge', routing_key='monitor')
            return Response({"success": True, "msg": _(u"启用监控提交成功,请等候!")})
        else:
            return Response({"success": False, "msg": _(u'参数格式不正确!')}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"success": False, "msg": _(u'缺少参数!')}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def HostDisableMonitor(request):
    if request.data.get("uuids", None):
        uuids = request.data["uuids"].split(",")
        try:
            uuids = map(int, request.data["uuids"].split(","))
        except:
            Response({"success": False, "msg": _(u'参数格式错误!')}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(uuids, list):
            celery.send_task('DisableMonitor', args=[request.user.uuid, uuids],
                    exchange='surge', routing_key='monitor')
            return Response({"success": True, "msg": _(u"禁用监控提交成功,请等候!")})
        else:
            return Response({"success": False, "msg": _(u'参数格式不正确!')}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"success": False, "msg": _(u'缺少参数!')}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def HostMonitorGraph(request):
    zabbix = Zabbix()
    graph = zabbix.graph(request.query_params.urlencode())
    return HttpResponse(graph, content_type="image/png")

class DivisionList(generics.ListAPIView):
    queryset = Divisions.objects.all()
    serializer_class = DivisionSerializer
    pagination_class = PagePagination

class DivisionSearch(generics.ListAPIView):
    queryset = Divisions.objects.all()
    serializer_class = DivisionSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)

    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('name',)

class IDCList(generics.ListAPIView):
    queryset = IdcRegions.objects.all()
    serializer_class = IdcRegionSerializer
    pagination_class = PagePagination

class IDCSearch(generics.ListAPIView):
    queryset = IdcRegions.objects.all()
    serializer_class = IdcRegionSerializer
    pagination_class = PagePagination
    permission_classes = (AdminResource,)

    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('idc', 'idc_region')

class IdcCabinetList(generics.ListAPIView):
    serializer_class = IdcCabinetSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        idc_uuid = self.kwargs["idc_uuid"]

        return IdcCabinets.objects.filter(idc__pk=idc_uuid).all()

class AppModeList(generics.ListAPIView):
    queryset = AppMode.objects.all()
    serializer_class = AppModeSerializer
    pagination_class = PagePagination

class AccelerateList(generics.ListAPIView):
    queryset = AccelerateCDN.objects.all()
    serializer_class = AccelerateSerializer
    pagination_class = PagePagination

class AccelerateSearch(generics.ListAPIView):
    serializer_class = AccelerateSerializer
    pagination_class = PagePagination
    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('domain', 'app__appname', 'division__name', 'company__name')

    def get_queryset(self):
        if self.request.user.is_admin:
            return AccelerateCDN.objects.all()
        return AccelerateCDN.objects.filter(app_id__in=self.request.user.owner_app()).all()

@api_view(['POST'])
@permission_classes((DataResource,))
def DeleteAccelerate(req):
    try:
        uuids = req.data.get("uuids", None)
        if not uuids:
            return Response({"success":False,"msg":_(u"缺少参数uuids")})
        celery.send_task('DeleteAccelerate', args=[req.user.uuid, uuids])
        return Response({"success":True,"msg":_(u"删除CND域名提交成功,请等候!")})
    except Exception,e:
        logger.error(e, exc_info=True)
        return Response({"success":False,"msg":_(u"删除CND域名提交失败")})

class CDNCompanyList(generics.ListAPIView):
    serializer_class = CDNSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        if self.request.user.is_admin:
            return CDNCompany.objects.all()
        return []

class CDNSearch(generics.ListAPIView):
    serializer_class = CDNSerializer
    pagination_class = PagePagination
    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('name', 'remark')

    def get_queryset(self):
        if self.request.user.is_admin:
            return CDNCompany.objects.all()
        return []

@api_view(['POST'])
@permission_classes((DataResource,))
def DeleteCDN(req):
    try:
        uuids = req.data.get("uuids", None)
        if not uuids:
            return Response({"success":False,"msg":_(u"缺少参数uuids")})
        celery.send_task('DeleteCDN', args=[req.user.uuid, uuids])
        return Response({"success":True,"msg":_(u"删除CND厂商提交成功,请等候!")})
    except Exception,e:
        logger.error(e, exc_info=True)
        return Response({"success":False,"msg":_(u"删除CND厂商提交失败")})

class ContractList(generics.ListAPIView):
    queryset = Contracts.objects.all()
    pagination_class = PagePagination
    serializer_class = ContractSerializer
    permission_classes = (AdminResource,)

class ContractSearch(generics.ListAPIView):
    queryset = Contracts.objects.all()
    pagination_class = PagePagination
    serializer_class = ContractSerializer
    permission_classes = (AdminResource,)

    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('name', 'number')

@api_view(['GET'])
def cabinetInfo(request):
    idc_id = request.GET.get("idc_id", None)
    if not idc_id:
        return Response({"success": False, "msg": _('Field idc_id is required!')})
    try:
        cabinets = IdcCabinets.objects.filter(idc_id=idc_id).all()
    except Exception as e:
        logger.error(e, exc_info=True)
        return Response({"success": False, "msg": _('idc_id is not invalid!')})
    data = [model_to_dict(i) for i in cabinets]
    return JsonResponse({"results":data})

class DomainList(generics.ListAPIView):
    queryset = RegisterDomain.objects.all()
    pagination_class = PagePagination
    permission_classes = (AdminResource,)
    serializer_class = DomainSerializer

class DomainSearch(generics.ListAPIView):
    queryset = RegisterDomain.objects.all()
    pagination_class = PagePagination
    permission_classes = (AdminResource,)
    serializer_class = DomainSerializer

    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('domain', 'ipc_id', 'ipc_ip', 'expire_date', 'register_date', \
            'register_company', 'register_subject', 'register_site', 'resolve_driver')


class DomainDelete(generics.DestroyAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "domain_uuid"
    queryset = RegisterDomain.objects.all()

    def check_object_permissions(self, request, obj):
        if not (self.user.is_admin or self.user.dataer):
            self.permission_denied(
                request, message=u"您没有权限删除域名"
            )

class ResolverAuditList(generics.ListAPIView):
    pagination_class = PagePagination
    serializer_class = ResolverSerializer

    def get_queryset(self):
        return ResolveAudit.objects.filter(userid=self.request.user.uuid).all()

class ResolverSearch(generics.ListAPIView):
    pagination_class = PagePagination
    serializer_class = ResolverSerializer
    filter_backends = (Prifilters.SearchFilter,)
    search_fields = ('record', 'description', 'username')

    def get_queryset(self):
        if self.request.user.is_admin:
            return ResolveAudit.objects.all()
        return ResolveAudit.objects.filter(userid=self.request.user.uuid).all()


class ResolverView(APIView):
    def post(self, request):
        seria = ResolverTempSerializer(data=request.data)
        if seria.is_valid():
            try:
                dnspod.handler(request, **seria.validated_data)
                return Response({"success":True,"msg":u"域名解析成功!"})
            except Exception,e:
                logger.error(e, exc_info=True)
                return Response({"success":False,"msg":u"内部错误!"})
        return Response({"success":False,"msg":seria.errors})

@api_view(['DELETE'])
def ResolverDelete(request, domain_id, record_id):
    try:
        record = dnspod.RecordInfo(domain_id, record_id)
        if dnspod.veritify(record)[0]:
            rr = dnspod.RecordRemove(record_id, domain_id=domain_id)
            success, msg = dnspod.veritify(rr)
            if success:
                ra = ResolveAudit(userid=request.user.uuid, username=request.user.name, \
                        record="%s.%s" % (record["record"]["sub_domain"], record["domain"]["domain"]),
                        description=u"删除 %(record_type)s 记录 %(record_line)s 线路 值 %(value)s" % record["record"])
                ra.save()
            return Response({"success":success,"msg":msg})
        return Response({"success":False,"msg":dnspod.veritify(record)[1]})
    except Exception,e:
        logger.error(e, exc_info=True)
        return Response({"success":False,"msg":u"内部错误!"})
