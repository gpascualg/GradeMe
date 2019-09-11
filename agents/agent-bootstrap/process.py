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
        if data['branch'] != instance['_id']['branch']:
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

    # TODO: Make this configurable
    if data.get('language') in ('python3', 'telegram'):
        agent_name = 'agent-' + data['language']
    else:
        print('> Non-existing agent')
        update_instance(instance, 'non-existing-agent')
        return False

    volume_name = os.environ['GITHUB_ORGANIZATION_ID'] + '-' + data['execute']

    # Run detached
    return subprocess.check_output(['docker', 'run', 
        '-d', '-t', '--rm',
        '-v', '/instance:/instance',
        '--mount', 'source=' + volume_name + ',target=/tests,readonly',
        '--network', 'results',
        agent_name, rabbit_channel])

def main(instance, organization_id, rabbit_channel):
    try:
        with open('/instance/code/.autograder.yml') as fp:
            try:
                data = yaml.load(fp)
            except:
                return False

        secret = Database().get_organization_config(organization_id)['secret']
        contents = copy.copy(data)
        contents['checksum'] = secret
        contents = yaml.dump(contents, encoding='utf-8')

        checksum = hashlib.sha256(contents).hexdigest()
        if checksum == data['checksum']:
            return continue_process(instance, data, rabbit_channel)
        else:
            print("Checksum mismatch {} != {} (should be != in file)".format(checksum, data['checksum']))
            return False
    except Exception as e:
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
        # TODO(gpascualg): Notify error
    else:
        # Make sure noone can connect directly
        docker_id_or_false = main(instance, int(os.environ['GITHUB_ORGANIZATION_ID']), os.environ['GITHUB_COMMIT'])

        if docker_id_or_false:
            # Block until we have all results
            results = MessageListener('rabbit', os.environ['GITHUB_COMMIT'])
            results.run()

            # Once we reach here it's done
            update_instance(instance, 'done', results.json())
            exitcode = 0
        else:
            # TODO(gpascualg): Check exit code using docker_id_or_false
            print("Instance .autograder.yml is invalid")
            update_instance(instance, 'incorrect-yml')

except pymongo.errors.ServerSelectionTimeoutError:
    print("Could not reach MongoDB")
except Exception as e:
    print('Instance execution error: {}'.format(e))
    update_instance(instance, 'execution-error')

sys.exit(exitcode)
