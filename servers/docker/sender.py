import pika
import json

from .message_type import MessageType


    
class ResultsSender(object):
    __instance = None
    
    def __new__(cls, queue):
        if ResultsSender.__instance is None:
            ResultsSender.__instance = object.__new__(cls)
            
        return ResultsSender.__instance

    def __init__(self, queue):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbit')
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.queue = queue

    def import_error(self, **data):
        msg = '{} {}'.format(int(MessageType.IMPORT_ERROR), json.dumps(data))
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg)

    def send_result(self, **data):
        msg = '{} {}'.format(int(MessageType.TEST_RESULT), json.dumps(data))
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg)

    def end(self):
        msg = '{} {}'.format(int(MessageType.TESTS_DONE), '-')
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg)
        self.connection.close()
    