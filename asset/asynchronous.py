#coding:utf-8
import os
import time
import json
import requests
from django.conf import settings
from celery.task.schedules import crontab
from celery.decorators import periodic_task

from ansible import utils
from ansible import callbacks
from ansible.playbook import PlayBook

from surge.celery import celery
from surge.models import UserAccounts

from asset.models import Assets

from operation.models import QueueNodes

basedir = os.path.join(os.path.dirname(__file__), '..')

@celery.task(name="BulkInputHost", ignore_result=True)
def BulkInputHost(userid, data):
    '''
    :param data: [(host, ansible_vars)]
    '''
    user = UserAccounts.objects.get(pk=userid)

    stats = callbacks.AggregateStats()
    callback = callbacks.PlaybookCallbacks()
    runner_callbacks = callbacks.PlaybookRunnerCallbacks(stats)
    runtime_env={"master_url":settings.DOMAIN, "key":user.apikey}
    for host, extra_vars in data:
        runtime_env["idc_uuid"] = extra_vars["idc_uuid"]
        extra_vars.update({"host":host,'basedir':basedir,"runtime_env":runtime_env})
        pb = PlayBook(host_list=[host], playbook='../ansible/playbooks/instance_input.yaml', \
                extra_vars=extra_vars, stats=stats, callbacks=callback, runner_callbacks=runner_callbacks)
        pb.run()


@celery.task(name="InstallAgent", ignore_result=True)
def InstallAgent(userid, data):
    pass



@periodic_task(name='UpdateAgentStatus', run_every=crontab(minute="*/5"))
def PeriodUpdateAgentStatus():
    for node in QueueNodes.objects.all():
        api = "http://%s:15672/api/connections?columns=peer_host" % node.rabbitmq_host
        try:
            current_connections = requests.get(api, auth=(node.queue_username, node.queue_password), \
                    headers={"Content-Type":"application/json"}).json()
        except:
            continue
        normal = [peer['peer_host'] for peer in current_connections if current_connections.count(peer) >= 2]
        for host in Assets.objects.filter(control=node).all():
            if host.public_ip.split(",")[0] not in normal:
                host.agent_status == False
                host.save(update_fields=['agent_status'])
            else:
                if not host.agent_status:
                    host.agent_status = True
                    host.save(update_fields=['agent_status'])
