#coding:utf-8
from __future__ import absolute_import
import os
from datetime import timedelta
from celery import Celery
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surge.settings')
from django.conf import settings

celery = Celery('surge',
        broker=settings.BROKER_URL,
        backend='database',
        )

celery.conf.update(
        CELERY_DISABLE_RATE_LIMITS=True,
        CELERY_ENABLE_UTC=False,
        CELERY_TIMEZONE='Asia/Shanghai',
        CELERYBEAT_SCHEDULER='surge.schedulers.CustomDatabaseScheduler',
        CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
        CELERY_TASK_RESULT_EXPIRES=3600,
        CELERY_RESULT_PERSISTENT=True,
        CELERY_ACCEPT_CONTENT=['pickle', 'json', 'msgpack', 'yaml'],
        CELERY_DEFAULT_QUEUE='default',
        CELERY_QUEUES=(
            Queue('default'),
            Queue('Reciver', routing_key='reciver'),
            Queue('Senders', routing_key='senders'),
            Queue('Monitor', routing_key='monitor'),
        ),
        CELERY_DEFAULT_EXCHANGE='surge',
        CELERY_DEFAULT_EXCHANGE_TYPE='direct',
)

celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name='asynchronous')
