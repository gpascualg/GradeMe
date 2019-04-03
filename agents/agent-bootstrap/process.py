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

from pymongo import MongoClient
from distutils.dir_util import copy_tree
from os.path import basename

from servers.common.database import Database
from servers.docker import ResultsListener


def update_instance(instance, status, results=[]):
    Database().update_instance(
        instance['_id']['org'], 
        instance['_id']['repo'],
        instance['instances'][0]['hash'],
        instance['instances'][0]['branch'],
        status,
        results
    )

def continue_process(instance, data, random_secret):
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

    docker_name = os.environ['DOCKER_NAME']
    volume_name = os.environ['GITHUB_ORGANIZATION_ID'] + '-' + data['execute']

    # Run detached
    return subprocess.check_output(['docker', 'run', 
        '-d', '-t', '--rm',
        '-v', '/instance:/instance',
        '--mount', 'source=' + volume_name + ',target=/tests,readonly',
        '--network', 'results',
        agent_name, docker_name, random_secret])

def main(instance, random_secret):
    try:
        with open('/instance/code/.autograder.yml') as fp:
            try:
                data = yaml.load(fp)
            except:
                return False

        contents = copy.copy(data)
        contents['checksum'] = os.environ['AUTOGRADER_SECRET']
        contents = yaml.dump(contents, encoding='utf-8')

        if hashlib.sha256(contents).hexdigest() == data['checksum']:
            return continue_process(instance, data, random_secret)
        else:
            return False
    except:
        return False


######################################################################################
# MAIN CODE

# TODO(gpascualg): Make mongodb host configurable
Database().initialize('mongo')

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
        random_secret = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
        docker_id_or_false = main(instance, random_secret)

        if docker_id_or_false:
            # Block until we have all results
            results = ResultsListener('')
            results.run(os.environ['DOCKER_NAME'], 9999, random_secret)

            # Once we reach here it's done
            update_instance(instance, 'done', results.json())
            exitcode = 0
        else:
            # TODO(gpascualg): Check exit code using docker_id_or_false
            print("Instance .autograder.yml is invalid")

except pymongo.errors.ServerSelectionTimeoutError:
    print("Could not reach MongoDB")
except Exception as e:
    print('Instance execution error: {}'.format(e))
    update_instance(instance, 'execution-error')

sys.exit(exitcode)
