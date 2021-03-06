import os
import sys
import yaml
import json
import hashlib
import subprocess
import tempfile
import string
import shutil
import copy
import argparse
import datetime
import random
import pymongo
import time

from queue import Queue
from distutils.dir_util import copy_tree
from os.path import basename

from servers.common.database import Database
from servers.docker import MessageListener


def update_instance(instance, status, results=[]):
    Database().update_instance(
        instance['_id']['org'], 
        instance['_id']['repo'],
        instance['instances'][0]['hash'],
        instance['instances'][0]['branch'],
        status,
        results
    )

def continue_process(instance, data, rabbit_channel):
    if 'branch' in data:
        if data['branch'] != instance['instances'][0]['branch']:
            update_instance(instance, 'branch-mismatch')
            print('> Skipped due to branch mismatch')
            return False

    if 'max_per_day' in data:
        daily_usage = instance['daily_usage']
        current_date = datetime.datetime.now().strftime("%y-%m-%d")
        daily_usage[current_date] = daily_usage.get(current_date, 0) + 1

        if daily_usage[current_date] > data['max_per_day']:
            update_instance(instance, 'out-of-tries')
            print('> No more attempts allowed today')
            return False

        Database().update_daily_usage(
            instance['_id']['org'],
            instance['_id']['repo'],
            daily_usage
        )

    # TODO(gpascualg): Make this configurable
    if data.get('language') in ('python3', 'telegram'):
        agent_name = 'agent-' + data['language']
    else:
        print('> Non-existing agent')
        update_instance(instance, 'non-existing-agent')
        return False

    # TODO(gpascualg): Add more options?
    agent_opts = []
    if data.get('python'):
        if data['python'].get('scriptify'):
            agent_opts.append('-s')
        if data['python'].get('importable'):
            agent_opts.append('-i')

    if data.get('default'):
        agent_opts.append('-d')

    volume_name = os.environ['GITHUB_ORGANIZATION'] + '-' + data['testset']

    print('Proceeding to run {} with options: {}'.format(agent_name, ' '.join(agent_opts)))

    # Run detached
    docker_id = subprocess.check_output(['docker', 'run', 
        '-d', '-t',
        '--mount', 'source=' + os.environ['GITHUB_COMMIT'] + '-data,target=/instance',
        '--mount', 'source=' + volume_name + ',target=/tests',
        '--mount', 'source=grademe-secrets,target=/run/secrets',
        '--network', 'results',
        agent_name, *agent_opts, agent_name, rabbit_channel], stderr=subprocess.PIPE)
    
    return docker_id.strip()

def on_tick(docker_id):
    is_running = False
    exit_code = -1

    try:
        data = subprocess.check_output(['docker', 'inspect', docker_id], stderr=subprocess.PIPE)
        data = json.loads(data)
        is_running = data[0]['State']['Running']
        exit_code = data[0]['State']['ExitCode']
    except:
        pass

    if not is_running:
        print('Docker not running anymore')
        logs = subprocess.check_output(['docker', 'logs', docker_id], stderr=subprocess.PIPE)
        print(logs)
    
    return is_running, exit_code


def main(instance, organization_id, rabbit_channel):
    try:
        with open('/instance/code/.autograder.yml') as fp:
            try:
                data = yaml.load(fp)
            except Exception as e:
                print("Got an exception processing .autograder.yml: {}".format(e))
                update_instance(instance, 'wrong-yml')
                return False
    except:
        update_instance(instance, 'missing-yml')
        print('.autograder-yml is missing')
        return False

    try:
        # TODO(gpascualg): Do not hardcode version here...
        if data['version'] != 3:
            update_instance(instance, 'version-mismatch')
            print("Version mismatch {} != {} (should-be != in-file)".format(3, data['version']))
            return False

        secret = Database().get_organization_config(organization_id)['secret']
        contents = copy.copy(data)
        contents['checksum'] = secret
        contents = yaml.dump(contents, encoding='utf-8')

        checksum = hashlib.sha256(contents).hexdigest()
        if checksum == data['checksum']:
            return continue_process(instance, data, rabbit_channel)
        else:
            update_instance(instance, 'checksum-mismatch')
            print("Checksum mismatch {} != {} (should-be != in-file)".format(checksum, data['checksum']))
            return False

    except Exception as e:
        update_instance(instance, 'unknown-error') # Possibly yml missing
        print("Got an exception processing .autograder.yml: {}".format(e))
        return False

######################################################################################
# MAIN CODE

# TODO(gpascualg): Make mongodb host configurable
Database.initialize('mongo')

exitcode = 1
try:
    instance = Database().get_instance(
        int(os.environ['GITHUB_ORGANIZATION_ID']),
        int(os.environ['GITHUB_REPOSITORY_ID']),
        os.environ['GITHUB_COMMIT'],
        os.environ['GITHUB_BRANCH']
    )
    
    if instance is None:
        print('Could not find instance, should never happen')
        update_instance(instance, 'fatal')
    else:
        # Make sure noone can connect directly
        docker_id_or_false = main(instance, int(os.environ['GITHUB_ORGANIZATION_ID']), os.environ['GITHUB_COMMIT'])
        
        # If it is False then processing stopped
        if docker_id_or_false:
            # Block until we have all results
            results = MessageListener('rabbit', os.environ['GITHUB_COMMIT'])
            results.run(lambda: on_tick(docker_id_or_false)[0])

            # Maybe it has not yet ended, gracefully wait
            exit_code = -1
            is_running = True
            while is_running:
                time.sleep(1)
                is_running, exit_code = on_tick(docker_id_or_false)

            # Done, update info and rm
            update_instance(instance, 'done' if exit_code == 0 else 'execution-error', results.json())
            subprocess.call(['docker', 'rm', docker_id_or_false])

except pymongo.errors.ServerSelectionTimeoutError:
    print("Could not reach MongoDB")
except Exception as e:
    print('Instance execution error: {}'.format(e))
    update_instance(instance, 'execution-error')

sys.exit(exitcode)
