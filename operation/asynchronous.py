#coding:utf-8
import time
import json
import logging
import datetime

from billiard import current_process
from celery import group
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.signals import worker_process_init, worker_process_shutdown

from django.db.models import Max
from django.core.cache import cache
from django_redis import get_redis_connection
from django.forms import model_to_dict
from django.db.models.loading import get_model
from djcelery.models import PeriodicTask

from surge.celery import celery
from surge.common import utils
from surge.common.Event import Event
from surge.common.Event import EventModel
from surge.models import UserAccounts

from asset.models import Assets
from asset.pyzabbix import Zabbix

from operation.endpoints import Control
from operation.models import Zones, Tasks, TaskSteps, TaskResults, WorkFlows, Apps
logger = logging.getLogger(__name__)

LOCK_EXPIRE = 10
channel = get_redis_connection('default')

def unicast(userid, msg, success):
    channel.publish('TASK.NOTIFICATION', json.dumps({"userid": userid, "success": success, "msg": msg, "time": datetime.datetime.now().strftime('%H:%M:%S')}))

@worker_process_init.connect
def init_worker_process(**kwargs):
    global proxy
    proxy = Control()

@worker_process_shutdown.connect
def shutdown_worker_process(**kwargs):
    global proxy
    for flag, node in proxy.Nodes.iteritems():
        node.stop()

def format_env(model_obj):
    if isinstance(model_obj, Zones):
        env = model_to_dict(model_obj, exclude=['created_at'])
        model_obj = model_obj.host
        env.update({"channel": "Zones"})
    else:
        env = {"channel": "Assets", "uuid": model_obj.uuid}
    env.update({"platid": model_obj.platform.platid, "platname": model_obj.platform.platname, "remote_ip": model_obj.remote_ip,
        "appid": model_obj.app.appid, "appname": model_obj.app.appname, "host_uuid": model_obj.uuid, "app_uuid": model_obj.app.uuid,
        "plat_uuid": model_obj.platform.uuid})
    return env

def get_routing_key(model_obj):
    if isinstance(model_obj, Zones):
        return ".%s." % model_obj.host.uuid
    return ".%s." % model_obj.uuid

def get_model_obj(target):
    if target[0] == "Assets":
        model = "asset.Assets"
        return get_model(model).objects.exclude(platform_id=None,app=None).filter(pk=target[1]).first()
    else:
        model = "operation.Zones"
        return get_model(model).objects.filter(pk=target[1]).first()

@celery.task(name="push_cmd")
def PushCmd(user_account, event, target, jobname, stepcount, first=False):
    obj = get_model_obj(target)
    if not obj:
        logger.error("Instance %s-%s not exists or incomplete information!" % target)
        return {"success": False, "msg": "Instance %s-%s not exists or incomplete information!" % target}
    endpoint = proxy.get_node(*[target[0], obj])
    tag = 0
    if endpoint.getConnectionStatus() != "Connected":
        while tag < 8:
            time.sleep(1.0)
            endpoint = proxy.get_node(*[target[0], obj])
            if endpoint.getConnectionStatus() == "Connected":
                break
            tag += 1
            if tag == 8:
                logger.error("Connect node %s faild!" % target[0])
                return {"success": False, "msg": "Connect node %s faild!" % target}

    event.EventID = obj.uuid
    if first:
        env = format_env(obj)
        user = UserAccounts.objects.get(account=user_account)
        env.update({"apikey": user.apikey})
        if event.EventEnviron:
            for k,v in event.EventEnviron.iteritems(): # 防止恶意变量注入
                if k not in env:
                    env[k] = v
        event.setEventEnv(env)
    else:
        env = event.EventEnviron
    event.setEventRemoteIP(env["remote_ip"])
    print "Process ID: %s" %  current_process().index
    print "vvvvvvvvvvvvvvvv  Send %s step %s vvvvvvvvvvvvvvvv" % (obj.uuid, event.StepID)
    print "Publish message to %s" % get_routing_key(obj)
    logger.debug("Publish message to %s" % get_routing_key(obj))
    endpoint.publish_message("%s" % get_routing_key(obj), event.toJSON())
    # 发布区服任务到channel
    # KEY Format: task:app_uuid:task_uuid:channel:target_uuid
    key = "TASK:%s:%s:%s:%s" % (env["app_uuid"], event.EventUUID, env["channel"], env["uuid"])
    channel.set(key, json.dumps({"%(channel)s_%(uuid)s" % env: {"jobname":jobname, "stepname": event.EventName,
        "progress":"%s/%s" % (event.StepID-0.5, stepcount), "finish": False}}))
    channel.publish('TASK.PROGRESS', json.dumps({"app_uuid":env["app_uuid"], "key":key}))

def filter_target(user, target_map, **kwargs):
    # 暂时不支持对服务器所有执行
    if target_map[0] == 'Assets':
        return set(target_map[1])
    if target_map[1] != '__all__' and target_map[0] != 'Assets':
        return set(target_map[1])
    if kwargs["tab"] == "plat":
        targets = Zones.objects.safe_select(user, kwargs["app_uuid"], plat_uuid=kwargs["uuid"])
    else:
        targets = Zones.objects.safe_select(user, kwargs["app_uuid"], group_uuid=kwargs["uuid"])
    if kwargs["region"] != '__all__':
        region = json.loads(cache.get(utils.REDIS_REGION % (user.uuid, kwargs["app_uuid"], kwargs["region"])))
        targets = targets.filter(sid__lte=region["max_value"], sid__gte=region["min_value"])
    if targets:
        return [i[0] for i in targets.values_list('uuid') if i[0]]
    return targets

@celery.task(name='exec_workflow')
def ExecWorkFlow(user_account, workflow_uuid, target_map=(), start_step=0, inject_env=None, **kwargs):
    '''
    :param target_map: tuple (ModelName, 唯一ID列表)
    :param ModelName: Zones, Assets
    '''
    #1. 获取目标区服
    #2. 格式化目标服务器, 环境变量
    #3. 获取执行的步骤对应的脚本
    #4. 发送指令到agent
    app_uuid = kwargs.get("app_uuid", None)
    try:
        user = UserAccounts.objects.get(account=user_account)
    except:
        logger.error("Invalid user account %s" % user_account)
        return {"success": False, "msg": "Invalid user account %s" % user_account}
    if not user.is_active:
        logger.error("User %s not active" % user_account)
        return {"success": False, "msg": "User %s not active" % user_account}
    try:
        workflow = WorkFlows.objects.get(uuid=workflow_uuid)
        stepcount = workflow.flow.count()
    except:
        _msg = u"[任务] 非法的作业"
        unicast(user.uuid, _msg, False)
        logger.error("Invalid workflow uuid %s" % workflow_uuid)
        return {"success": False, "msg": "Invalid workflow uuid %s" % workflow_uuid}
    try:
        project = Apps.objects.get(pk=app_uuid)
    except Exception,e:
        _msg = u"[任务] 非法的应用"
        unicast(user.uuid, _msg, False)
        logger.error(e, exc_info=True)
        return {"success": False, "msg": "Invalid app uuid %s" % app_uuid}

    targets = filter_target(user, target_map, **kwargs)

    # 获取要执行的步骤
    try:
        next_step = WorkFlows.objects.next_step(workflow_uuid, start_step)
        if not next_step:
            _msg = u"[任务] 作业中没有具体的步骤"
            unicast(user.uuid, _msg, False)
            logger.error("WorkFlow %s no flow" % workflow_uuid)
            return {"success": False, "msg": "WorkFlow %s no flow" % workflow_uuid}
    except:
        logger.error("WorkFlow %s no flow" % workflow_uuid)
        return {"success": False, "msg": "WorkFlow %s no flow" % workflow_uuid}

    first = kwargs.pop("first", False)
    triggers = kwargs.pop("trigger", 1)
    if first:
        # 创建Task
        task = Tasks(user=user.name, user_id=user.uuid, app=project, app_alias=project.appalias, triggers=triggers,
                stepid=next_step.stepid, status=2, total=len(targets), name=workflow.name, timeout=kwargs.get("timeout", 600),
                target_map=json.dumps({"kind": target_map[0], "targets": list(targets)}))
        task.workflow = workflow
        if inject_env:
            task.inject_env = json.dumps(inject_env)
        task.save()
        # 删除定时的任务
        if triggers == 2:
            pass
    else:
        try:
            task = Tasks.objects.get(pk=kwargs["task_uuid"])
        except:
            logger.error("Invalid task uuid %s" % kwargs.get("task_uuid", None))
            return {"success": False, "msg": "Invalid task uuid %s" % kwargs.get("task_uuid", None)}

    lock_id = '{0}-lock-{1}'.format(task.uuid, next_step.stepid)
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    # 创建对应的taskstep
    if acquire_lock():
        try:
            taskstep = TaskSteps.objects.get(task__uuid=task.uuid, stepid=next_step.stepid)
        except:
            taskstep = TaskSteps(status=2, name=next_step.name, app=project, stepid=next_step.stepid, scriptflow=next_step, task=task)
            taskstep.save()
            # 设置当前步骤的过期时间
            expire_id = "TIMEOUT:%s:%s" % (task.uuid, taskstep.uuid)
            timeout = kwargs.get("timeout", 600)
            cache.set(expire_id, timeout, timeout=timeout)
        finally:
            release_lock()

    if not isinstance(inject_env, dict):
        try:
            inject_env = json.loads(inject_env)
        except:
            inject_env = {}
    inject_env.update({"trigger": triggers})

    event = EventModel.createEvent(
            event_uuid=task.uuid,
            event_data=next_step.script.content,
            event_source=kwargs.get("source", None),
            event_name=next_step.name,
            event_user=user.account,
            event_environ=inject_env,
            event_channel=kwargs.get("tab", None),
            step_id=next_step.stepid,
            event_timeout=kwargs.get("timeout", 600),
            event_args=next_step.script.param,
            flow_uuid=workflow_uuid)
    # 分发指令
    for target in targets:
        celery.send_task('push_cmd',  
                         args=(user_account, event, (target_map[0], target), workflow.name, stepcount),
                         exchange='surge', 
                         routing_key='senders',
                         kwargs={"first": first})
    logger.info("Publish message %s success" % next_step.uuid)
    return {"success": True, "msg": "Publish message %s success" % next_step.uuid}


@celery.task(name="receive_flow")
def WorkFlowReceive(event_json):
    #1. 分析指令返回的结果
    #2. 查看任务是否被关闭
    #3. 查询对应任务否需要继续执行
    #4. 调用ExecWorkFlow执行接下来的步骤
    event = Event.fromJSON(event_json)
    try:
        task = Tasks.objects.get(uuid=event.EventUUID)
    except:
        logger.error("Invalid task uuid %s" % event.EventUUID)
        return {"success": False, "msg": "Invalid task uuid %s" % event.EventUUID}
    try:
        workflow = WorkFlows.objects.get(uuid=event.FlowUUID)
    except:
        logger.error("Invalid workflow uuid %s" % event.FlowUUID)
        return {"success": False, "msg": "Invalid workflow uuid %s" % event.FlowUUID}
    try:
        step = workflow.flow.get(stepid=event.StepID)
    except:
        logger.error("Invalid step id %s" % event.StepID)
        return {"success": False, "msg": "Invalid step id %s" % event.StepID}
    taskstep = TaskSteps.objects.get(task__uuid=task.uuid, stepid=event.StepID)

    logger.info("Receive flow %s step %s" % (event.FlowUUID, event.StepID))
    tr = TaskResults(remote_ip=event.RemoteIP, elapsed=event.EventUseTime, rc=event.EventData["rc"], taskstep=taskstep,
            stdout=event.EventData["stdout"], stderr=event.EventData["stderr"], plat_uuid=event.EventEnviron["plat_uuid"],
            sid=event.EventEnviron.get("sid", None), app_id=event.EventEnviron["app_uuid"])
    tr.save()
        
    # 检查是否已经手动结束
    if task.status == 3:
        # KEY Format: task:app_uuid:task_uuid:channel:target_uuid
        logger.warning("Task %s already closed by people" % task.uuid)
        key = "TASK:%s:%s:%s:%s" % (event.EventEnviron["app_uuid"], event.EventUUID, event.EventEnviron["channel"], event.EventEnviron["uuid"])
        channel.set(key, json.dumps({"%(channel)s_%(uuid)s" % event.EventEnviron: {"finish":True}}))
        channel.publish('TASK.PROGRESS', json.dumps({"app_uuid":event.EventEnviron["app_uuid"], "key":key}))
        return {"success": False, "msg": "Task is closed"}

    # 如果有客户端返回错误, 修改当前步骤为错误(4)
    if event.EventData["rc"] != 0 and taskstep.status != 4:
        logger.debug("Set taskstep %s status=4" % taskstep.uuid)
        taskstep.status = 4
        taskstep.save(update_fields=['status'])

    # 检查当前返回是否为该步骤的最后一个, 修改步骤的状态
    if taskstep.results.count() == task.total and taskstep.status == 2:
        taskstep.status = 5
        taskstep.save(update_fields=['status'])

    next_step = WorkFlows.objects.next_step(event.FlowUUID, event.StepID)
    logger.info("Select flow %s next_step by stepid=%s, next_step=%s" % (event.FlowUUID, event.StepID, next_step))
    if next_step:
        celery.send_task('exec_workflow', 
                args=(
                    event.EventUser, 
                    event.FlowUUID,
                    (event.EventEnviron["channel"], [event.EventEnviron["uuid"]])
                ),
                exchange='surge',
                routing_key='senders',
                kwargs={
                    "app_uuid": task.app.uuid,
                    "start_step": event.StepID,
                    "inject_env": event.EventEnviron,
                    "task_uuid": event.EventUUID,
                    "timeout": event.EventTimeout,
                    "source": event.EventSource,
                    "tab": event.EventChannel,
                    "trigger": event.EventEnviron["trigger"]})
    else:
        # 没有下一步需要执行了
        key = "TASK:%s:%s:%s:%s" % (event.EventEnviron["app_uuid"], event.EventUUID, event.EventEnviron["channel"], event.EventEnviron["uuid"])
        channel.set(key, json.dumps({"%(channel)s_%(uuid)s" % event.EventEnviron: {"finish":True}}))
        channel.publish('TASK.PROGRESS', json.dumps({"app_uuid":event.EventEnviron["app_uuid"], "key":key}))

        # 没有下一步,并且当前步骤的执行结果已全部返回
        if taskstep.results.count() == task.total:
            # 如果包含执行错误(4)的步骤
            if task.steps.filter(status=7):
                task.status = 7
                _msg = u"[%s] %s 执行超时" % (task.app.appalias, task.name)
                success = False
            else:
                if task.steps.exclude(status=5):
                    task.status = 4
                    _msg = u"[%s] %s 执行失败" % (task.app.appalias, task.name)
                    success = False
                else:
                    task.status = 5
                    _msg = u"[%s] %s 执行成功" % (task.app.appalias, task.name)
                    success = True
            _now = utils.NOW()
            task.finish_at = _now
            task.elapsed = '%.2f' % (_now - task.start_at.replace(tzinfo=None)).total_seconds()
            task.save(update_fields=['status', "finish_at", 'elapsed'])
            clean_task_progress(task.app.uuid, task.uuid)
            unicast(task.user_id, _msg, success)
    return {"success": True, "msg": "ExecWorkFlow finished"}

@celery.task(name="close_task")
def CloseTasks(user_account, tasks):
    try:
        user = UserAccounts.objects.get(account=user_account)
    except:
        logger.error("Invalid user account %s" % user_account)
        return {"success": False, "msg": "Invalid user account %s" % user_account}
    for task_id in tasks:
        try:
            task = Tasks.objects.get(pk=task_id)
        except:
            continue
        try:
            target_map = json.loads(task.target_map)
        except:
            continue
        for pk in target_map[1]:
            key = "TASK:%s:%s:%s:%s" % (task.app_id, task.uuid, target_map[0], pk)
            channel.set(key, json.dumps({"%s_%s" % (target_map[0], pk): {"finish":True}}))
            channel.publish('TASK.PROGRESS', json.dumps({"app_uuid":task.app_id, "key":key}))
    _msg = u"[%s] %s 关闭成功" % (task.app.appalias, task.name)
    unicast(user.uuid, _msg, True)

def clean_task_progress(app_uuid, task_uuid, last_boardcast=False):
    cursor = 1
    match = "TASK:%s:%s:*" % (app_uuid, task_uuid)
    while cursor > 0:
        cursor, keys = channel.scan(cursor=cursor, match=match, count=300)
        for key in keys:
            if last_boardcast:
                _id = key.split(":")[-2:]
                channel.set(key, json.dumps({"_".join(_id): {"finish":True}}))
                channel.publish('TASK.PROGRESS', json.dumps({"app_uuid":app_uuid, "key":key}))
            channel.delete(key)

@periodic_task(name="CleanTimeoutTask", run_every=crontab(hour="*", minute="*", day_of_week="*"))
def inspecttimeout():
    # 检查任务是否超时
    running_steps = TaskSteps.objects.exclude(status__in=(3,4,5,6,7)).all()
    number = 0
    for step in running_steps:
        expire_id = "TIMEOUT:%s:%s" % (step.task.uuid, step.uuid)
        if cache.ttl(expire_id):
            continue
        # 已经超时
        number += 1
        step.status = 7
        step.save(update_fields=["status"])
        if step.task.status == 7:
            continue
        # 查看是否为最后一步
        if step.task.workflow.flow.aggregate(Max('stepid')).get("stepid__max", 0) == step.stepid:
            step.task.status = 7
            step.task.save(update_fields=['status'])
            clean_task_progress(step.task.app.uuid, step.task.uuid, last_boardcast=True)

    return {"success": True, "msg": "TimeOut job %s." % number}


@periodic_task(name="UpdateZabbixID", run_every=crontab(hour="2", minute="1", day_of_week="*"))
def update_hostid_by_zabbix():
    zabbix = Zabbix()
    for instance in Assets.objects.filter(deleted=False).all():
        if instance.remote_ip:
            hostid = zabbix.hostid(instance.uuid)
            if hostid:
                instance.hostid = hostid
                instance.save(update_fields=["hostid"])
