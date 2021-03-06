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
    parser.add_argument('--organization', type=str, help='Target Github organization', required=True)
    parser.add_argument('--branch', type=str, help='Branch on which tests are triggered', required=True)
    parser.add_argument('--max-per-day', type=int, help='Maximum amount of tries per day', required=True)
    parser.add_argument('--testset', type=str, help='What to execute in the server', required=True)
    parser.add_argument('--language', type=str, help='Agent to run tests in', required=True)
    parser.add_argument('--default', action='store_true', help='Execute default routine for this tests')
    parser.add_argument('--python-scriptify', action='store_true', help='Converts notebooks to importable python files')
    parser.add_argument('--python-importable', action='store_true', help='The source folder contains importable python files (or converted notebooks)')
    args = parser.parse_args()

    Database.initialize(args.mongo_host)

    try:
        data = {
            'branch': args.branch,
            'checksum': Database().get_organization_config_by_name(args.organization)['secret'],
            'testset': args.testset,
            'language': args.language,
            'max_per_day': args.max_per_day,
            'default': args.default,
            'version': 3,
            'python': {
                'scriptify': args.python_scriptify,
                'importable': args.python_importable
            }
        }
        
        serialized_contents = yaml.dump(data, encoding='utf-8')
        data['checksum'] = hashlib.sha256(serialized_contents).hexdigest()
        yaml.dump(data, sys.stdout, default_flow_style=False)
        return 0
    except:
        return 2

sys.exit(main())
