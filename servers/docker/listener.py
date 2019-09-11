import pika

from queue import Queue

from .message_type import MessageType
from ..common.database import Database


class MessageListener(object):
    __instance = {}
    
    def __new__(cls, host, queue, messages=None):
        if MessageListener.__instance.get(queue) is None:
            MessageListener.__instance[queue] = object.__new__(cls)
            
        return MessageListener.__instance[queue]

    def __init__(self, host, queue, messages=None):
        credentials = Database().get_credentials(host)
        credentials = pika.PlainCredentials(credentials['username'], credentials['password'])
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.queue = queue
        self.messages = messages or Queue()

    def callback(self, ch, method, properties, body):
        try:
            msg = body.split(max=1)
            msgtype = MessageType(int(msg[0]))

            if msgtype == MessageType.TESTS_DONE:
                self.channel.stop_consuming()
            else:
                self.messages.put((msgtype, msg[1]))
        except:
            self.channel.stop_consuming()
            
    def run(self, on_tick=None):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        while self.channel._consumer_infos:
            self.channel.connection.process_data_events(time_limit=1)
            
            if on_tick is not None:
                if not on_tick():
                    self.channel.stop_consuming()
        
        self.connection.close()
        MessageListener.__instance[self.queue] = None

    def get(self):
        messages = []
        while True:
            try:
                messages.append(self.messages.get(False))
            except:
                break
        return messages

    def json(self):
        return [{"type": type, "data": data} for type, data in self.get()]
