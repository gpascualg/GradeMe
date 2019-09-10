import yaml
import hashlib
import argparse
import sys
import copy
import shutil

from servers.common.database import Database


def main():
    # New organizations to use
    parser = argparse.ArgumentParser(description='Classroom AutoGrader')
    parser.add_argument('--mongo-host', default='mongo', help='MongoDB hostname')
    parser.add_argument('--branch', type=str, help='Branch on which tests are triggered', required=True)
    parser.add_argument('--yml', help='Destination for the yml file', required=True)
    parser.add_argument('--branch', type=str, help='Branch on which tests are triggered', required=True)
    parser.add_argument('--max-per-day', type=int, help='Maximum amount of tries per day', required=True)
    parser.add_argument('--execute', type=str, help='What to execute in the server', required=True)
    parser.add_argument('--language', type=str, help='Agent to run tests in', required=True)
    args = parser.parse_args()

    Database.initialize(args.mongo_host)

    try:
        data = {
            'branch': args.branch,
            'checksum': Database().get_organization_config(args.organization)['secret'],
            'execute': args.execute,
            'language': args.language,
            'max_per_day': args.max_per_day,
            'version': 3
        }
        
        serialized_contents = yaml.dump(data, encoding='utf-8')
        data['checksum'] = hashlib.sha256(serialized_contents).hexdigest()
        print(data['checksum'])

        shutil.copyfile(filepath, filepath + '.old')
        with open(filepath, 'w') as fp:
            yaml.dump(data, fp, encoding='utf-8', default_flow_style=False)

        return 0
    except:
        return 2

parser = argparse.ArgumentParser(description='Options')
parser.add_argument('--yml')
args = parser.parse_args()
sys.exit(main(args.yml))
