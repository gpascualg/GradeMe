import pika
import json

from .message_type import MessageType
from ..common.database import Database


class MessageSender(object):
    __instance = {}
    
    def __new__(cls, host, queue):
        if MessageSender.__instance.get(queue) is None:
            MessageSender.__instance[queue] = object.__new__(cls)
            
        return MessageSender.__instance[queue]

    def __init__(self, host, queue):
        credentials = Database().get_credentials(host)
        credentials = pika.PlainCredentials(credentials['username'], credentials['password'])
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
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
        self.connection.close()
        MessageSender.__instance[self.queue] = None
    
    def send(self, type, data):
        msg = '{} {}'.format(int(type), json.dumps(data))
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg)
