#coding:utf-8
from django.conf.urls import patterns, url
from asset.views import hosts as host_view
from asset.views import idcs as idc_view
from asset.views import accelerate as cdn_view

urlpatterns = patterns('asset.views',
    url(r'^hosts/create/?$', host_view.HostCreate.as_view(), name='host_create'),
    url(r'^hosts/bulk/update/?$', host_view.HostBulkUpdate.as_view(), name='host_bulk_update'),
    url(r'^hosts/bulk/monitor/?$', host_view.HostBulkMonitor.as_view(), name='host_bulk_monitor'),
    url(r'^hosts/(?P<host_uuid>[0-9]+)/update/?$', host_view.HostUpdate.as_view(), name='host_update'),
    url(r'^hosts/(?P<host_uuid>[0-9]+)/agentdata/?$', host_view.HostAgentData.as_view(), name='host_agentdata'),
    url(r'^hosts/example/?$', host_view.HostInputDownload.as_view(), name='host_input_download'),
    url(r'^hosts/bulk/input/?$', host_view.HostBulkInput.as_view(), name='host_bulk_input'),
    url(r'^hosts/(?P<idc_uuid>[a-z0-9]+)/input/?$', host_view.HostInput.as_view(), name='host_input'),

    # IDC
    url(r'^idc/create/?$', idc_view.IDCCreate.as_view(), name='idc_create'),
    url(r'^idc/(?P<idc_uuid>[a-z0-9]+)/update/?$', idc_view.IDCUpdate.as_view(), name='idc_update'),

    # 机柜
    url(r'^cabinet/create/?$', idc_view.CabinetCreate.as_view(), name='cabinet_create'),
    url(r'^cabinet/(?P<cabinet_uuid>[a-z0-9]+)/update/?$', idc_view.CabinetUpdate.as_view(), name='cabinet_update'),

    # 合同
    url(r'^contract/create/?$', host_view.ContractCreate.as_view(), name='contract_create'),
    url(r'^contract/(?P<contract_uuid>[a-z0-9]+)/update/?$', host_view.ContractUpdate.as_view(), name='contract_update'),

    # 事业部
    url(r'^division/create/?$', host_view.DivisionCreate.as_view(), name='division_create'),
    url(r'^division/(?P<division_uuid>[a-z0-9]+)/update/?$', host_view.DivisionUpdate.as_view(), name='division_update'),

    # 主机组
    #url(r'^hostgroup/create/?$', host_view.HostGroupCreate.as_view(), name='hostgroup_create'),
    #url(r'^hostgroup/(?P<group_uuid>[a-z0-9]+)/update/?$', host_view.HostGroupUpdate.as_view(), name='hostgroup_update'),

    # CDN
    url(r'^cdn/create/?$', cdn_view.CDNCompanyCreate.as_view(), name='cdncompany_create'),
    url(r'^cdn/(?P<cdn_uuid>[a-z0-9]+)/update/?$', cdn_view.CDNCompanyUpdate.as_view(), name='cdncompany_update'),
    url(r'^accelerate/create/?$', cdn_view.AccelerateCreate.as_view(), name='accelerate_create'),
    url(r'^accelerate/(?P<accelerate_uuid>[a-z0-9]+)/update/?$', cdn_view.AccelerateUpdate.as_view(), name='accelerate_update'),

    # 域名
    url(r'domain/create/?$', cdn_view.DomainCreate.as_view(), name='domain_create'),
    url(r'domain/(?P<domain_uuid>[a-z0-9]+)/update/?$', cdn_view.DomainUpdate.as_view(), name='domain_update'),
    url(r'resolver/?$', cdn_view.ResolverList.as_view(), name='resolver_list'),
    url(r'resolver/create/?$', cdn_view.ResolverCreate.as_view(), name='resolver_create'),
    url(r'resolver/(?P<domain>[a-z]+)/(?P<record_id>[0-9]+)/update/?$', cdn_view.ResolverUpdate.as_view(), name='resolver_update'),
)
