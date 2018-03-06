#coding:utf-8
import json
import inspect

from django.db.models.signals import (post_save, post_delete)
from django.dispatch import receiver

from surge.common import utils
from asset.models import (CDNCompany, AccelerateCDN, Assets, Contracts, RegisterDomain, Audit)
from operation.models import Zones

@receiver(post_save, sender=Assets)
@receiver(post_delete, sender=Assets)
@receiver(post_save, sender=Contracts)
@receiver(post_delete, sender=Contracts)
@receiver(post_save, sender=CDNCompany)
@receiver(post_delete, sender=CDNCompany)
@receiver(post_save, sender=AccelerateCDN)
@receiver(post_delete, sender=AccelerateCDN)
@receiver(post_save, sender=RegisterDomain)
@receiver(post_delete, sender=RegisterDomain)
def operation_audit(sender, **kwargs):
    instance = kwargs["instance"]
    init_value = instance.init_value
    final_values = instance.final_values
    pk = instance.pk

    for frame_record in inspect.stack():
        if frame_record[3] == "get_response":
            request  = frame_record[0].f_locals['request']
            user = request.user.name
            break
    else:
        # 不记录没有用户的
        return
        
    for field, value in final_values.items():
        if value == init_value[field]:
            final_values.pop(field)
            init_value.pop(field)

    Audit.objects.create(user=user, before=json.dumps(init_value, cls=utils.ComplexEncoder), \
            after=json.dumps(final_values, cls=utils.ComplexEncoder), resource_id=pk, \
            resource_type="%s.%s" % (instance._meta.app_label, instance._meta.object_name), \
            action=instance.action)


@receiver(post_save, sender=Assets)
@receiver(post_delete, sender=Assets)
def link_update(sender, **kwargs):
    instance = kwargs["instance"]
    if "app_detail" in instance.final_values:
        if not (instance.app and instance.app.online):
            # 有所属应用且应用已上线
            return
        if not instance.platform:
            # 有所属平台
            return
        if not instance.app_detail:
            Zones.objects.filter(host=instance).delete()
            if instance.status != 4:
                instance.status = 4
                instance.save(update_fields=['status'])
            return
        persent = {}
        for _z in Zones.objects.filter(host=instance).all():
            persent[_z.uuid] = _z

        for detail in instance.app_detail.split(","):
            if "-" in detail:
                try:
                    sid = int(detail.split("-")[0])
                    alias = detail
                except:
                    continue
            else:
                try:
                    sid = int(detail)
                    alias = detail
                except:
                    continue
            try:
                zone = Zones.objects.get(app_uuid=instance.app_id, plat_uuid=instance.platform_id, sid=sid)
                if zone.alias != alias:
                    zone.alias = alias
                    zone.save(update_fileds=['alias'])
                persent.pop(zone.uuid)
            except:
                zone = Zones(sid=sid, alias=alias, app_uuid=instance.app_id, plat_uuid=instance.platform_id, host=instance)
                zone.save()

        for _z in persent.values():
            _z.delete()

        if instance.status != 5:
            instance.status = 5
            instance.save(update_fields=['status'])
