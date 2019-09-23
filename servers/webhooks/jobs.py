from gevent import subprocess, greenlet
import gevent
import os
import json
import threading

from os.path import basename

from ..common.database import Database
from ..common.logger import logger
from ..docker.sender import MessageSender
from ..docker.message_type import MessageType
from ..docker.singleton import Singleton


def retrieve_stdout(command):
    logger.info('Executing: {}'.format(' '.join(command)))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    output = proc.stdout.read()
    log = output.decode('utf-8').strip()
    logger.debug(log)
    return log
    
class Jobs(object, metaclass=Singleton):   
    def post(self, meta):
        MessageSender('rabbit', 'jobs').send(MessageType.JOB_QUEUED, meta)
        logger.info(f'Sending message JOB_QUEUED')

        if os.environ.get('DISABLE_POOL'):
            return JobsOrchestrator().handle(meta)
        else:
            Database().push_job(meta)

    
class JobsOrchestrator(object, metaclass=Singleton):
    def __init__(self):
        config = Database().get_config()
        self._oauth_token = config['oauth_token']
        self._stop = False

        if not os.environ.get('DISABLE_POOL'):
            for _ in range(config['parallel_jobs']):
                ready = gevent.event.Event()
                greenlet.Greenlet.spawn(self.update, ready)
                ready.wait()

    def __once_done(self, result):
        meta, log = result
        Database().set_instance_log(meta['org']['id'], meta['repo']['id'], meta['hash'], meta['branch'], log)
        MessageSender('rabbit', 'jobs').send(MessageType.JOB_ENDED, meta)
        logger.info(f'Sending message JOB_ENDED')

        # RM volume
        retrieve_stdout(['docker', 'volume', 'rm', meta['hash'] + '-data'])

        # Flag done
        Database().remove_job(meta)

        return True

    def __process_job(self, meta):
        instance_name = meta['hash']

        retrieve_stdout(['docker', 'create', '-t',
            '-e', 'GITHUB_BRANCH=' + meta['branch'],
            '-e', 'GITHUB_ORGANIZATION=' + meta['org']['name'],
            '-e', 'GITHUB_REPOSITORY=' + meta['repo']['name'],
            '-e', 'GITHUB_ORGANIZATION_ID=' + str(meta['org']['id']),
            '-e', 'GITHUB_REPOSITORY_ID=' + str(meta['repo']['id']),
            '-e', 'GITHUB_COMMIT=' + meta['hash'],
            '-e', 'OAUTH_TOKEN=' + self._oauth_token,
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '--mount', 'source=' + instance_name + '-data,destination=/instance',
            '--mount', 'source=grademe-secrets,target=/run/secrets,readonly',
            '--network', 'backend',
            '--rm',
            '--name', instance_name,
            'agent-bootstrap'])

        retrieve_stdout(['docker', 'network', 'connect', 'results', instance_name])
        
        MessageSender('rabbit', 'jobs').send(MessageType.JOB_STARTED, meta)
        logger.info(f'Sending message JOB_STARTED')

        return meta, retrieve_stdout(['docker', 'start', '-a', instance_name])

    def handle(self, job):
        return self.__once_done(self.__process_job(job))

    def update(self, ready):
        ready.set()

        while not self._stop:
            job = Database().get_job()
            if job is not None:
                self.handle(job)

            gevent.sleep(0.1)

    