import socket

from .message_type import MessageType
from .message import Message

    
class ResultsSender(object):
    __instance = None
    
    def __new__(cls):
        if ResultsSender.__instance is None:
            ResultsSender.__instance = object.__new__(cls)
            
        return ResultsSender.__instance

    def connect(self, host, port, secret):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.secret = secret.encode()

    def import_error(self, **data):
        msg, _ = Message(MessageType.IMPORT_ERROR, data).pack(self.secret)
        self.socket.send(msg)

    def send_result(self, **data):
        msg, _ = Message(MessageType.TEST_RESULT, data).pack(self.secret)
        self.socket.send(msg)

    def end(self):
        msg, _ = Message(MessageType.TESTS_DONE).pack(self.secret)
        self.socket.send(msg)
