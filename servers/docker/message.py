import hmac
import hashlib
import json

from .message_type import MessageType


class Message(object):
    def __init__(self, msg_type=None, data=None, digest=None):
        self.__type = msg_type
        self.__data = data
        self.__digest = digest
        self.__datasize = 0
        self.__step = 0
        self.__buffer = b''

    def Type(self):
        return self.__type

    def Data(self):
        return self.__data

    def Digest(self):
        return self.__digest

    def clone(self):
        return Message(
            msg_type=self.Type(), 
            data=self.Data(), 
            digest=self.Digest()
        )

    def is_valid(self, secret):
        _, digest = self.pack(secret)
        return digest == self.Digest()

    def pack(self, secret):
        data = json.dumps(self.__data)
        data = data.encode('utf-8')

        size = len(data)
        s0 = (size >> 0) & 0xFF
        s1 = (size >> 8) & 0xFF
        s2 = (size >> 16) & 0xFF
        s3 = (size >> 24) & 0xFF

        packed = bytes([self.__type.value, s0, s1, s2, s3]) + data
        digest = hmac.new(secret, packed, hashlib.sha256).digest()
        return packed + digest, digest

    def buffer_size(self):
        return len(self.__buffer)

    def read_pending(self):
        if self.__step == 0:
            return 1

        if self.__step == 1:
            return 4 - self.buffer_size()

        if self.__step == 2:
            return self.__datasize - self.buffer_size()

        if self.__step == 3:
            return 32 - self.buffer_size()

        return 0

    def unpack(self, data):
        # MESSAGE TYPE
        if self.__step == 0:
            self.__buffer += data
            if self.buffer_size() < 1: # If client closed connection
                return False

            self.__type = MessageType(self.__buffer[0])
            self.__step += 1
            self.__buffer = b''

        # DATA SIZE
        elif self.__step == 1:
            self.__buffer += data
            if self.buffer_size() < 4:
                return False

            self.__datasize = \
                (self.__buffer[0] << 0) | \
                (self.__buffer[1] << 8) | \
                (self.__buffer[2] << 16) | \
                (self.__buffer[3] << 24)

            self.__step += 1
            self.__buffer = b''

        # DATA
        elif self.__step == 2:
            self.__buffer += data
            if self.buffer_size() < self.__datasize:
                return False

            self.__data = json.loads(self.__buffer)
            self.__step += 1
            self.__buffer = b''
        
        # DIGEST
        elif self.__step == 3:
            self.__buffer += data
            if self.buffer_size() < 32:
                return False

            self.__digest = self.__buffer
            self.__step = 0
            self.__buffer = b''
            return True
            
        return False
