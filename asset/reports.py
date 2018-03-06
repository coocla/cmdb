#coding:utf-8
from django.db.models import Sum, Avg, Count, ForeignKey
from django.db.models.loading import get_model

def get_model_field(model, name):
    return model._meta.get_field(name)

def get_lookup_value(model, field, value, relation_map):
    real_field = field.split("__")[0]
    try:
        field_obj = get_model_field(model, real_field)
        rel_model = field_obj.rel.to
        return getattr(rel_model.objects.get(pk=value), relation_map[field])
    except:
        return value

class PlatFormCount(object):
    '''
    所属应用的平台总数
    '''
    def __init__(self, req, appid):
        if req.user.is_admin:
            self.base = get_model('operation', 'Apps').objects.get(pk=appid)
        else:
            role = req.user.roles.get(app_id=appid)
            if role.staff:
                self.base = get_model('operation', 'Apps').objects.get(pk=appid)
            else:
                self.base = role.app

    def get_data(self):
        return self.base.platforms.count()

class ZoneCount(object):
    '''
    所属应用的区服总数
    '''
    def __init__(self, req, appid):
        self.appid = appid
        self.allow = False

        if req.user.is_admin:
            self.allow = True
        else:
            role = req.user.roles.get(app_id=appid)
            if role.staff:
                self.allow = True
            else:
                self.base = [i[0] for i in role.app.platforms.values_list('uuid')]

    def get_data(self):
        model = get_model('operation', 'Zones')
        if self.allow:
            return model.objects.filter(app_uuid=self.appid).count()
        return model.objects.filter(app_uuid=self.appid).filter(\
                plat_uuid__in=self.base).count()

class InstanceCount(object):
    '''
    服务器总数
    '''
    def __init__(self, req, appid=None, user_params=None):
        self.appid = appid
        self.allow = False
        self.model = get_model('asset', 'Assets')

        if req.user.is_admin:
            self.base = self.model.objects.all()
        else:
            if appid:
                role = req.user.roles.get(app_id=appid)
                if role.staff:
                    self.base = self.model.objects.all()
                else:
                    self.base = model.objects.filter(app_id=appid)
            else:
                self.base = model.objects.filter(app_id__in=req.user.owner_app())
        if user_params:
            self.base = self.base.filter(**user_params)

    def get_data(self):
        return self.base.count()

class InstanceStatusAnaly(InstanceCount):
    '''
    服务指标占比::
    #1. 状态的占比
    '''
    def __init__(self, *args, **kwargs):
        super(InstanceStatusAnaly, self).__init__(*args, **kwargs)
        self.annotate = (("uuid", Count),)
        self.group_by = ["status"]
        self.choices = ("status")       #需要显示choices值的字段
        self.display = ()               #需要显示verbose_name值的字段
        self.relation_map = {}          #定义需要显示的外键关联后所取的relation_model的字段
        self.results = []

    def get_data(self):
        self.get_annotate()
        return self.results

    def get_annotate(self):
        annotate_args = {}
        for field, func in self.annotate:
            annotate_args[field] = func(field)

        values = [i.split("__")[0] for i in self.group_by]
        rows = self.base.values(*values).annotate(**annotate_args).order_by(values[0])
        for row in rows:
            count_cols = 0
            for col in self.group_by:
                if count_cols == 0:
                    row_vals = [self.get_value_display(row, col)]
                else:
                    row_vals.append(self.get_value_display(row, col))
                count_cols += 1
            for field, func in self.annotate:
                row_vals.append(row[field])
            self.results.append(row_vals)

    def get_value_display(self, data, field):
        if '__' in field:
            real_field = field.split("__")[0]
        else:
            real_field = field

        value = data[real_field]
        if value is None:
            return u"闲置池"
        field_obj = self.get_field(real_field)
        if field in self.choices:
            value = [display for val, display in field_obj.choices if val == value][0]
        if field in self.display:
            value = field_obj.verbose_name
        if isinstance(field_obj, ForeignKey):
            value = get_lookup_value(self.model, field, value, self.relation_map)
        return value

    def get_field(self, name):
        return get_model_field(self.model, name)

class InstanceAppAnaly(InstanceStatusAnaly):
    def __init__(self, *args, **kwargs):
        super(InstanceAppAnaly, self).__init__(*args, **kwargs)
        self.annotate = (("uuid", Count),)
        self.group_by = ["app__uuid"]
        self.choices = ()
        self.display = ()
        self.relation_map = {"app__uuid": "appalias"}
        self.results = []

class InstancePlatAnaly(InstanceStatusAnaly):
    def __init__(self, *args, **kwargs):
        super(InstancePlatAnaly, self).__init__(*args, **kwargs)
        self.annotate = (("uuid", Count),)
        self.group_by = ["platform__uuid"]
        self.choices = ()
        self.display = ()
        self.relation_map = {"platform__uuid": "platalias"}
        self.results = []

class InstanceDivisionAnaly(InstanceStatusAnaly):
    def __init__(self, *args, **kwargs):
        super(InstanceDivisionAnaly, self).__init__(*args, **kwargs)
        self.annotate = (("uuid", Count),)
        self.group_by = ["division__uuid"]
        self.choices = ()
        self.display = ()
        self.relation_map = {"division__uuid": "name"}
        self.results = []

class InstanceIDCAnaly(InstanceStatusAnaly):
    def __init__(self, *args, **kwargs):
        super(InstanceIDCAnaly, self).__init__(*args, **kwargs)
        self.annotate = (("uuid", Count),)
        self.group_by = ["idc_location__uuid"]
        self.choices = ()
        self.display = ()
        self.relation_map = {"idc_location__uuid": "idc"}
        self.results = []

class InstanceSourceAnaly(InstanceStatusAnaly):
    def __init__(self, *args, **kwargs):
        super(InstanceSourceAnaly, self).__init__(*args, **kwargs)
        self.annotate = (("uuid", Count),)
        self.group_by = ["source"]
        self.choices = ("source")
        self.display = ()
        self.relation_map = {}
        self.results = []
