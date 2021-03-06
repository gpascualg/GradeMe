import pika
import json
import threading
from queue import Queue, Empty

from .message_type import MessageType
from .singleton import ThreadedSingleton



class MessageListener(object, metaclass=ThreadedSingleton):
    def __init__(self, host, queue, messages=None):
        with open('/run/secrets/RABBIT_USER') as fp:
            rabbit_username = fp.read().strip()
        with open('/run/secrets/RABBIT_PASS') as fp:
            rabbit_password = fp.read().strip()

        credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.queue = queue
        self.messages = messages or Queue()

    def callback(self, ch, method, properties, body):
        try:
            msg = body.split(maxsplit=1)
            msgtype = MessageType(int(msg[0]))

            if msgtype == MessageType.TESTS_DONE:
                self.channel.stop_consuming()
            else:
                data = json.loads(msg[1])
                self.messages.put((msgtype, data))
        except Exception as e:
            print("Exception {}".format(repr(e)))
            self.channel.stop_consuming()
            
    def run(self, on_tick=None):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        while self.channel._consumer_infos:
            self.channel.connection.process_data_events(time_limit=1)
            
            if on_tick is not None:
                if not on_tick():
                    self.channel.stop_consuming()
        
        self.connection.close()

    def get(self):
        messages = []
        while True:
            try:
                messages.append(self.messages.get(False))
            except Empty as e:
                break
        return messages

    def json(self):
        return [{'type': msgtype.value, **data} for msgtype, data in self.get()]
