import logging

# Create a custom logger
logger = logging.getLogger('grademe')

def setup_logger(level):
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('grademe.log')
    c_handler.setLevel(level)
    f_handler.setLevel(level)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
