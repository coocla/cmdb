#coding:utf-8
import os
import pika
import json
import time
import logging
import datetime
import threading
import commands

from django.forms.models import model_to_dict

from asset.models import Assets
from operation.models import QueueNodes

logger = logging.getLogger(__name__)

class ConnectionStatus(object):
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"

class Context(object):
    def __init__(self, rabbitmq_down_exchange=None, rabbitmq_up_exchange=None, 
            queue_username=None, queue_password=None, rabbitmq_vhost=None, 
            rabbitmq_ssl=False, rabbitmq_host=None, rabbitmq_port=5672):
        self.rabbitmq_exchange = rabbitmq_down_exchange
        self.rabbitmq_queue = rabbitmq_down_exchange
        self.queue_username = queue_username
        self.queue_password = queue_password
        self.rabbitmq_vhost = rabbitmq_vhost
        self.rabbitmq_ssl = rabbitmq_ssl
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = int(rabbitmq_port)

class AMQPSender(object):
    EXCHANGE = 'message'
    EXCHANGE_TYPE = 'topic'
    PUBLISH_INTERVAL = 1
    QUEUE = 'download'
    ROUTING_KEY = 'example.text'

    def __init__(self, agentData=None):
        """
        Setup Publisher object

        """
        self._connection = None
        self._channel = None
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0
        self._stopping = False
        self._closing = False

        self.agentData = agentData

        self.connectionStatusLock = threading.Lock()
        self.connectionStatus = ConnectionStatus.DISCONNECTED
        self.disconnectedTime = datetime.datetime.now()

    def connect(self):
        """
        初始化环境目录, 构造rabbit连接字符串
        设置消息接收的 EXCHANGE QUEUE ROUTING_KEY

        """
        self.EXCHANGE = self.agentData.rabbitmq_exchange 
        self.QUEUE = self.agentData.rabbitmq_queue
        self.ROUTING_KEY = ''

        credentials = pika.PlainCredentials(self.agentData.queue_username, 
                self.agentData.queue_password)
        parameters = pika.ConnectionParameters(host=self.agentData.rabbitmq_host,
                port=self.agentData.rabbitmq_port,
                virtual_host=self.agentData.rabbitmq_vhost, credentials=credentials,
                ssl=self.agentData.rabbitmq_ssl, channel_max=1000,
                connection_attempts=3, retry_delay=5,
                socket_timeout=10, heartbeat_interval=10)
        logger.info('AMQPSender Connecting to %s:%s' % (self.agentData.rabbitmq_host, self.agentData.rabbitmq_port))
        return pika.SelectConnection(parameters,
                                     self.on_connection_open,
                                     stop_ioloop_on_close=False)

    def getConnectionStatus(self):
        return self.connectionStatus
    
    def getDisconnectedTime(self):
        return self.disconnectedTime

    def on_connection_open(self, unused_connection):
        """
        当连接打开后, 修改当前的连接状态和断开时间, 并添加连接关闭的回调, 打开channel
        """
        logger.debug('AMQPSender Connection opened')
        self.connectionStatusLock.acquire()
        self.connectionStatus = ConnectionStatus.CONNECTED
        self.disconnectedTime = None
        self.connectionStatusLock.release()

        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        """
        将 on_connection_closed 设置为连接关闭的回调函数
        """
        logger.debug('AMQPSender Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """
        用于连接意外中断时的处理, 并且启动重连

        :param int reply_code: 意外断开的code
        :param str reply_text: 断开的原因/exception
        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logger.warning('AMQPSender Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self.connectionStatusLock.acquire()
            self.connectionStatus = ConnectionStatus.DISCONNECTED
            self.disconnectedTime = datetime.datetime.now()
            self.connectionStatusLock.release()
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """
        利用ioloop重新执行 connect 创建连接字符串
        """
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0

        # 停掉老的连接字符串实例
        self._connection.ioloop.stop()

        if not self._closing:
            # 创建新的连接字符串实例
            self._connection = self.connect()

            # 利用ioloop运行这个连接实例
            self._connection.ioloop.start()

    def open_channel(self):
        """
        打开一个新的channel, 当channel被打开后, on_channel_open 将会被调用
        """
        logger.debug('AMQPSender Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """
        当 channel 被打开后, channel实例将会传递进来, 此时添加channel关闭的回调处理
        并且开启持久化消息, 发送本地需要发送的消息
        """
        logger.debug('AMQPSender Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)
        self.enable_delivery_confirmations()
        #self.publish_message()

    def add_on_channel_close_callback(self):
        """
        添加 channel 关闭的回调函数
        """
        logger.debug('AMQPSender Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """
        当 channel 关闭则连接字符串不可用, 此时主动关闭连接字符串触发重连机制

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        logger.warning('AMQPSender Channel was closed: (%s) %s', reply_code, reply_text)
        if not self._closing:
            self._connection.close()

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        logger.debug('AMQPSender Declaring exchange %s', exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self.EXCHANGE_TYPE,
                                       durable=True)

    def on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        logger.debug('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name, durable=True)

    def on_queue_declareok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """
        logger.debug('Binding %s with %s',
                    self.EXCHANGE, self.QUEUE)
        self._channel.queue_bind(self.on_bindok, self.QUEUE, self.EXCHANGE)

    def on_bindok(self, unused_frame):
        """This method is invoked by pika when it receives the Queue.BindOk
        response from RabbitMQ. Since we know we're now setup and bound, it's
        time to start publishing."""
        self.start_publishing()

    def start_publishing(self):
        """This method will enable delivery confirmations and schedule the
        first message to be sent to RabbitMQ

        """
        logger.debug('Issuing consumer related RPC commands')
        self.enable_delivery_confirmations()
        #self.schedule_next_message()

    def enable_delivery_confirmations(self):
        """
        开启消息确认

        当消息被确认时, on_delivery_confirmation 将会通过 Basic.ACK 或 Basic.Nack
        来判断消息是确认还是拒绝, 确保消息成功投递
        """
        logger.debug('Issuing Confirm.Select RPC command')
        self._channel.confirm_delivery(self.on_delivery_confirmation)

    def on_delivery_confirmation(self, method_frame):
        """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
        command, passing in either a Basic.Ack or Basic.Nack frame with
        the delivery tag of the message that was published. The delivery tag
        is an integer counter indicating the message number that was sent
        on the channel via Basic.Publish. Here we're just doing house keeping
        to keep track of stats and remove message numbers that we expect
        a delivery confirmation of from the list used to keep track of messages
        that are pending confirmation.

        :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame

        """
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        logger.debug('Received %s for delivery tag: %i',
                    confirmation_type,
                    method_frame.method.delivery_tag)
        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1

        try:
            if method_frame.method.delivery_tag in self._deliveries :
                self._deliveries.remove(method_frame.method.delivery_tag)
        except Exception,e:
            logger.error(e, exc_info=True)

        logger.debug('Published %i messages, %i have yet to be confirmed, '
                    '%i were acked and %i were nacked',
                    self._message_number, len(self._deliveries),
                    self._acked, self._nacked)

    def schedule_next_message(self):
        """If we are not closing our connection to RabbitMQ, schedule another
        message to be delivered in PUBLISH_INTERVAL seconds.

        """
        if self._stopping:
            return
        logger.debug('Scheduling next message for %0.1f seconds',
                    self.PUBLISH_INTERVAL)
        self._connection.add_timeout(self.PUBLISH_INTERVAL,
                                     self.publish_message)

    def publish_message(self, routing_key, message):
        """If the class is not stopping, publish a message to RabbitMQ,
        appending a list of deliveries with the message number that was sent.
        This list will be used to check for delivery confirmations in the
        on_delivery_confirmations method.

        Once the message has been sent, schedule another message to be sent.
        The main reason I put scheduling in was just so you can get a good idea
        of how the process is flowing by slowing down and speeding up the
        delivery intervals by changing the PUBLISH_INTERVAL constant in the
        class.

        """
        if self._stopping:
            return


        if not self._channel:
            self._connection = self.connect()
            self._connection.ioloop.start()

        time.sleep(3)
        self._channel.basic_publish(self.EXCHANGE, routing_key, message,
                properties=pika.BasicProperties(delivery_mode=2))
        self._message_number += 1
        self._deliveries.append(self._message_number)
        logger.info('Published message # %i', self._message_number)
        #self.schedule_next_message()

    def close_channel(self):
        """Invoke this command to close the channel with RabbitMQ by sending
        the Channel.Close RPC command.

        """
        logger.debug('Closing the channel')
        if self._channel:
            self._channel.close()

    def run(self):
        """Run the example code by connecting and then starting the IOLoop.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        """Stop the example by closing the channel and connection. We
        set a flag here so that we stop scheduling new messages to be
        published. The IOLoop is started because this method is
        invoked by the Try/Catch below when KeyboardInterrupt is caught.
        Starting the IOLoop again will allow the publisher to cleanly
        disconnect from RabbitMQ.

        """
        logger.info('Stopping')
        self._stopping = True
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.start()
        logger.info('Stopped')

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logger.info('Closing connection')
        self._closing = True
        self._connection.close()

class Control(object):
    def __init__(self):
        self.Nodes = {}

    def __new__(cls, *args, **kw):  
        if not hasattr(cls, '_instance'):
            org = super(Control, cls)
            cls._instance = org.__new__(cls, *args, **kw)
        return cls._instance

    def get_node(self, name, obj):
        control = getattr(self, "get_by_%s" % name)(obj)
        if control.rabbitmq_host in self.Nodes:
            return self.Nodes[control.rabbitmq_host]
        conn = self._initial(control)
        self.Nodes[control.rabbitmq_host] = conn
        return conn

    def _initial(self, node):
        kwargs = model_to_dict(node, exclude=['uniq_id', 'uuid', 'name', 'create_user', 'created_at'])
        context = Context(**kwargs)
        conn = AMQPSender(context)
        t =  ControlThread(conn)
        t.start()
        return conn

    def get_by_Zones(self, obj):
        return obj.host.control

    def get_by_Assets(self, obj):
        return obj.control


class ControlThread(threading.Thread):
    def __init__(self, conn):
        super(ControlThread, self).__init__()
        self.daemon = True
        self.conn = conn

    def run(self):
        self.conn.run()

    def stop(self):
        self.conn.stop()


def main():
    context = Agent()
    example = AMQPSender(context)
    pool = {}
    pool["42.51.161.236"] = example
    t = threading.Thread(target=example.run)
    t.start()
    try:
        while 1:
            pass
    except:
        example.stop()

if __name__ == '__main__':
    main()
