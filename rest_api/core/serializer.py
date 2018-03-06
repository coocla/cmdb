#coding:utf-8
import json

from rest_framework import serializers
from django.db.models.loading import get_model

from asset.models import Audit
from operation.models import (Apps, PlatForms)

class JSONField(serializers.Field):
    def __init__(self, *args, **kwargs):
        self.load_model = {}
        super(JSONField, self).__init__(*args, **kwargs)

    def to_internal_value(self, obj):
        print obj
        return json.dumps(obj)

    def to_representation(self, value):
        model = self.root.instance[0].resource_type
        if model not in self.load_model:
            model_class = get_model(model)
            self.load_model[model] = model_class
        else:
            model_class = self.load_model[model]

        try:
            val = json.loads(value)
        except TypeError:
            raise serializers.ValidationError(
                    "Could not load json <{}>".format(value)
            )
        data = {}
        for field_name in val:
            field = model_class._meta.get_field(field_name)
            data[field.verbose_name] = val[field_name]
        return data

class AppSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField(read_only=True)
    class Meta:
        model = Apps

class PlatFormSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField(read_only=True)
    class Meta:
        model = PlatForms

class AuditSerializer(serializers.ModelSerializer):
    before = JSONField()
    after = JSONField()
    action = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        exclude = ('uuid', 'resource_type')

    def get_action(self, obj):
        return obj.get_action_display()
