import pika

from .message_type import MessageType


class ResultsListener(object):
    __instance = None
    
    def __new__(cls, queue):
        if ResultsListener.__instance is None:
            ResultsListener.__instance = object.__new__(cls)
            
        return ResultsListener.__instance

    def __init__(self, queue):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbit')
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.queue = queue
        self.messages = []

    def callback(self, ch, method, properties, body):
        try:
            msg = body.split(max=1)
            msgtype = int(msg[0])

            if msgtype == MessageType.TESTS_DONE:
                self.channel.stop_consuming()

            else:
                self.messages.append((MessageType(msgtype), msg[1]))
        except:
            self.channel.stop_consuming()
            
    def run(self):
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        while self.channel._consumer_infos:
            self.channel.connection.process_data_events(time_limit=1)
        self.connection.close()

    def json(self):
        return [{"type": type, "data": data} for type, data in self.messages]
