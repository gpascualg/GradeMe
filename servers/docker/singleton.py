import threading


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        key = (cls, *args, *kwargs.items())
        if key not in cls._instances:
            cls._instances[key] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]
    def get(cls, idx=0):
        instances = iter(cls._instances.values())
        return [next(instances) for _ in range(idx + 1)][0]
    def reset(cls):
        cls._instances.clear()

class ThreadedSingleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        iden = threading.get_ident()
        key = (iden, cls, *args, *kwargs.items())
        if key not in cls._instances:
            cls._instances[key] = super(ThreadedSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]
    def get(cls, idx=0):
        instances = iter(cls._instances.values())
        return [next(instances) for _ in range(idx + 1)][0]
    def reset(cls):
        cls._instances.clear()
