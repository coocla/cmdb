#coding:utf-8
from rest_framework import serializers

from asset.models import Widgets

from rest_api.serializer import HyperLinkField

class WidgetSerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()
    url = HyperLinkField(view_name="api_report",
                         read_only=True,
                         lookup_mapping={
                             "widget_id": "self",
                         })
    class Meta:
        model = Widgets
        fields = ('id', 'name', 'kind', 'url')

    def get_kind(self, obj):
        return obj.get_kind_display()
