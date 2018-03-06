#coding:utf-8
from django.db import models
from django.core.validators import MinValueValidator

from djcelery.models import PeriodicTask

from surge.common import utils

STATUS = (
   (1, u"未执行"),
   (2, u"正在执行"),
   (3, u"手动结束"),
   (4, u"执行失败"),
   (5, u"执行成功"),
   (6, u"步骤终止"),
   (7, u"执行超时"),
)


class Tasks(models.Model):
    TRIGGER = (
        (1, u"手动执行"),
        (2, u"计划任务"),
    )
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    user = models.CharField(u"发起人", max_length=100)
    name = models.CharField(u"作业名", max_length=100)
    user_id = models.CharField(u"用户ID", max_length=50)
    status = models.IntegerField(u"作业状态", choices=STATUS, default=1)
    start_at = models.DateTimeField(u"开始时间", default=utils.NOW)
    finish_at = models.DateTimeField(u"结束时间", blank=True, null=True)
    app_alias = models.CharField(u'应用别名',max_length=100)
    elapsed = models.CharField(u"总耗时", max_length=100, blank=True)
    inject_env = models.TextField(u"环境变量", blank=True)
    total = models.IntegerField(u"区服总数")
    timeout = models.IntegerField(u"超时时间", help_text=u"单个步骤的超时时间,单位:秒(s)", default=600)
    target_map = models.TextField(u"执行目标")

    app = models.ForeignKey('Apps', verbose_name=u"应用UUID")
    triggers = models.IntegerField(u"触发方式", choices=TRIGGER, default=1)
    async_id = models.CharField(u"异步ID", max_length=50, blank=True)
    stepid = models.PositiveIntegerField(u"当前步骤ID", validators=[MinValueValidator(1)])
    workflow = models.ForeignKey('WorkFlows', verbose_name=u"作业", related_name="tasks")

    class Meta:
        app_label = "operation"
        ordering = ['-start_at']

    def __unicode__(self):
        return self.name

class TaskSteps(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u'步骤名称', max_length=50)
    status = models.IntegerField(u"步骤状态", choices=STATUS)
    stepid = models.PositiveIntegerField(u"步骤ID", validators=[MinValueValidator(1)])

    app = models.ForeignKey('Apps', verbose_name=u"应用UUID")
    scriptflow = models.ForeignKey('ScriptFlow', verbose_name=u"步骤详情", related_name="tasksteps")
    task = models.ForeignKey(Tasks, verbose_name=u"所属作业", related_name="steps")

    class Meta:
        unique_together = (('stepid', 'task'))
        ordering = ['stepid']
        app_label = "operation"

    def __unicode__(self):
        return self.name

class TaskResults(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    remote_ip = models.CharField(u"通信IP", max_length=100)
    elapsed = models.CharField(u'耗时(s)', max_length=100)
    sid = models.CharField(u'区服ID', max_length=50)
    rc = models.IntegerField(u"退出码")
    stdout = models.TextField(u"标准输出")
    stderr = models.TextField(u"错误输出")
    plat_uuid =  models.CharField(u"平台UUID", max_length=50)

    taskstep = models.ForeignKey(TaskSteps, verbose_name=u"作业详情", related_name="results")
    app = models.ForeignKey('Apps', verbose_name=u"应用UUID")

    class Meta:
        app_label = "operation"
        ordering = ['remote_ip']

    def __unicode__(self):
        return "%s-s%s" % (self.remote_ip, self.sid)

class PeriodicTaskMeta(models.Model):
    periodictask = models.OneToOneField(PeriodicTask)

    userid = models.CharField(u'用户ID', max_length=50)
    user = models.CharField(u'创建人', max_length=100)
    app_uuid = models.CharField(u'应用UUID', max_length=50)
    appalias = models.CharField(u'应用名', max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    class Meta:
        app_label = "operation"

    def __unicode__(self):
        return self.periodictask.name
