#coding:utf-8
from django.apps import AppConfig

class SurgeConfig(AppConfig):
    name = 'surge'
    verbose_name = 'Surge Application'

    def ready(self):
        from asset import signals
