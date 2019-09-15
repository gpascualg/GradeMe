from multiprocessing import Pool

import subprocess
import os
import json
import tempfile

from os.path import basename

from ..common.database import Database
from ..common.logger import logger
from ..docker.sender import MessageSender
from ..docker.message_type import MessageType


def retrieve_stdout(command):
    logger.info('Executing: {}'.format(' '.join(command)))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    output = proc.stdout.read()
    log = output.decode('utf-8').strip()
    logger.debug(log)
    return log

def process_job(meta, oauth_token):
    instance_path = tempfile.mkdtemp()
    instance_name = basename(instance_path)

    retrieve_stdout(['docker', 'create', '-t',
        '-e', 'GITHUB_BRANCH=' + meta['branch'],
        '-e', 'GITHUB_ORGANIZATION=' + meta['org']['name'],
        '-e', 'GITHUB_REPOSITORY=' + meta['repo']['name'],
        '-e', 'GITHUB_ORGANIZATION_ID=' + str(meta['org']['id']),
        '-e', 'GITHUB_REPOSITORY_ID=' + str(meta['repo']['id']),
        '-e', 'GITHUB_COMMIT=' + meta['hash'],
        '-e', 'OAUTH_TOKEN=' + oauth_token,
        '-v', '/var/run/docker.sock:/var/run/docker.sock',
        '--mount', 'type=tmpfs,destination=/instance',
        '--mount', 'source=secrets,target=/run/secrets,readonly',
        '--network', 'backend',
        '--rm',
        '--name', instance_name,
        'agent-bootstrap'])

    retrieve_stdout(['docker', 'network', 'connect', 'results', instance_name])
    
    MessageSender('rabbit', 'jobs').send(MessageType.JOB_STARTED, meta)
    logger.info(f'Sending message JOB_STARTED')

    return meta, retrieve_stdout(['docker', 'start', '-a', instance_name])
    
class Jobs(object):
    __instance = None

    def __new__(cls):
        if Jobs.__instance is None:
            Jobs.__instance = object.__new__(cls)
        return Jobs.__instance

    def __init__(self):
        config = Database().get_config()
        self.oauth_token = config['oauth_token']
        self.pool = Pool(config['parallel_jobs'])
    
    def __once_done(self, result):
        meta, log = result
        Database().set_instance_log(meta['org']['id'], meta['repo']['id'], meta['hash'], meta['branch'], log)
        MessageSender('rabbit', 'jobs').send(MessageType.JOB_ENDED, meta)
        logger.info(f'Sending message JOB_ENDED')
        return True
    
    def post(self, meta):
        MessageSender('rabbit', 'jobs').send(MessageType.JOB_QUEUED, meta)
        logger.info(f'Sending message JOB_QUEUED')

        if os.environ.get('DISABLE_POOL'):
            return self.__once_done(process_job(meta, self.oauth_token))
        else:
            return self.pool.apply_async(process_job, (meta, self.oauth_token), callback=self.__once_done)
