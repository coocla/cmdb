#coding:utf-8
import os
import json
import uuid
import random
import hashlib
import datetime

from django.db.models.base import Model
from django.core.serializers.json import Serializer
from django.utils.deconstruct import deconstructible

REDIS_USER_TOKEN = "USER:%s"      # USER:UID
REDIS_REGION = "REGION:%s:%s:%s"  # REGION:UID:APPID:REGION_ID
REDIS_REGION_RE = "REGION:%s:%s:*"

def UUID():
    """
    随机生成一个32位长度的id
    """
    _uuid = uuid.uuid1(node=random.randint(1, 999999999999))
    return _uuid.hex

def NOW():
    return datetime.datetime.now()

def EXPIRE():
    return datetime.datetime.now() + datetime.timedelta(days=3*365)

def uniq_id(public_ip, private_ip):
    ipv4 = [i for i in ",".join([public_ip, private_ip]).split(",") if i]
    return hashlib.md5(",".join(set(ipv4))).hexdigest()

def make_password(raw, salt="QXb.zd231"):
    return hashlib.md5('%s@%s' % (raw, salt)).hexdigest()

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return int(obj)
        else:    
            return json.JSONEncoder.default(self, obj)

class Free(object):
    def __init__(self):
        self.uuid = None

    def __getattr__(self, name):
        return u"闲置池"

@deconstructible
class upload_rule(object):
    def __init__(self, path):
        self.path = path
    def __call__(self, instance, filename):
        return os.path.join(self.path, UUID()+".png")

class MySerialize(Serializer):
    def start_serialization(self):
        self._count = self.options.pop("count", 0)
        self.stream.write('{"count":%d,"data":' % self._count)
        super(MySerialize, self).start_serialization()

    def end_serialization(self):
        super(MySerialize, self).end_serialization()
        self.stream.write('}')

    def get_dump_object(self, obj):
        self._current.update({"id": obj.pk})
        return self._current

def serialize(queryset, **options):
    s = MySerialize()
    s.serialize(queryset, **options)
    return s.getvalue()

class AuditModel(Model):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self.init_value = {}
        self.final_values = {}
        self.action = 1
        super(AuditModel, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        empty_values = False

        if not hasattr(self, "audit_fields"):
            self.audit_fields = [f.name for f in self._meta.fields]

        if self.pk is None:
            empty_values = True
        else:
            self.action = 2
            try:
                self.init_value = self.__class__.objects.filter(pk=self.pk).\
                        values(*self.audit_fields)[0]
            except IndexError:
                empty_values = True

        if empty_values:
            for field in self.audit_fields:
                self.init_value[field] = ""

        for field in self.audit_fields:
            field_inst = self._meta.get_field_by_name(field)[0]
            self.final_values[field] = field_inst.to_python(field_inst
                    .value_from_object(self))

        super(AuditModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        initial_values, final_values = {}, dict(audit_is_delete=True)
        for field in self.audit_fields:
            final_values[field] = getattr(self, field)
        self.action = 3
        super(AuditModel, self).delete(*args, **kwargs)
