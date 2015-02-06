import inspect
import logging
import logging.handlers
import os

ELEVATED_PATH = '/var/log/management/'
LOCAL_PATH = '~/Library/Logs/Management/'

class Logger(logging.Logger):
    """
    This class replaces the regular logging methods (info, error, etc.) with
    methods that can both output information to the console as well as write to
    the logs.
    """
    def __init__(self, name, level=logging.INFO):
        """
        Set up the logger. Generally this will be created from some command
        line arguments.
        
        :param name: the name of the logger
        :type  name: str
        :param level: the level at which to log output
        :type  level: int
        """
        
        # Call the super constructor to build the actual logger.
        super(Logger, self).__init__(name=name, level=level)
    
    def debug(self, message, print_out=True, log=True):
        """
        Log 'message' as debugging output.
        """
        if print_out:
            print("DEBUG: {}".format(message))
        if log:
            super(Logger, self).debug(message)
    
    def info(self, message, print_out=True, log=True):
        """
        Log 'message' as general information.
        """
        if print_out:
            print("{}".format(message))
        if log:
            super(Logger, self).info(message)
    
    def warning(self, message, print_out=True, log=True):
        """
        Log 'message' as a warning (not enough to halt execution, but enough to
        be notable).
        """
        if print_out:
            print("Warning: {}".format(message))
        if log:
            super(Logger, self).warning(message)
        
    warn = warning
        
    def error(self, message, print_out=True, log=True):
        """
        Log 'message' as an error.
        """
        if print_out:
            print("Error: {}".format(message))
        if log:
            super(Logger, self).error(message)
    
    def critical(self, message, print_out=True, log=True):
        """
        Log 'message' as a critical failure. This should probably halt
        execution more often than not.
        """
        if print_out:
            print("CRITICAL: {}".format(message))
        if log:
            super(Logger, self).critical(message)
    
    fatal = critical
    
    def log(self, level, message, print_out=True, log=True):
        """
        Log 'message' with a custom logging level.
        """
        if print_out:
            print("{}".format(message))
        if log:
            super(Logger, self).log(level, message)
        
class FileLogger(Logger):
    """
    A rotating file logger. This will write to a file up until the file contains
    10MB of data. At that point the file will get ".1" appended to its name, and
    a new file will be created in its place. This will keep up to five backup
    files aside from the main file to which output is logged.
    
    The default destination is:
        ELEVATED_PATH/<name>.log
    But if the current user does not have write permissions within that
    directory, instead the destination will be:
        LOCAL_PATH/<name>.log
    
    The default logging severity level is INFO.
    """
    def __init__(self, name=None, level=logging.INFO, path=None):
        """
        Create the rotating file logger. By default, the name will be set based
        on the inspection stack; the level will be set to INFO; and the path
        will be set to the class defaults.
        
        :param name: the name of the logger (e.g. "myprogram")
        :type  name: str
        :param level: the logging level for output
        :type  level: int
        :param path: the directory to put the log file inside
        :type  path: str
        """
        
        # Did they specify a path?
        if path:
            # Make sure that the path ends with a slash. (It should point to a
            # directory, not a file).
            if not path.endswith('/'):
                path += '/'
        else:
            # See if we have privileges to write to the root log file and set
            # the destination accordingly.
            if os.access(os.path.dirname(ELEVATED_PATH[:-1]), os.W_OK):
                path = ELEVATED_PATH
            else:
                path = os.path.expanduser(LOCAL_PATH)
        
        # There needs to be a name. If none is provided, pull it from the
        # inspection stack. (It might not be pretty.)
        if not name:
            name = inspect.stack()[1][3]
        
        # Form the destination. All destinations will end in '.log'.
        destination = os.path.join(path, name)
        if not destination.endswith('.log'):
            destination += '.log'
        
        # Ensure that the necessary directories exist for creating the log file.
        if not os.path.exists(os.path.dirname(destination)):
            try:
                os.makedirs(os.path.dirname(destination))
            except OSError:
                raise ValueError("Invalid path specified: could not create'{}'".format(str(os.path.dirname(destination))))
        
        # Call the super constructor.
        super(FileLogger, self).__init__(name=name, level=level)
        
        # Set up the formatting and handling for this file logger.
        # This will be a rotating file logger, with up to five backup files each
        # weighing up to 10MB. Each line is prefaced with the timestamp, the
        # logging level, and the message. So
        #   logger.info("This is some test output!")
        # would produce a line as:
        #   2015-02-05 17:29:48,289 INFO: This is some test output!
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        handler   = logging.handlers.RotatingFileHandler(destination, maxBytes=10485760, backupCount=5)
        handler.setFormatter(formatter)
        
        self.addHandler(handler)

class StreamLogger(Logger):
    """
    A simple console-output logger. This will not write to a file, but instead
    will output everything to the console.
    
    The default logging severity level is DEBUG.
    """
    def __init__(self, name=None, level=logging.DEBUG):
        """
        Build the stream logger as specified. The default logging level is set
        at DEBUG.
        
        :param level: the level at which to cut off logging
        :type  level: int
        """
        
        # Since this type of logger is only used for console output, the name
        # defaults to whatever method called the logger.
        if not name:
            name = inspect.stack()[1][3]
        
        # Call the super constructor.
        super(StreamLogger, self).__init__(name=name, level=level)
        
        # Set up the formatting and handling for this logger. Each line is
        # prefaced with the timestamp, the logging level, and the message. So
        #   logger.info("This is some test output!")
        # would produce a line as:
        #   2015-02-05 17:29:48,289 INFO: This is some test output!
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        handler   = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        self.addHandler(handler)

def get_logger(name=None, log=False, path=None):
    """
    Returns the appropriate logger depending on the passed-in arguments.
    
    This is particularly useful in conjunction with command-line arguments when
    you won't know for sure what kind of logger the program will need.
    """
    # Are we writing the output to disk? Pick the type of logger based on that.
    if log:
        return FileLogger(name=name, path=path)
    else:
        return StreamLogger(name=name)

def file_logger(name=None, level=logging.INFO, path=None):
    """
    Provides backwards compatibility with previous versions of Management Tools
    (i.e. version < 1.6.0).
    """
    return FileLogger(name=name, level=level, path=path)

def stream_logger(level=logging.DEBUG):
    """
    Provides backwards compatibility with previous versions of Management Tools
    (i.e. version < 1.6.0).
    """
    return StreamLogger(name=None, level=level)
