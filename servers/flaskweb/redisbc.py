from multiprocessing.connection import Listener, Client, wait
from threading import Thread
import time
import threading
import redis


class RedisBC(object):
    __instance = None
    
    r = ""#instancia de conexio amb el servidor de redis
    p = ""#instancia subscripcio de redis
    
    def __new__(cls):
        if RedisBC.__instance is None:
            RedisBC.__instance = object.__new__(cls)
            
        return RedisBC.__instance

        
	#funcio que escolta 1 canal subscrit previament i executa una funcio quan escolta resposta
    def listen(self,callback):
        print('listening')
        while True:  
            message = self.p.get_message()
            if message:
                callback(message)
            else:
                time.sleep(1)
	

    #funcio per publicar un missatge a un canal
    def publish(self,c,msg):
        self.r.publish(c,msg)

			
    #funcio per conectar-se al servidor a partir de la direccio i el port
    def connect(self, redis_host, redis_port):
        self.r = redis.StrictRedis(host=redis_host, port=redis_port)
        self.p= self.r.pubsub()
        print('Connected to redis!')
        
    
    #funcio per subscriures a un canal a partir de el nom del canal i la funcio que s'executara quan es rebi resposta
    def subscribe(self, callback, channel):
        self.p.psubscribe(channel)
        threading.Thread(target=self.listen, args=(callback, )).start()
        print('Subscribed to: ', channel)
