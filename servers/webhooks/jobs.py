from multiprocessing import Pool

import subprocess
import os
import json

from ..common.database import Database


def retrieve_stdout(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    output = proc.stdout.read()
    return output.decode('utf-8').strip()


def fetch_current_docker():
    docker_id = os.environ.get('DOCKER_ID', 
        retrieve_stdout(['cat', '/proc/1/cpuset']).split('/')[-1])
    msg = retrieve_stdout(['docker', 'inspect', docker_id])
    msg = msg[:msg.rfind(']') + 1]
    docker_info = json.loads(msg)

    try:
        network_name = list(docker_info[0]['NetworkSettings']['Networks'].keys())[0]
        mounts = docker_info[0]['Mounts']
        mounts = {mount['Destination']: mount['Source'] for mount in mounts}

        return network_name, mounts
    except:
        return None, {}


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
        self.network_name, self.mounts = fetch_current_docker()

    def __process(self, meta):
        return meta, retrieve_stdout(['docker', 'run', '-td',
            '-e', 'GITHUB_BRANCH=' + meta['branch'],
            '-e', 'GITHUB_ORGANIZATION=' + meta['org']['name'],
            '-e', 'GITHUB_REPOSITORY=' + meta['repo']['name'],
            '-e', 'GITHUB_ORGANIZATION_ID=' + meta['org']['id'],
            '-e', 'GITHUB_REPOSITORY_ID=' + meta['repo']['id'],
            '-e', 'GITHUB_COMMIT=' + meta['hash'],
            '-e', 'OAUTH_TOKEN=' + self.oauth_token,
            '-e', 'DOCKER_MOUNT_PATHS=' + self.mounts['/tests'] + ':/tests' + ';' + self.mounts['/instances'] + ':/instances',
            '-e', 'AUTOGRADER_SECRET=' + Database().get_organization_config(meta['org']['id'])['secret'],
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '-v', self.mounts['/tests'] + ':/tests',
            '-v', self.mounts['/instances'] + ':/instances',
            '--network', self.network_name,
            'agent-bootstrap'])
    
    def __once_done(self, result):
        meta, log = result
        Database().set_instance_log(meta['org']['id'], meta['repo']['id'], meta['hash'], meta['branch'], log)
        
    def post(self, meta):
        self.pool.apply_async(self.__process, meta,
            callback=self.__once_done)
