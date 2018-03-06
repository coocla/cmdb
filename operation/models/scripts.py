#coding:utf-8
from django.db import models
from django.core.validators import MinValueValidator

from surge.common import utils

class Scripts(models.Model):
    '''
    脚本
    '''
    ScriptMode = (
        (1, u"私有脚本"),   #仅自己可以看到
        (2, u"公有脚本"),   #拥有命令查看和执行权限的用户都可以看到
    )
    ScriptStorage = (
        (1, u"数据库存储"),  #仅允许通过控制台进行修改
        (2, u"Git存储"),  #允许通过hook来更新脚本内容
    )
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"脚本名称", max_length=100)
    mode = models.IntegerField(u"脚本类型", choices=ScriptMode)
    storage = models.IntegerField(u"脚本存储", choices=ScriptStorage)
    content = models.TextField(u"脚本内容")
    userid = models.CharField(u"用户ID", max_length=100)
    create_user = models.CharField(u"创建人", max_length=100)
    app = models.ForeignKey('operation.Apps', verbose_name=u"所属应用", related_name="scripts")
    param = models.CharField(u"脚本参数", max_length=255, blank=True)

    class Meta:
        app_label = "operation"
        ordering = ['name']

    def __unicode__(self):
        return self.name


class WorkFlowManage(models.Manager):
    def next_step(self, uuid, stepid):
        stepid=int(stepid)
        try:
            nextstep = self.get_queryset().get(uuid=uuid)
        except:
            return None
        nextstep = nextstep.flow.filter(stepid__gt=stepid).order_by('stepid')
        if nextstep:
            return nextstep[0]
        return None

class WorkFlows(models.Model):
    '''
    脚本集
    
    其中包含脚本的执行流程, 流程中包含对应具体的脚本
    '''
    JobMode = (
        (1, u"私有作业"),   #仅自己可以看到
        (2, u"公有作业"),   #拥有命令查看和执行权限的用户都可以看到
    )

    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"作业名", max_length=100)
    mode = models.IntegerField(u"作业类型", choices=JobMode)
    app = models.ForeignKey('operation.Apps', verbose_name=u"所属应用", related_name="workflows")
    userid = models.CharField(u"用户ID", max_length=100)
    create_user = models.CharField(u"创建人", max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    objects = WorkFlowManage()

    class Meta:
        app_label = "operation"
        ordering = ['name']

    def __unicode__(self):
        return self.name

class ScriptFlow(models.Model):
    '''
    脚本流程

    包含流程的步骤ID, 流程参数, 流程控制等
    '''
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"步骤名称", max_length=100)
    stepid = models.PositiveIntegerField(u"步骤ID", validators=[MinValueValidator(1)])
    script = models.ForeignKey(Scripts, verbose_name=u"选择脚本", related_name="scriptflow", on_delete=models.CASCADE)
    on_error_pause = models.BooleanField(u"当失败时,是否暂停", default=True)
    workflow = models.ForeignKey(WorkFlows, verbose_name=u"步骤", related_name="flow", on_delete=models.CASCADE)

    class Meta:
        app_label = "operation"
        unique_together = (('workflow', 'stepid'))
        ordering = ['name']

    def __unicode__(self):
        return self.name
