#coding:utf-8
from django.conf.urls import patterns, include, url

from rest_api.account import views as account_view
from rest_api.core import views as core_view
from rest_api.cmdb import views as cmdb_view
from rest_api.app import views as app_view
from rest_api.widget import views as widget_view

urlpatterns = [
    # 用户
    url('^users/?$', account_view.UserList.as_view(), name="api_users"),
    url('^users/activate/?$', account_view.activate_user, name="api_active_user"),
    url('^users/deactivate/?$', account_view.deactivate_user, name="api_deactive_user"),
    url('^users/delete/?$', account_view.delete_user, name="api_delete_users"),
    url('^users/(?P<app_uuid>[a-z0-9]+)/widgets/?$', account_view.WidgetList.as_view(), name="api_user_widgets"),
    url('^users/widgets/create/?$', account_view.WidgetAdd, name="api_widget_add"),
    url('^users/(?P<widget_id>[0-9]+)/widgets/?$', account_view.WidgetRemove, name="api_widget_remove"),
    url('^search/users/?$', account_view.UserSearch.as_view(), name="api_users_search"),

    # 角色
    url('^roles/?$', account_view.RoleList.as_view(), name="api_roles"),

    # 应用
    url('^apps/?$', core_view.AppList.as_view(), name="api_apps"),
    url('^apps/create/?$', core_view.AppCreate, name="api_app_create"),
    url('^apps/delete/?$', core_view.DeleteApps, name="api_app_delete"),
    url('^apps/(?P<app_uuid>[a-z0-9]+)/?$', core_view.AppDetail.as_view(), name="api_app_detail"),
    url('^search/apps/?$', core_view.AppsSearch.as_view(), name="api_apps_search"),

    # 平台
    url('^platforms/?$', core_view.PlatFormList.as_view(), name="api_platform"),
    url('^platforms/create/?$', core_view.PlatFormCreate, name="api_platform_create"),
    url('^platforms/delete/?$', core_view.DeletePlatForm, name="api_platform_delete"),
    url('^platforms/(?P<plat_uuid>[a-z0-9]+)/?$', core_view.PlatFormDetail.as_view(), name="api_platform_detail"),
    url('^search/platforms/?$', core_view.PlatFormSearch.as_view(), name="api_platform_search"),

    # 应用中的平台
    url('^(?P<app_uuid>[a-z0-9]+)/(?P<tab>[a-z]+)/tree/$', app_view.AppTree, name="api_ops_tree"),
    url('^(?P<app_uuid>[a-z0-9]+)/plat/(?P<plat_uuid>[a-z0-9]+)/zones/?$', app_view.AppZone.as_view(), name="api_zones"),
    url('^(?P<app_uuid>[a-z0-9]+)/group/(?P<group_uuid>[a-z0-9]+)/zones/?$', app_view.AppGroupZone.as_view(), name="api_zones_group"),
    url(r'^platgroup/(?P<group_uuid>[a-z0-9]+)/delete/?$', app_view.PlatGroupDelete.as_view(), name="api_platgroup_delete"),

    url('^(?P<app_uuid>[a-z0-9]+)/search/hosts/?$', app_view.AppHostSearch.as_view(), name='api_apphost_search'),
    url('^(?P<app_uuid>[a-z0-9]+)/plat/(?P<plat_uuid>[a-z0-9]+)/zones/create/?$', app_view.AppZoneCreate, name="api_zone_create"),
    url('^(?P<app_uuid>[a-z0-9]+)/plat/(?P<plat_uuid>[a-z0-9]+)/zones/merge/?$', app_view.AppZoneMerge, name="api_zone_merge"),

    url('^(?P<app_uuid>[a-z0-9]+)/plat/(?P<plat_uuid>[a-zA-Z0-9]+)/hosts/?$', app_view.AppHost.as_view(), name="api_hosts"),
    url('^(?P<app_uuid>[a-z0-9]+)/group/(?P<group_uuid>[a-z0-9]+)/hosts/?$', app_view.AppGroupHost.as_view(), name="api_hosts_group"),

    url('^(?P<app_uuid>[a-z0-9]+)/scripts/?$', app_view.ScriptList.as_view(), name="api_scripts"),
    url('^(?P<app_uuid>[a-z0-9]+)/scripts/(?P<script_uuid>[a-z0-9]+)/delete/?$', app_view.ScriptDelete.as_view(), name="api_script_delete"),
    url('^(?P<app_uuid>[a-z0-9]+)/workflows/?$', app_view.WorkFlowList.as_view(), name="api_workflows"),
    url('^(?P<app_uuid>[a-z0-9]+)/workflows/(?P<workflow_uuid>[a-z0-9]+)/delete/?$', app_view.WorkFlowDelete.as_view(), name="api_workflow_delete"),

    url('^(?P<app_uuid>[a-z0-9]+)/tasks/?$', app_view.TaskList.as_view(), name="api_tasks"),
    url('^(?P<app_uuid>[a-z0-9]+)/tasks/close/?$', app_view.TaskClose, name="api_close_task"),
    url('^(?P<app_uuid>[a-z0-9]+)/task/(?P<task_uuid>[a-z0-9]+)/steps/?$', app_view.TaskStepList.as_view(), name="api_taskstep"),
    url('^(?P<app_uuid>[a-z0-9]+)/task/(?P<task_uuid>[a-z0-9]+)/step/(?P<step_uuid>[a-z0-9]+)/?$', app_view.TaskResultList.as_view(), name="api_taskstep_result"),
    url('^(?P<app_uuid>[a-z0-9]+)/task/(?P<result_uuid>[a-z0-9]+)/?$', app_view.TaskResultDetail.as_view(), name="api_taskresult_detail"),

    url('^(?P<app_uuid>[a-z0-9]+)/platforms/?$', app_view.PlatFormList.as_view(), name="api_app_platforms"),
    url('^(?P<app_uuid>[a-z0-9]+)/roles/?$', app_view.RoleList.as_view(), name="api_app_roles"),
    url('^(?P<app_uuid>[a-z0-9]+)/roles/(?P<role_uuid>[a-z0-9]+)/delete/?$', app_view.RolesDelete.as_view(), name="api_app_role_delete"),

    url('^(?P<app_uuid>[a-z0-9]+)/(?P<tab>[a-z]+)/(?P<uuid>[a-z0-9]+)/execute/?$', app_view.ExecuteFlow, name="api_execute_workflow"),
    url('^(?P<app_uuid>[a-z0-9]+)/cronjob/?$', app_view.CronJob.as_view(), name='api_cronjob'),
    url('^(?P<app_uuid>[a-z0-9]+)/cronjob/(?P<job_id>[0-9]+)/delete/?$', app_view.CronJobDelete, name='api_cronjob_delete'),
    url('^(?P<app_uuid>[a-z0-9]+)/(?P<sub_uuid>[a-z0-9]+)/regions/?$', app_view.RegionList, name='api_region_list'),
    url('^(?P<app_uuid>[a-z0-9]+)/region/(?P<region_uuid>[a-z0-9]+)/delete/?$', app_view.RegionDelete, name='api_region_delete'),


    # CMDB
    url('^search/hosts/?$', cmdb_view.HostSearch.as_view(), name="api_hosts_search"),
    url('^search/accelerates/?$', cmdb_view.AccelerateSearch.as_view(), name="api_accelerate_search"),
    url('^search/resolvers/?$', cmdb_view.ResolverSearch.as_view(), name="api_resolver_search"),
    url('^search/cdns/?$', cmdb_view.CDNSearch.as_view(), name="api_cdn_search"),
    url('^search/domains/?$', cmdb_view.DomainSearch.as_view(), name="api_domain_search"),
    url('^search/divisions/?$', cmdb_view.DivisionSearch.as_view(), name="api_division_search"),
    url('^search/idcs/?$', cmdb_view.IDCSearch.as_view(), name="api_idc_search"),
    url('^search/contracts/?$', cmdb_view.ContractSearch.as_view(), name="api_contract_search"),

    url('^cmdb/menu/?$', cmdb_view.BaseMenu, name="api_cmdb_menu"),
    url('^cmdb/(?P<root>[a-z]+)/tree/?$', cmdb_view.BaseTree, name="api_cmdb_tree"),
    url('^hosts/?$', cmdb_view.HostList.as_view(), name="api_hosts_all"),
    url('^hosts/create/?$', cmdb_view.HostCreate, name="api_hosts_create"),
    url('^hosts/bulk/monitor', cmdb_view.HostBulkMonitor, name="api_hosts_bulk_monitor"),
    url('^hosts/bulk/update', cmdb_view.HostBulkUpdate, name="api_hosts_bulk_update"),
    url('^hosts/bulk/delete', cmdb_view.HostBulkDelete, name="api_hosts_bulk_delete"),

    url(r'^hosts/(?P<host_uuid>[0-9]+)/monitor/?$', cmdb_view.HostMonitor.as_view(), name='api_host_monitor'),
    url(r'^hosts/(?P<host_uuid>[0-9]+)/monitor/status/?$', cmdb_view.HostMonitorStatus, name='api_host_monitor_status'),
    url(r'^hosts/monitor/enable/?$', cmdb_view.HostEnableMonitor, name='api_host_monitor_enable'),
    url(r'^hosts/monitor/disable/?$', cmdb_view.HostDisableMonitor, name='api_host_monitor_disable'),
    url(r'^hosts/monitor/?$', cmdb_view.HostMonitorInfo, name='api_monitor_info'),
    url(r'^hosts/graph/?$', cmdb_view.HostMonitorGraph, name="api_host_monitor_graph"),

    url('^idcs/?$', cmdb_view.IDCList.as_view(), name="api_idcs"),
    url('^idcs/(?P<idc_uuid>[a-z0-9]+)/cabinets/?$', cmdb_view.IdcCabinetList.as_view(), name="api_cabinets"),

    url('^appmodes/?$', cmdb_view.AppModeList.as_view(), name="api_appmodes"),
    url('^contracts/?$', cmdb_view.ContractList.as_view(), name="api_contract"),
    url('^divisions/?$', cmdb_view.DivisionList.as_view(), name="api_divisions"),

    url('^accelerates/?$', cmdb_view.AccelerateList.as_view(), name="api_accelerates"),
    url('^accelerates/delete/?$', cmdb_view.DeleteAccelerate, name="api_accelerates_delete"),
    url('^cdns/?$', cmdb_view.CDNCompanyList.as_view(), name="api_cdns"),
    url('^cdns/delete/?$', cmdb_view.DeleteCDN, name="api_cdns_delete"),
    url('^domains/?$', cmdb_view.DomainList.as_view(), name="api_domains"),
    url('^domains/(?P<domain_uuid>[a-z0-9]+)/delete/?$', cmdb_view.DomainDelete.as_view(), name="api_domain_delete"),
    url('^resolver/?$', cmdb_view.ResolverView.as_view(), name="api_resolver"),
    url('^resolver/(?P<domain_id>[0-9]+)/(?P<record_id>[0-9]+)/delete/?$', cmdb_view.ResolverDelete, name="api_resolver_delete"),
    url('^resolver/audit/?$', cmdb_view.ResolverAuditList.as_view(), name="api_resolves"),

    # 审计
    url('^audit/(?P<resource_id>[a-z0-9]+)/logs/?$', core_view.AuditList.as_view(), name="api_audits"),

    # 节点
    url('^nodes/?$', app_view.NodesList.as_view(), name="api_nodes"),
    url('^search/nodes/?$', app_view.NodeSearch.as_view(), name="api_nodes_search"),

    # 统计报表
    url('^(?P<app_uuid>[a-z0-9]+)/widgets/?$', widget_view.WidgetList.as_view(), name="api_widgets"),
    url('^(?P<widget_id>[a-z0-9]+)/report/?$', widget_view.DataReport, name="api_report"),

    # 辅助API
    url('^getcabinet/?$', cmdb_view.cabinetInfo, name="api_cabinet_opt"),
]
