#coding:utf-8
from django.db import models

from surge.common import utils
from operation.models import Apps, PlatForms


class IdcRegions(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    idc = models.CharField(u"IDC 厂商", max_length=255)
    idc_region = models.CharField(u"IDC 机房", max_length=255)
    idc_address = models.CharField(u"IDC 地址", max_length=255)
    idc_area = models.CharField(u"IDC 区域", max_length=100, default="中国大陆")
    remark = models.TextField(u"IDC 备注", blank=True)
    # 存储JSON, 分为租赁和托管
    cost = models.TextField(u"IDC费用", blank=True)

    class Meta:
        app_label = "asset"
        ordering = ['idc_region']

    def __unicode__(self):
        return self.idc_region

class IdcCabinets(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"IDC 机柜", max_length=255)
    idc = models.ForeignKey(IdcRegions, verbose_name=u"IDC 机房", related_name="cabinet")
    remark = models.CharField(u"机柜备注", max_length=255, blank=True)

    class Meta:
        app_label = "asset"
        ordering = ['name']

    def __unicode__(self):
        return self.name

class Divisions(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"事业部名", max_length=50)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "asset"
        ordering = ['name']

#class AssetGroups(models.Model):
#    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
#    name = models.CharField(u"组名", max_length=50)
#    operator = models.ManyToManyField("surge.UserAccounts", verbose_name=u"运维负责人", related_name="usergroup")
#    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)
#
#    class Meta:
#        app_label = "asset"
#
#    def __unicode__(self):
#        return self.name

class AppMode(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"应用类型", max_length=50)
    create_user = models.CharField(u"创建人", max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "asset"


class Assets(utils.AuditModel):
    STATUS = (
        (1, u"下架"),
        (2, u"录入"),
        (3, u"闲置"),
        (4, u"待用"),
        (5, u"在线"),
        (6, u"故障"),
    )
    SOURCE = (
        (1, u"购买"),
        (2, u"租赁"),
        (3, u"合作商提供"),
        (4, u"360"),
    )

    # Agent属性
    uuid = models.AutoField(u"客户端ID", primary_key=True, auto_created=True)
    agent_status = models.BooleanField(u"客户端状态", default=0, db_index=True)
    control = models.ForeignKey(u"operation.QueueNodes", verbose_name=u"控制服务器", related_name="host",blank=True, null=True, on_delete=models.SET_NULL)
    # 网络属性
    remote_ip = models.CharField(u"端点通信IP", max_length=100, blank=True)
    public_ip = models.CharField(u"公网IP", max_length=255)
    private_ip = models.CharField(u"私有IP", blank=True, max_length=255)
    virtual_ip = models.CharField(u"虚拟IP", blank=True, max_length=255)
    drac_ip = models.CharField(u"远控卡IP", blank=True, max_length=255)
    #ipv4 = models.TextField(u"所有的IP地址")
    uniq_id = models.CharField(u"唯一序号", max_length=128, unique=True)
    # 磁盘属性
    disk_number = models.IntegerField(u"磁盘个数", default=1)
    disk_capacity = models.CharField(u"磁盘容量/G", max_length=50)
    raid_type = models.CharField(u"Raid类型", blank=True, max_length=50)
    # 内存属性
    memory_capacity = models.CharField(u"内存容量/G", max_length=50)
    # CPU属性
    cpu_brand = models.CharField(u"CPU品牌", max_length=50, blank=True)
    cpu_core = models.CharField(u"CPU核数", max_length=50)
    # 固有属性
    serial_number = models.CharField(u"序列号", blank=True, max_length=50)
    asset_model = models.CharField(u"服务器型号", blank=True, max_length=50)
    asset_family = models.ForeignKey("self", verbose_name=u"宿主机", blank=True, null=True, default=None, to_field='uuid') # 宿主机
    # 系统属性
    os_family = models.CharField(u"操作系统版本", blank=True, max_length=50)
    # 逻辑属性
    #asset_group = models.ForeignKey(AssetGroups, verbose_name=u"服务器组", related_name="asset", blank=True, null=True)
    deleted = models.BooleanField(u"是否已删除", default=False)
    # 附加属性
    cost_person = models.CharField(u"成本担当人", max_length=255, blank=True)
    launch_date = models.DateTimeField(u"上架日期", default=utils.NOW, help_text=u"格式:YY-MM-DD hh:mm:ss")
    launch_person = models.CharField(u"上架人", max_length=50)
    source = models.IntegerField(u"服务器来源", choices=SOURCE, default=1)
    expire = models.BooleanField(u"是否过保", default=False)
    expire_date = models.DateTimeField(u"过保日期", help_text=u"格式:YY-MM-DD hh:mm:ss", default=utils.EXPIRE)
    status = models.IntegerField(u"服务器状态", choices=STATUS, default=2)
    purchase_cost = models.CharField(u"费用消耗", max_length=100, blank=True)
    contract = models.ForeignKey('asset.Contracts', verbose_name=u"合同编号", related_name="asset", blank=True, null=True, on_delete=models.SET_NULL)
    # IDC属性
    idc_location = models.ForeignKey(IdcRegions, verbose_name=u"IDC机房", related_name="asset", blank=True, null=True)
    idc_cabinet = models.ForeignKey(IdcCabinets, verbose_name=u"机柜", related_name="asset", blank=True, null=True)
    # 业务属性
    division = models.ForeignKey(Divisions, verbose_name=u"所属事业部", related_name="hosts", blank=True, null=True, on_delete=models.SET_NULL)
    app = models.ForeignKey(Apps, verbose_name=u"所属应用", related_name="hosts", blank=True, null=True, on_delete=models.SET_NULL)
    platform = models.ForeignKey(PlatForms, verbose_name=u"所属平台", related_name="hosts", blank=True, null=True, on_delete=models.SET_NULL)
    # 应用属性
    app_mode = models.ForeignKey(AppMode, verbose_name=u"应用类型", related_name="hosts", blank=True, null=True, on_delete=models.SET_NULL)
    app_detail = models.CharField(u"应用详情", max_length=255, blank=True)
    # 监控属性
    hostid = models.CharField(u"zabbix中hostid", max_length=255, blank=True)

    class Meta:
        app_label = "asset"
        ordering = ['remote_ip']
        unique_together = (('public_ip', 'private_ip'),)

    def __unicode__(self):
        return self.public_ip or self.private_ip

    @property
    def ipv4(self):
        return "_".join([self.public_ip, self.private_ip, self.virtual_ip])

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()
