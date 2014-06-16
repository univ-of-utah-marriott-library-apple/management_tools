import inspect
import logging
import logging.handlers
import os

ELEVATED_PATH = '/var/log/management/'
LOCAL_PATH = '~/Library/Logs/Management/'

def file_logger (name=None, level=logging.INFO, path=None):
    '''Returns a rotating file logger.  The default location is:
        ELEVATED_PATH/<name>.log
    If the current user does not have write access to this location, instead
    the logs will be written to:
        LOCAL_PATH/<name>.log
    '''

    # Get the path.
    if not path:
        # If no path is specified, provide the default.
        if os.access(os.path.dirname(ELEVATED_PATH[:-1]), os.W_OK):
            path = ELEVATED_PATH
        else:
            path = os.path.expanduser(LOCAL_PATH)
    else:
        # If a path was specified, make sure it is formatted properly.
        if not path.endswith('/'):
            path += '/'

    # If no name was specified, use the name of the module that called this.
    if not name:
        name = inspect.stack()[1][3]

    # Join the path to the name and make sure it ends with '.log'.
    destination = os.path.join(path, name)
    if not destination.endswith('.log'):
        destination += '.log'

    # If the path doesn't exist, attempt to create the directory structure.
    if not os.path.exists(os.path.dirname(destination)):
        try:
            os.makedirs(os.path.dirname(destination))
        except OSError:
            raise ValueError("Invalid path specified: could not create '" + str(os.path.dirname(destination)) + "'")

    # Set up the formatters and handlers for the logger.
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler = logging.handlers.RotatingFileHandler(destination, maxBytes=10485760, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def stream_logger (level=logging.INFO):
    '''Returns a stream logger.  Useful for quick debugging or something.
    '''

    # Set the name to that of the module that called this.
    name = inspect.stack()[1][3]

    # Set up the formatters and handlers for the logger.
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
