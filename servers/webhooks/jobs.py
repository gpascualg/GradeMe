from multiprocessing import Pool

import subprocess
import os
import json
import tempfile

from os.path import basename

from ..common.database import Database


def retrieve_stdout(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    output = proc.stdout.read()
    return output.decode('utf-8').strip()

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

    def __process(self, meta):
        instance_path = tempfile.mkdtemp()
        instance_name = basename(instance_path)

        retrieve_stdout(['docker', 'create', '-t', '--rm',
            '-e', 'GITHUB_BRANCH=' + meta['branch'],
            '-e', 'GITHUB_ORGANIZATION=' + meta['org']['name'],
            '-e', 'GITHUB_REPOSITORY=' + meta['repo']['name'],
            '-e', 'GITHUB_ORGANIZATION_ID=' + str(meta['org']['id']),
            '-e', 'GITHUB_REPOSITORY_ID=' + str(meta['repo']['id']),
            '-e', 'GITHUB_COMMIT=' + meta['hash'],
            '-e', 'OAUTH_TOKEN=' + self.oauth_token,
            '-e', 'DOCKER_NAME=' + instance_name,
            '-e', 'AUTOGRADER_SECRET=' + Database().get_organization_config(meta['org']['id'])['secret'],
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '--mount', 'type=tmpfs,destination=/instance',
            '--network', 'backend',
            '--name', instance_name,
            'agent-bootstrap'])

        retrieve_stdout(['docker', 'network', 'connect', 'internal', instance_name])

        return meta, retrieve_stdout(['docker', 'start', '-a', instance_name])
    
    def __once_done(self, result):
        meta, log = result
        print(log)
        Database().set_instance_log(meta['org']['id'], meta['repo']['id'], meta['hash'], meta['branch'], log)
        
    def post(self, meta):
        if os.environ.get('DISABLE_POOL'):
            self.__once_done(self.__process(meta))
        else:
            self.pool.apply_async(self.__process, meta,
                callback=self.__once_done)
