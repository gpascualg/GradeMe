#!/usr/bin/env python3

import unittest
import logging
import atexit
import os
import tempfile

from docker import MessageSender
from .privilegies improt drop_privileges


def send_end(client):
    client.end()

def setup(host, secret):
    # Results
    # TODO(gpascualg): Retry connection, it will probably fail at first
    client = MessageSender()

    # Logging
    logger = logging.getLogger()
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
    parser.add_argument('--secret', required=True)
    args = parser.parse_args()

    # Setup logger and client
    logger, client = setup(args.host, args.secret)

    # Load tests
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUsing = None
    testsuite = test_loader.discover('/tests/_/unittest/')

    # Drop privilegies (so /tests is no longer readable)
    drop_privileges()

    # Run tests
    unittest.TextTestRunner(stream=fp, verbosity=0).run(testsuite)

if __name__ == '__main__':
    main()
