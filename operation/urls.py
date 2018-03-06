#coding:utf-8
from django.conf.urls import patterns, url
from operation.views import apps as app_view
from operation.views import platform as platform_view
from operation.views import script as script_view
from operation.views import zones as zone_view
from operation.views import nodes as node_view

urlpatterns = patterns('operation.views',
    url(r'^apps/create/?$', app_view.AppCreate.as_view(), name='app_create'),
    url(r'^apps/(?P<app_uuid>[a-z0-9]+)/update/?$', app_view.AppUpdate.as_view(), name='app_update'),
    url(r'^apps/(?P<app_uuid>[a-z0-9]+)/?$', 'apps.AppLoad', name='app_load'),

    url(r'^plat/create/?$', platform_view.PlatCreate.as_view(), name='plat_create'),
    url(r'^plat/(?P<plat_uuid>[a-z0-9]+)/update/?$', platform_view.PlatUpdate.as_view(), name='plat_update'),
    url(r'^platgroup/(?P<app_uuid>[a-z0-9]+)/create/?$', platform_view.PlatGroupCreate.as_view(), name="platgroup_create"),
    url(r'^platgroup/(?P<group_uuid>[a-z0-9]+)/update/?$', platform_view.PlatGroupUpdate.as_view(), name="platgroup_update"),

    url(r'^(?P<app_uuid>[a-z0-9]+)/plat/create/?$', platform_view.AppPlatCreate.as_view(), name="appplat_create"),
    url(r'^(?P<app_uuid>[a-z0-9]+)/region/create/?$', platform_view.RegionCreate.as_view(), name='region_create'),

    #url(r'^(?P<app_uuid>[a-z0-9]+)/plat/(?P<plat_uuid>[a-z0-9]+)/zones/create/?$', zone_view.ZoneCreate.as_view(), name='zone_create'),

    url(r'^(?P<app_uuid>[a-z0-9]+)/workflow/create/??$', script_view.WorkFlowCreate.as_view(), name='workflow_create'),
    url(r'^(?P<app_uuid>[a-z0-9]+)/workflow/(?P<workflow_uuid>[a-z0-9]+)/update/??$', script_view.WorkFlowUpdate.as_view(), name='workflow_update'),

    url(r'^(?P<app_uuid>[a-z0-9]+)/script/create/?$', script_view.ScriptCreate.as_view(), name='script_create'),
    url(r'^(?P<app_uuid>[a-z0-9]+)/script/(?P<script_uuid>[a-z0-9]+)/update/?$', script_view.ScriptUpdate.as_view(), name='script_update'),

    url(r'^nodes/create/?$', node_view.NodeCreate.as_view(), name='nodes_create'),
    url(r'^nodes/(?P<node_uuid>[a-z0-9]+)/update/?$', node_view.NodeUpdate.as_view(), name='nodes_update'),
)
