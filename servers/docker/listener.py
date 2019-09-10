import pika

from .message_type import MessageType
from ..common.database import Database


class MessageListener(object):
    __instance = {}
    
    def __new__(cls, host, queue):
        if MessageListener.__instance.get(queue) is None:
            MessageListener.__instance[queue] = object.__new__(cls)
            
        return MessageListener.__instance[queue]

    def __init__(self, host, queue):
        credentials = Database().get_credentials(host)
        credentials = pika.PlainCredentials(credentials['username'], credentials['password'])
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.queue = queue
        self.messages = []

    def callback(self, ch, method, properties, body):
        try:
            msg = body.split(max=1)
            msgtype = MessageType(int(msg[0]))

            if msgtype == MessageType.TESTS_DONE:
                self.channel.stop_consuming()
            else:
                self.messages.append((msgtype, msg[1]))
        except:
            self.channel.stop_consuming()
            
    def run(self):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        while self.channel._consumer_infos:
            self.channel.connection.process_data_events(time_limit=1)
        
        self.connection.close()
        MessageListener.__instance[self.queue] = None

    def json(self):
        return [{"type": type, "data": data} for type, data in self.messages]
