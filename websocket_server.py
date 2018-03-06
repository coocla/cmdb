#coding:utf-8
from __future__ import absolute_import
import os
import json
import time
import signal
import Queue
import socket
import threading
from collections import defaultdict
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'surge.settings')
import django
django.setup()

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver
from tornado.options import define, options

from django.db import connections
from django.conf import settings
from django.core.cache import cache
from django_redis import get_redis_connection
from asset.models import Assets

MAX_WAIT = 3
channel = get_redis_connection('default')
define("port", default=8000, help="run on the given port", type=int)
define("listen", default="127.0.0.1", help="run on the given address", type=str)
define("dev", default=False, type=bool)

class Notification(object):
    callbacks = set()
    def register(self, callback):
        self.callbacks.add(callback)

    def unregister(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def broadcast_monitor(self, msg):
        try:
            data = json.loads(msg["data"])
            app_uuid = data["app_uuid"]
            message = data["message"]
            if message:
                self.send(app_uuid, message)
        except:
            pass

    def broadcast_task(self, msg):
        try:
            data = json.loads(msg["data"])
            key = data["key"]
            app_uuid = data["app_uuid"]
            message = channel.get(key)
            if message:
                print "Cast task=%s" % message
                self.send(app_uuid, message)
        except:
            pass

    def unicast_notification(self, msg):
        try:
            data = json.loads(msg["data"])
        except:
            return
        for callback in self.callbacks:
            if options.dev:
                callback.boardcast(json.dumps({"NOTIFY":data}))
            else:
                if data["userid"] == callback.user.uuid:
                    callback.boardcast(json.dumps({"NOTIFY":data}))

    def send(self, app_uuid, msg):
        for callback in self.callbacks:
            if callback.match(app_uuid):
                callback.boardcast(msg)

def Probe(ip, port, timeout=2):
    try:
        cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
        cs.settimeout(float(timeout))
        address=(str(ip),int(port))
        status = cs.connect_ex((address))
        if status == 0:
            return 1  #正常
        elif status == 111:
            return 2  #端口不通
        else:
            return 3  #IP不通
    except Exception,e:
        return 3

class MonWorker(threading.Thread):
    def __init__(self, queue):
        super(MonWorker, self).__init__()
        self.queue = queue
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                args, kwargs = self.queue.get()
                data = defaultdict(lambda:{})
                print "MonWork Recived:", args, kwargs
                for ip, port_uuid in args.iteritems():
                    for port, uuid in port_uuid.items():
                        data["message"]["monitor-%s" % uuid] = {"health":Probe(ip, port)}
                data["app_uuid"] = kwargs["app_uuid"]
                print "Boardcast client:",data
                channel.publish('MONITOR', json.dumps(data))
            except:
                pass
            finally:
                self.queue.task_done()

class ThreadPool(object):
    def __init__(self, max_number=10):
        self.queue = Queue.Queue()
        for _ in xrange(max_number):
            MonWorker(self.queue)

    def add_task(self, args=(), **kwargs):
        print "Queue Recived:",args, kwargs
        self.queue.put((args, kwargs))

    def wait_completion(self):
        self.queue.join()

class MonitorHandler(object):
    def __init__(self):
        self.pool = ThreadPool()

    def handler(self, msg):
        try:
            data = json.loads(msg["data"])
            print "subscribe data:", data
            self.pool.add_task(data["data"], app_uuid=data["app_uuid"])
        except:
            pass


class WebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        token = self.get_cookie("X-Auth-Token")
        if not options.dev:
            user = cache.get("USER:%s" % token)
            if not user:
                print "Close no auth connect.."
                self.close(401, u"未认证,请重新登录")
                return
            self.user = user
        self.application.notification.register(self)
        if options.dev:
            self.recive_list = ["0b6f2d21fd4e11e590c4002feddfc315"]
            for match in self.recive_list:
                self.unicast(match)
        else:
            if not self.user.is_admin:
                self.recive_list = [i['app__uuid'] for i in self.user.roles.values('app__uuid')]
                for match in self.recive_list:
                    self.unicast(match)
            else:
                self.unicast('TASK:*')

    def unicast(self, match):
        cursor = 1
        while cursor > 0:
            cursor, keys = channel.scan(cursor=cursor, match=match, count=300)
            if not keys:
                break
            message = {}
            for i in channel.mget(keys):
                try:
                    message.update(json.loads(i))
                except Exception,e:
                    continue
            self.boardcast(json.dumps(message))

    def on_message(self, message):
        '''
        :param message: [remote_ip, remote_ip]
        '''
        try:
            message = json.loads(message)
        except:
            return
        data = defaultdict(lambda:{})
        assets = Assets.objects.filter(remote_ip__in=message).all()
        for host in assets:
            for zone in host.zones.all():
                try:
                    port = eval(host.app.external_port % {"sid":zone.sid})
                except:
                    continue
                data[host.remote_ip][port] = zone.uuid
        print "Recived data:", data
        channel.publish('ZONES.MOITOR', json.dumps({"app_uuid":zone.app_uuid, "data":data}))


    def match(self, app_uuid):
        if options.dev:
            return True
        if self.user.is_admin:
            return True
        if app_uuid in self.recive_list:
            return True
        return False

    def on_close(self):
        self.application.notification.unregister(self)

    def boardcast(self, msg):
        self.write_message(msg)

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        handlers = [
            (r'/websocket', WebSocket),
        ]

        setting = {
            'cookie_secret': settings.SECRET_KEY,
        }
        super(Application, self).__init__(handlers, **setting)
        self.notification = Notification()

def shutdown_instance(sig, frame):
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)

def mysql_ping():
    connect_proxy = connections["default"]
    try:
        ping = connect_proxy.is_usable()
    except:
        ping = None

    if not ping:
        try:
            connect_proxy.connect()
        except:
            return

def shutdown():
    push_server.stop()
    http_server.stop()
    if ping_server.is_running():
        ping_server.stop()

    timeout = time.time() + MAX_WAIT
    io_loop = tornado.ioloop.IOLoop.instance()
    def stop_ioloop():
        now = time.time()
        if now < timeout and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now+1, stop_ioloop)
        else:
            io_loop.stop()
    stop_ioloop()

if __name__ == '__main__':
    global http_server
    global push_server
    global ping_server
    app = Application()
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.bind(options.port, options.listen)

    ping_server = tornado.ioloop.PeriodicCallback(mysql_ping, 60000)  # 1min loop
    ping_server.start()

    monitor = MonitorHandler()
    p = channel.pubsub()
    p.subscribe(**{"TASK.PROGRESS":app.notification.broadcast_task, 
                   "TASK.NOTIFICATION":app.notification.unicast_notification,
                   "MONITOR":app.notification.broadcast_monitor,
                   "ZONES.MOITOR":monitor.handler})
    push_server = p.run_in_thread(sleep_time=0.001)
    signal.signal(signal.SIGTERM, shutdown_instance)
    signal.signal(signal.SIGINT, shutdown_instance)
    http_server.start(num_processes=1)
    tornado.ioloop.IOLoop.instance().start()
