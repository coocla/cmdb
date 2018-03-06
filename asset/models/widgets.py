#coding:utf-8
from django.db import models

class Widgets(models.Model):
    '''
    报表分析组件
    '''
    KIND = (
        (1, u"pie"),
        (2, u"line"),
        (3, u"column"),
        (4, u"block"),
    )

    name = models.CharField(u"组件名", max_length=128)
    clsname = models.CharField(u"数据生成类名", max_length=128)
    kind = models.IntegerField(u"图表种类", choices=KIND)
    params = models.CharField(u"预设参数", max_length=255)

    class Meta:
        app_label = "asset"


class UserWidgets(models.Model):
    '''
    用户添加的widget
    '''
    widget = models.ForeignKey(Widgets, verbose_name=u"组件")
    user = models.ForeignKey('surge.UserAccounts', verbose_name=u"用户")
    appid = models.CharField(u"所属应用", max_length=50)
    user_params = models.CharField(u"用户参数", max_length=255)

    class Meta:
        app_label = "asset"
        unique_together = (('widget', 'user', 'appid'),)
