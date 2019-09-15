from ..sender import MessageSender

def get_rabbit_sender():
    return MessageSender.get()
