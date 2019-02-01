import socket
import select

from .message_type import MessageType
from .message import Message


class ResultsListener(object):
    __instance = None
    
    def __new__(cls):
        if ResultsListener.__instance is None:
            ResultsListener.__instance = object.__new__(cls)
            
        return ResultsListener.__instance

    def __listen(self):
        self.socket.bind(self.address)
        self.socket.listen(1)
        
        (clientsocket, address) = self.socket.accept()
        clientsocket.setblocking(0)
        self.__connections.append(clientsocket)

    def __poll(self):
        msg = Message()

        while self.running:
            read_ready, _, _ = select.select(self.__connections, [], [], 1.0)
            for sock in read_ready:

                read_size = msg.read_pending()
                data = sock.recv(read_size)

                # Disconnected
                if not data:
                    self.running = False
                    sock.close()
                    break

                if msg.unpack(data):
                    if not msg.is_valid(self.secret):
                        self.running = False
                        sock.close()
                        break

                    if msg.Type() == MessageType.TESTS_DONE:
                        self.running = False
                        sock.close()
                        break
                    
                    self.__messages.append(msg.clone())

    def run(self, host, port, secret):
        self.running = True
        self.address = (host, port)
        self.secret = secret.encode()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__connections = []
        self.__messages = []
        self.__listen()
        self.__poll()

    def json(self):
        return [{"type": msg.Type().value, "data": msg.Data()} for msg in self.__messages]
