from multiprocessing.connection import Listener, Client, wait
from threading import Thread
from enum import Enum


class MessageType(Enum):
    IMPORT_ERROR    = 0
    TEST_RESULT     = 1
    TESTS_DONE      = 2


class Message(object):
    def __init__(self, msg_type, data=None):
        self.Type = msg_type
        self.Data = data


class ResultsListener(object):
    __instance = None
    
    def __new__(cls):
        if ResultsListener.__instance is None:
            ResultsListener.__instance = object.__new__(cls)
            
        return ResultsListener.__instance

    def __listen(self):
        with Listener(self.address, authkey=self.secret, family='AF_INET') as listener:
                self.connections.append(listener.accept())

    def __poll(self):
        while self.running:
            for r in wait(self.connections, timeout=1.0):
                try:
                    msg = r.recv()
                except:
                    self.connections.remove(r)
                else:
                    if msg.Type == MessageType.TESTS_DONE:
                        self.running = False
                        break
                    
                    self.messages.append(msg)

    def run(self, host, port, secret):
        self.running = True
        self.address = (host, port)
        self.secret = secret
        self.connections = []
        self.messages = []        
        self.listen_thread = Thread(target=self.__listen)
        self.poll_thread = Thread(target=self.__poll)

        self.__listen()
        self.__poll()

    
class ResultsSender(object):
    __instance = None
    
    def __new__(cls):
        if ResultsSender.__instance is None:
            ResultsSender.__instance = object.__new__(cls)
            
        return ResultsSender.__instance

    def connect(self, host, port, secret):
        self.client = Client((host, port), authkey=secret, family='AF_INET')

    def import_error(self, **data):
        self.client.send(Message(MessageType.IMPORT_ERROR, data))

    def send_result(self, **data):
        self.client.send(Message(MessageType.TEST_RESULT, data))

    def end(self):
        self.client.send(Message(MessageType.TESTS_DONE))
