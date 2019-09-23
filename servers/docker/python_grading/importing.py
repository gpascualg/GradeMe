from .get_rabit import get_rabbit_sender

import logging
import importlib


import_errors = []
user_modules = []

def notify_import_error(module, error_message):
    # Notify of import errors only one!
    if all(x != module for x in import_errors):
        get_rabbit_sender().import_error(module=module, error=error_message)

        logger = logging.getLogger('grade-me')
        logger.info('[FAILED] Importing {}'.format(module).ljust(100))
        logger.info('\t> {}'.format(error_message))
        logger.info('-'*100)

        import_errors.append(module)

def module_import(module):
    try:
        module = importlib.import_module(module)
        module = importlib.reload(module)
        user_modules.append(module)
        # TODO: Assert OK!
        return module
    except Exception as e:
        notify_import_error(module, repr(e))
        return None
