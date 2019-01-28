import yaml
import hashlib
import argparse
import sys
import copy
import shutil


def main(filepath):
    try:
        with open(filepath) as fp:
            try:
                data = yaml.load(fp)
            except:
                return 4

        contents = copy.copy(data)
        contents['checksum'] = 'UpTvPNTP0BmwwwMMxYzNp7wYVC4yQOTPRDHAVCP9'
        serialized_contents = yaml.dump(contents, encoding='utf-8')
        contents['checksum'] = hashlib.sha256(serialized_contents).hexdigest()
        print(contents['checksum'])

        shutil.copyfile(filepath, filepath + '.old')
        with open(filepath, 'w') as fp:
            yaml.dump(contents, fp, encoding='utf-8', default_flow_style=False)

        return 0
    except:
        return 2

parser = argparse.ArgumentParser(description='Options')
parser.add_argument('--yml')
args = parser.parse_args()
sys.exit(main(args.yml))
