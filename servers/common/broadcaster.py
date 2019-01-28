from multiprocessing.connection import Listener, Client, wait
from threading import Thread


class Broadcaster(object):
    __instance = None
    
    def __new__(cls):
        if Broadcaster.__instance is None:
            Broadcaster.__instance = object.__new__(cls)
            
        return Broadcaster.__instance

    def __listen(self):
        with Listener(self.address, authkey=self.secret, family='AF_INET') as listener:
            while self.running:
                self.connections.append(listener.accept())

    def __poll(self):
        while self.running:
            for r in wait(self.connections, timeout=1.0):
                try:
                    msg = r.recv()
                except:
                    self.connections.remove(r)
                else:
                    # Forward message
                    self.broadcast(msg)        

    def broadcast(self, msg):
        for s in self.connections:
            s.send(msg)

    def run(self, host, port, secret):
        self.running = True
        self.address = (host, port)
        self.secret = secret
        self.connections = []        
        self.listen_thread = Thread(target=self.__listen)
        self.poll_thread = Thread(target=self.__poll)

        self.listen_thread.start()
        self.poll_thread.start()
        
    def close(self):
        self.running = False
        
        # Use a dummy client to trigger an accept
        with Client(self.address, authkey=self.secret, family='AF_INET'):
            self.listen_thread.join()
            self.poll_thread.join()

