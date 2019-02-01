import os
import sys
import yaml
import json
import hashlib
import subprocess
import tempfile
import shutil
import copy
import argparse
import datetime

from pymongo import MongoClient
from distutils.dir_util import copy_tree
from os.path import basename

from common.database import Database
from docker.resultscomm import ResultsListener


def update_instance(instance, status, results=[]):
    Database().update_instance(
        instance['_id']['org'], 
        instance['_id']['repo'],
        instance['instances'][0]['hash'],
        instance['instances'][0]['branch'],
        status,
        results
    )

def continue_process(basedir, org, repo, instance, data, mounts):
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

    with tempfile.TemporaryDirectory(dir='/tests') as tmpdirname:
        copy_tree('/tests', tmpdirname)
        
        mount_dir = mounts['/tests'] + tmpdirname[len('/tests'):]
        instance_dir = mounts['/instances'] + '/' + basename(basedir)

        # Create a network

        # Run detached
        docker_id = subprocess.check_output(['docker', 'run', 
            '-d', '-t', '--rm',
            '-v', mount_dir + ':/tests',
            '-v', instance_dir + ':/instance',
            agent_name, data['execute']])

    return docker_id

def main(basedir, secret, org, repo, instance, mounts):
    try:
        with open(basedir + '/code/.autograder.yml') as fp:
            try:
                data = yaml.load(fp)
            except:
                return False

        contents = copy.copy(data)
        contents['checksum'] = secret
        contents = yaml.dump(contents, encoding='utf-8')

        if hashlib.sha256(contents).hexdigest() == data['checksum']:
            return continue_process(basedir, org, repo, instance, data, mounts)
        else:
            return False
    except:
        return False


######################################################################################
# MAIN CODE

# TODO(gpascualg): Make mongodb host configurable
Database().initialize('mongo')

parser = argparse.ArgumentParser(description='Options')
parser.add_argument('--dir')
parser.add_argument('--org')
parser.add_argument('--repo')
parser.add_argument('--org-id')
parser.add_argument('--repo-id')
parser.add_argument('--hash')
parser.add_argument('--branch')
parser.add_argument('--mount')
parser.add_argument('--secret')
args = parser.parse_args()


try:
    mounts = {v: k for k,v in (m.split(':') for m in args.mount.split(';'))}

    instance = Database().get_instance(
        args.org_id,
        args.repo_id,
        args.hash,
        args.branch
    )
    
    if instance is None:
        update_instance(instance, 'org-repo-mismatch')
    else:
        docker_name_or_false = main(args.dir, args.secret, args.org, args.repo, instance, mounts)

        if docker_name_or_false:
            # Block until we have all results
            results = ResultsListener('')
            results.run()

            # Once we reach here it's done
            update_instance(instance, 'done', results.messages)
            exitcode = 0

            # TODO(gpascualg): Check exit code using docker_name_or_false
except:
    update_instance(instance, 'execution-error')

shutil.rmtree(args.dir)
sys.exit(exitcode)
