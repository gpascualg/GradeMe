import pika
import json
import threading
from threading import Thread
from queue import Queue

from .message_type import MessageType


class MessageSender(object):
    __instance = {}
    
    @staticmethod
    def get(queue=None):
        # This is not the most beautiful code out there
        # If there is more than one instance running (or none), expect the unexpected
        if queue is None:
            ident = next(iter(MessageSender.__instance.keys()))
        else:
            ident = threading.get_ident()
            ident = (ident, queue)

        return MessageSender.__instance.get(ident)

    def __new__(cls, host, queue):
        ident = threading.get_ident()
        ident = (ident, queue)
        if MessageSender.__instance.get(ident) is None:
            MessageSender.__instance[ident] = object.__new__(cls)
            MessageSender.__instance[ident].__init(host, queue)
            
        return MessageSender.__instance[ident]

    def __init(self, host, queue):
        # Save rabbit credentials
        with open('/run/secrets/RABBIT_USER') as fp:
            rabbit_username = fp.read().strip()
        with open('/run/secrets/RABBIT_PASS') as fp:
            rabbit_password = fp.read().strip()

        credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
        self.queue = queue
        self.msgs = Queue()
        self.thread = Thread(target=self.run, args=(credentials, host, queue))
        self.thread.start()
        
    def run(self, credentials, host, queue):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=credentials)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.channel.confirm_delivery()

        while True:
            try:
                try:
                    msg = self.msgs.get(False)
                    if msg is None:
                        self.connection.close()
                        break
                    else:
                        self.channel.basic_publish(exchange='', routing_key=self.queue, body=msg)
                except:
                    pass

                self.connection.sleep(0.1)
            except:
                break

        MessageSender.__instance[self.queue] = None        

    def import_error(self, **data):
        self.send(MessageType.IMPORT_ERROR, data)

    def send_result(self, **data):
        self.send(MessageType.TEST_RESULT, data)

    def end(self):
        self.send(MessageType.TESTS_DONE, {})
        self.msgs.put(None)
        self.thread.join()
    
    def send(self, type, data):
        msg = '{} {}'.format(int(type.value), json.dumps(data))
        self.msgs.put(msg)
