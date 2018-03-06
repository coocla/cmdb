#coding:utf-8
from rest_framework import serializers

from surge.common import utils

from asset import dnspod
from asset.models import *

from operation.models import Zones, QueueNodes

class ForeignField(serializers.RelatedField):
    def __init__(self, *args, **kwargs):
        self.rel_field = kwargs.pop("rel_field", None)
        super(ForeignField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        if self.rel_field:
            return getattr(value, self.rel_field)
        return value


class BulkSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Assets
        exclude = ('uuid', 'agent_status', 'hostid', 'remote_ip', 'public_ip', \
                'private_ip', 'virtual_ip', 'drac_ip', 'uniq_id', 'deleted')

class HostSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    app_mode = ForeignField(read_only=True, rel_field="name")
    app = ForeignField(read_only=True, rel_field="appalias")
    platform = ForeignField(read_only=True, rel_field="platname")
    division = ForeignField(read_only=True, rel_field="name")

    class Meta:
        model = Assets

    def get_source(self, obj):
        return obj.get_source_display()

    def get_status(self, obj):
        return obj.get_status_display()

class _ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zones
        fields = ('alias',)

class OpsHostSerializer(serializers.ModelSerializer):
    zones = _ZoneSerializer(many=True, read_only=True)
    states = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    class Meta:
        model = Assets
        fields = ('uuid', 'agent_status', 'remote_ip', 'public_ip', 'disk_capacity', 'memory_capacity', \
                'cpu_core', 'os_family', 'expire', 'states', 'status', 'app_mode', 'source', 'zones')

    def get_states(self, obj):
        return obj.get_status_display()

    def get_source(self, obj):
        return obj.get_source_display()

class HostCreateSerializer(serializers.Serializer):
    public_ip = serializers.CharField()
    private_ip = serializers.CharField(required=False, allow_blank=True)
    disk_number = serializers.IntegerField(required=False)
    disk_capacity = serializers.CharField()
    memory_capacity = serializers.CharField()
    cpu_core = serializers.CharField()
    idc_location_id = serializers.CharField(required=False)
    
    def validate(self, data):
        request = self.context.get("request", None)
        data["launch_person"] = request.user.name
        data["remote_ip"] = data["public_ip"].split(",")[0]
        if data.get("idc_location_id", None):
            data["control"] = QueueNodes.objects.select_node(data["idc_location_id"])
        data["uniq_id"] = utils.uniq_id(data["public_ip"], data.get("private_ip", ""))
        return data

    def validate_public_ip(self, value):
        data = [i for i in value.split(",") if i]
        return ",".join(data)

    def validate_idc_location_id(self, value):
        if not IdcRegions.objects.filter(pk=value).first():
            raise serializers.ValidationError(u"该机房不存在!")
        return value

    def create(self, validate_data):
        uniq_id = utils.uniq_id(validate_data["public_ip"], validate_data["private_ip"])
        instance = Assets.objects.filter(uniq_id=uniq_id).first()
        if instance:
            return u"该服务器已经存在!"
        return Assets.objects.create(**validate_data)


class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Divisions

class IdcRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdcRegions

class IdcCabinetSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdcCabinets

class AppModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppMode

class AccelerateSerializer(serializers.ModelSerializer):
    app = ForeignField(read_only=True, rel_field="appalias")
    company = ForeignField(read_only=True, rel_field="name")
    division = ForeignField(read_only=True, rel_field="name")

    class Meta:
        model = AccelerateCDN

class CDNSerializer(serializers.ModelSerializer):
    class Meta:
        model = CDNCompany

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contracts

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisterDomain

class ResolverSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResolveAudit

class ResolverTempSerializer(serializers.Serializer):
    record = serializers.CharField()
    value = serializers.CharField()
    record_type = serializers.ChoiceField(choices=dnspod.TYPE, default='A')
    record_line = serializers.ChoiceField(choices=dnspod.LINE, default=u'默认')

    def validate(self, data):
        if data["record_type"] == "CNAME":
            if not data["value"].endswith("."):
                raise serializers.ValidationError(u"CNAME格式错误!")
        else:
            if data["value"].count(",") != 1:
                raise serializers.ValidationError(u"解析地址格式错误!")
            data["value"] = data["value"].split(",")
        if data["record"].count(".") < 2:
            raise serializers.ValidationError(u"域名格式错误!")
        data["sub_domain"] = ".".join(data["record"].split(".")[:-2])
        data["domain"] = ".".join(data["record"].split(".")[-2:])
        return data
