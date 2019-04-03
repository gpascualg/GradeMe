from multiprocessing import Pool



#importar RedisBC
import subprocess
import os
import json
import tempfile

from os.path import basename
from ..common.redisbc import RedisBC
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
        instance_path = tempfile.mkdtemp(dir=self.mounts['/instances'])
        instance_name = basename(instance_path)

        return meta, retrieve_stdout(['docker', 'run', '-td', '--rm',
            '-e', 'GITHUB_BRANCH=' + meta['branch'],
            '-e', 'GITHUB_ORGANIZATION=' + meta['org']['name'],
            '-e', 'GITHUB_REPOSITORY=' + meta['repo']['name'],
            '-e', 'GITHUB_ORGANIZATION_ID=' + meta['org']['id'],
            '-e', 'GITHUB_REPOSITORY_ID=' + meta['repo']['id'],
            '-e', 'GITHUB_COMMIT=' + meta['hash'],
            '-e', 'OAUTH_TOKEN=' + self.oauth_token,
            '-e', 'DOCKER_NAME=' + instance_name,
            '-e', 'AUTOGRADER_SECRET=' + Database().get_organization_config(meta['org']['id'])['secret'],
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '--mount', 'type=tmpfs,destination=/instance',
            '--network', 'system',
            '--network', 'results', # TODO(gpascualg): Can we have two networks here?
            '--name', instance_name,
            'agent-bootstrap'])
    
    def __once_done(self, result):
        meta, log = result
        Database().set_instance_log(meta['org']['id'], meta['repo']['id'], meta['hash'], meta['branch'], log)
        #TODO REDIS
        
    def post(self, meta):
        self.pool.apply_async(self.__process, meta,
            callback=self.__once_done)
            
    def trymax():
        print('qwe')
        RedisBC().connect("localhost",6379,"hola")
        RedisBC().subscribe(asd)
        
    def trymax():
        print('zxc')
        RedisBC().connect("localhost",6379,"hola")
        RedisBC().publish("hola","ggggg")
        
    def asd():
        print("asd")
