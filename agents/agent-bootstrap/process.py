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
    if data.get('python-options'):
        if data['python-options'].get('scriptify'):
            agent_opts.append('-s')
        if data['python-options'].get('importable'):
            agent_opts.append('-i')

    volume_name = os.environ['GITHUB_ORGANIZATION'] + '-' + data['testset']

    # Run detached
    docker_id = subprocess.check_output(['docker', 'run', 
        '-d', '-t',
        '-v', '/instance:/instance',
        '--mount', 'source=' + volume_name + ',target=/tests,readonly',
        '--network', 'results',
        agent_name, *agent_opts, agent_name, rabbit_channel], stderr=subprocess.STDOUT)
    
    return docker_id.strip()

def on_tick(docker_id):
    is_running = False

    try:
        data = subprocess.check_output(['docker', 'inspect', docker_id], stderr=subprocess.STDOUT)
        data = json.loads(data)
        is_running = data[0]['State']['Running']
    except:
        pass

    if not is_running:
        print('Docker not running anymore')
        logs = subprocess.check_output(['docker', 'logs', docker_id], stderr=subprocess.STDOUT)
        print(logs)
    
    return is_running


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
            results.run(lambda: on_tick(docker_id_or_false))

            exitcode = 1
            try:
                inspect = subprocess.check_output(['docker', 'inspect', docker_id_or_false], stderr=subprocess.STDOUT)
                inspect = json.loads(inspect)
                exitcode = inspect[0]['State']['ExitCode']
            except:
                pass

            update_instance(instance, 'done' if exitcode == 0 else 'execution-error', results.json())
            subprocess.call(['docker', 'rm', docker_id_or_false])

except pymongo.errors.ServerSelectionTimeoutError:
    print("Could not reach MongoDB")
except Exception as e:
    print('Instance execution error: {}'.format(e))
    update_instance(instance, 'execution-error')

sys.exit(exitcode)
