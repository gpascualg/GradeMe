import argparse
import unittest
import logging
import atexit
import os
import sys
import tempfile

from .docker import MessageSender
from .utils.privilegies import drop_privileges


def send_end(client):
    client.end()

def setup(queue):
    # Results
    # TODO(gpascualg): Retry connection, it will probably fail at first
    client = MessageSender('rabbit', queue)

    # Logging
    logger = logging.getLogger('grade-me')
    log_formatter = logging.Formatter("%(message)s")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    atexit.register(lambda: send_end(client))

    return logger, client

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--queue', required=True)
    args = parser.parse_args()

    # Setup logger and client
    _, client = setup(args.queue)

    # Load tests
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUsing = None
    exit_code = 0
    try:
        testsuite = test_loader.discover('/tests/_/unittest/')

        # Drop privilegies (so /tests is no longer readable)
        drop_privileges()

        # Run tests
        try:
            unittest.TextTestRunner(verbosity=3).run(testsuite)
        except:
            exit_code = 2
    except:
        exit_code = 1

    # Make sure we close connection
    client.end()
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
