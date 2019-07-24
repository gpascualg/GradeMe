import pika
import json

from .message_type import MessageType


    
class MessageSender(object):
    __instance = {}
    
    def __new__(cls, queue):
        if MessageSender.__instance.get(queue) is None:
            MessageSender.__instance[queue] = object.__new__(cls)
            
        return MessageSender.__instance[queue]

    def __init__(self, queue):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbit')
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.queue = queue

    def import_error(self, **data):
        self.send(MessageType.IMPORT_ERROR, data)

    def send_result(self, **data):
        self.send(MessageType.TEST_RESULT, data)

    def end(self):
        self.send(MessageType.TESTS_DONE, {})
    
    def send(self, type, data):
        msg = '{} {}'.format(int(type), json.dumps(data))
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg)