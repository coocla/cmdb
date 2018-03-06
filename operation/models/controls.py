#coding:utf-8
from django.db import models
from django.db.models import Count
from django.db.models.loading import get_model
from django.core.validators import MinValueValidator

from surge.common import utils

class QueueManager(models.Manager):
    def select_node(self, idc_uuid=None):
        if idc_uuid:
            nodes = self.get_queryset().all()
            for node in nodes:
                host = get_model('asset', 'Assets').objects.filter(uniq_id=node.uniq_id).first()
                if host and host.idc_location_id == idc_uuid:
                    return node
        return self.get_queryset().annotate(count=Count('host')).filter(count__lt=3000).first()

class QueueNodes(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True, default=utils.UUID)
    name = models.CharField(u"节点名字", max_length=50)
    rabbitmq_host = models.CharField(u"节点IP", max_length=255, help_text=u"请严格填写对应服务器的`remote_ip`字段")
    queue_username = models.CharField(u"消息用户", max_length=100)
    queue_password = models.CharField(u"消息密码", max_length=255)
    rabbitmq_ssl = models.BooleanField(u"是否使用ssl连接", default=False, help_text=u"请确保对应的rabbitmq server配置了ssl,并且可信任")
    rabbitmq_port = models.PositiveIntegerField(u"消息端口", validators=[MinValueValidator(1)])
    rabbitmq_vhost = models.CharField(u"虚拟主机", max_length=100)
    rabbitmq_down_exchange = models.CharField(u"下发交换机", max_length=100)
    rabbitmq_up_exchange = models.CharField(u"回传交换机", max_length=100)
    uniq_id = models.CharField(u"唯一序号", max_length=128, unique=True)
    create_user = models.CharField(u"创建人", max_length=100)
    created_at = models.DateTimeField(u"创建时间", default=utils.NOW)

    objects = QueueManager()

    class Meta:
        app_label = "operation"
        ordering = ['name']

    def __unicode__(self):
        return self.name

