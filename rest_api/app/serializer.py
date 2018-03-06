#coding:utf-8
import json
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from rest_api.serializer import HyperLinkField

from asset.models import Assets

from operation.models import (Scripts, WorkFlows, PlatForms, Zones, \
        Tasks, TaskSteps, TaskResults, PeriodicTaskMeta, QueueNodes)


class ScriptSerializer(serializers.ModelSerializer):
    mode = serializers.SerializerMethodField()
    url = HyperLinkField(view_name='script_update', read_only=True,
            lookup_mapping={"app_uuid": "app", "script_uuid": "self"})

    class Meta:
        model = Scripts
        fields = ('uuid', 'name', 'mode', 'userid', 'create_user', 'app', 'param', 'url')

    def get_mode(self, obj):
        return obj.get_mode_display()

class WorkFlowSerializer(serializers.ModelSerializer):
    mode = serializers.SerializerMethodField()
    flow = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    url = HyperLinkField(view_name='workflow_update', read_only=True,
            lookup_mapping={"app_uuid": "app", "workflow_uuid": "self"})

    class Meta:
        model = WorkFlows
        fields = ('uuid', 'name', 'mode', 'create_user', 'created_at', 'url', 'flow')

    def get_mode(self, obj):
        return obj.get_mode_display()

class _HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = ('uuid', 'remote_ip', 'public_ip')

class ZoneSerializer(serializers.ModelSerializer):
    server = _HostSerializer(source='host')

    class Meta:
        model = Zones
        fields = ('uuid', 'sid', 'alias', 'server')

class TaskSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    url = HyperLinkField(view_name='api_taskstep', read_only=True,
            lookup_mapping={"app_uuid": "app", "task_uuid": "self"})
    triggers = serializers.SerializerMethodField()

    class Meta:
        model = Tasks
        fields = ('uuid', 'user', 'progress', 'status', 'app_alias', 'triggers', 'url', 'start_at', 'finish_at', 'name')

    def get_progress(self, obj):
        return obj.get_status_display()

    def get_triggers(self, obj):
        return obj.get_triggers_display()

class TaskStepSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    url = HyperLinkField(view_name='api_taskstep_result', read_only=True,
            lookup_mapping={"app_uuid": "app", "task_uuid": "task", "step_uuid": "self"})

    class Meta:
        model = TaskSteps
        fields = ('uuid', 'name', 'state', 'status', 'stepid', 'url')

    def get_state(self, obj):
        return obj.get_status_display()

class TaskResultSerializer(serializers.ModelSerializer):
    url = HyperLinkField(view_name='api_taskresult_detail', read_only=True,
            lookup_mapping={"app_uuid": "app", "result_uuid": "self"})

    class Meta:
        model = TaskResults
        fields = ('uuid', 'sid', 'remote_ip', 'elapsed', 'rc', 'url')

class TaskResultDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskResults

class JSONField(serializers.Field):
    def to_internal_value(self, obj):
        return json.dumps(obj)

    def to_representation(self, value):
        try:
            val = json.loads(value)
        except TypeError:
            raise serializers.ValidationError(
                    "Could not load json <{}>".format(value)
            )
        return val

class ExecuteWorkFlowSerializer(serializers.Serializer):
    workflow_uuid = serializers.CharField()
    uuids = serializers.CharField(required=True)
    timeout = serializers.IntegerField(min_value=1, default=600)
    inject_env = JSONField(required=False)
    cronExpression = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    kind = serializers.CharField(required=True)
    region = serializers.CharField(required=False)

    def validate_kind(self, value):
        if value not in ["zone", "host"]:
            raise serializers.ValidationError(_(u"非法的kind!"))
        return value

    def validate_cronExpression(self, value):
        data = {}
        value = value.split(",")
        if value:
            if len(value) != 4:
                raise serializers.ValidationError(_(u"非法的定时表达式!"))
            data["minute"] = value[0]
            data["hour"] = value[1]
            data["day_of_month"] = value[2]
            data["month_of_year"] = value[3]
        return data

    def validate_uuids(self, value):
        if value == '__all__':
            return value
        value = value.split(",")
        try:
            value = map(int, value)
        except:
            raise serializers.ValidationError(_(u"非法的参数格式uuids"))
        return value


class ModifyZoneSerializer(serializers.Serializer):
    host = serializers.CharField()
    sid = serializers.CharField()

    def validate_host(self, value):
        try:
            Assets.objects.get(pk=value, status__in=('3','4','5'))
        except:
            raise serializers.ValidationError(_(u"服务器不存在或当前状态不可操作"))
        return value

    def validate_sid(self, value):
        try:
            value = [i for i in value.split(",") if i]
            return map(int, value)
        except:
            raise serializers.ValidationError(_(u"非法的区服ID"))

class CronField(serializers.Field):
    def to_representation(self, obj):
        return "%s-%s %s:%s" % (obj.month_of_year, obj.day_of_month, obj.hour, obj.minute)

class CronJobSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='periodictask.name')
    crontab = CronField(source='periodictask.crontab')
    last_run_at = serializers.CharField(source='periodictask.last_run_at')

    class Meta:
        model = PeriodicTaskMeta
        exclude = ('periodictask',)

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueNodes
        exclude = ('queue_username', 'queue_password')
