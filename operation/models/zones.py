#coding:utf-8
from django.db import models
from django.db.models import Max, Q
from django.forms.models import model_to_dict

from surge.common import utils

class ZoneManager(models.Manager):
    def max_sid(self, app_uuid, plat_uuid):
        return self.get_queryset().filter(app_uuid=app_uuid, \
                plat_uuid=plat_uuid).aggregate(Max('sid'))["sid__max"]

    def role_scope(self, role):
        scope = []
        for vdc in role.idrange.split(","):
            if not vdc:
                continue
            if "-" in vdc:
                ph = vdc.split("-")
                try:
                    _start = int(ph[0])
                    _stop = int(ph[-1])
                except:
                    continue
                scope.append(Q(sid__gte=_start, sid__lte=_stop))
            else:
                try:
                    vdc = int(vdc)
                except:
                    continue
                scope.append(Q(sid==vdc))
        return scope

    def filter_zones(self, user, query, role, plat_uuid=None, group_uuid=None):
        if plat_uuid:
            try:
                if role.staff != 1:
                    platform = role.platforms.get(pk=plat_uuid)
                query = query.filter(plat_uuid=plat_uuid)
            except:
                # 返回一个空的queryset
                return query.filter(sid__lt=0)
        if group_uuid:
            try:
                group =  user.groups.get(pk=group_uuid)
                query = query.filter(plat_uuid__in=group.platforms.all())
            except:
                # 返回一个空的queryset
                return query.filter(sid__lt=0)
        return query


    def safe_range(self, user, app_uuid, zone_uuid, plat_uuid=None, group_uuid=None):
        query = self.get_queryset().filter(app_uuid=app_uuid)
        if user.is_admin: return True
        try:
            role = user.roles.get(app_id=app_uuid)
        except:
            return False
        if not role.idrange: return True
        scope = self.role_scope(role)
        query = self.filter_zones(user, query, role, plat_uuid=plat_uuid, group_uuid=group_uuid)
        if scope:
            query = query.filter("|".join(scope))
        if zone_uuid == '__all__':
            if query.count() > 0:
                return True
            return False
        if query.filter(pk__in=zone_uuid).count() != len(zone_uuid):
            return False
        return True

    def safe_select(self, user, app_uuid, plat_uuid=None, group_uuid=None):
        query = self.get_queryset().filter(app_uuid=app_uuid)
        if user.is_admin:
            if plat_uuid:
                query = query.filter(plat_uuid=plat_uuid)
            if group_uuid:
                group =  user.groups.get(pk=group_uuid)
                query = query.filter(plat_uuid__in=group.platforms.all())
            return query.all()
        try:
            role = user.roles.get(app_id=app_uuid)
        except:
            return []
        query = self.filter_zones(user, query, role, plat_uuid=plat_uuid, group_uuid=group_uuid)
        scope = self.role_scope(role)
        if scope:
            query = query.filter("|".join(scope))
        return query.all()

    def exist_zone(self, app_uuid, plat_uuid, zones):
        return self.get_queryset().filter(app_uuid=app_uuid, plat_uuid=plat_uuid, sid__in=zones).count()



class Zones(models.Model):
    uuid = models.AutoField(primary_key=True, auto_created=True)
    sid = models.IntegerField(u'区服ID')
    alias = models.CharField(u'区服显示', max_length=100)
    app_uuid = models.CharField(u'应用ID', max_length=50)
    plat_uuid = models.CharField(u'平台ID', max_length=50)
    host = models.ForeignKey('asset.Assets', verbose_name=u"所属服务器", related_name="zones")
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    objects = ZoneManager()

    class Meta:
        ordering = ['sid']

    def contain(self, sid):
        _c = map(int, self.alias.split('-'))
        return sid > max(_c)
