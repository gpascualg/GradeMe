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


def update_instance(instance, status, results=[]):
    Database().update_instance(
        instance['_id']['org'], 
        instance['_id']['repo'],
        instance['instances'][0]['hash'],
        instance['instances'][0]['branch'],
        status,
        results
    )

def get_organization_config(org):
    return orgs.find(
        {'_id': org},
        {'_id': 0}
    )

def continue_process(basedir, org, repo, instance, data, mounts):
    if 'branch' in data:
        if data['branch'] != instance['_id']['branch']:
            update_instance(instance, 'branch-mismatch')
            print('> Skipped due to branch mismatch')
            return 6

    if 'max_per_day' in data:
        daily_usage = instance['daily_usage']
        current_date = datetime.datetime.now().strftime("%y-%m-%d")
        daily_usage[current_date] = daily_usage.get(current_date, 0) + 1

        if daily_usage[current_date] > data['max_per_day']:
            update_instance(instance, 'out-of-tries')
            print('> No more attempts allowed today')
            return 8

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
        return 5

    with tempfile.TemporaryDirectory(dir='/tests') as tmpdirname:
        copy_tree('/tests', tmpdirname)
        
        mount_dir = mounts['/tests'] + tmpdirname[len('/tests'):]
        instance_dir = mounts['/instances'] + '/' + basename(basedir)

        retcode = subprocess.call(['docker', 'run', '-t', '--rm',
            '-v', mount_dir + ':/tests',
            '-v', instance_dir + ':/instance',
            agent_name, data['execute']])

    return retcode

def main(basedir, secret, org, repo, instance, mounts):
    try:
        with open(basedir + '/code/.autograder.yml') as fp:
            try:
                data = yaml.load(fp)
            except:
                return 4

        contents = copy.copy(data)
        contents['checksum'] = secret
        contents = yaml.dump(contents, encoding='utf-8')

        if hashlib.sha256(contents).hexdigest() == data['checksum']:
            return continue_process(basedir, org, repo, instance, data, mounts)
        else:
            return 3
    except:
        return 2


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
        exitcode = 7
    else:
        exitcode = main(args.dir, args.secret, args.org, args.repo, instance, mounts)

    json_path = os.path.join(args.dir, 'results.json')
    json_results = []
    try:
        with open(json_path) as fp:
            json_results = json.load(fp)
    except:
        pass

    update_instance(instance, 'done', json_results)
except:
    update_instance(instance, 'execution-error')
    exitcode = 1

shutil.rmtree(args.dir)
sys.exit(exitcode)
