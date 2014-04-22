import inspect
import logging
import logging.handlers
import os

def file_logger (name=None, level=logging.INFO, path=None):
    '''Returns a rotating file logger.  The default location is:
        /var/log/management/<name>.log
    This does NOT check if the caller has permission to write in this location.

    If you specify a path, be sure that you have permissions there.
    '''

    if not path:
        path = '/var/log/management/'
    else:
        if not path.endswith('/'):
            path += '/'
    if not os.path.exists(path):
        os.makedirs(path)
    if not name:
        name = inspect.stack()[1][3]
    destination = path + name + '.log'

    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler = logging.handlers.RotatingFileHandler(destination, maxBytes=102400, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def stream_logger (level=logging.INFO):
    '''Returns a stream logger.  Useful for quick debugging or something.
    '''

    name = inspect.stack()[1][3]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
