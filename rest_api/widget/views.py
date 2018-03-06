#coding:utf-8
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view

from surge.common.pagination import PagePagination

from asset import reports
from asset.models import (UserWidgets, Widgets)
from rest_api.widget.serializers import WidgetSerializer

class WidgetList(generics.ListAPIView):
    pagination_class = PagePagination
    serializer_class = WidgetSerializer

    def get_queryset(self):
        app_uuid = self.kwargs["app_uuid"]
        exclude = UserWidgets.objects.filter(user=self.request.user,\
                appid=app_uuid).values('widget')
        return Widgets.objects.exclude(id__in=[i["widget"] for i in exclude]).all()

@api_view(['GET'])
def DataReport(req, widget_id):
    try:
        uw = UserWidgets.objects.filter(user=req.user, widget_id=widget_id).first()
    except Exception,e:
        print e
        return Response({})
    data = getattr(reports, uw.widget.clsname)(req, uw.appid).get_data()
    series = {"title": uw.widget.name,
              "kind": uw.widget.get_kind_display(),
              "series": data,
              }
    return Response(series)
