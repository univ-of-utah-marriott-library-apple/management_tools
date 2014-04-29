#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

# Check that the logging imports properly.
try:
    from helpful_tools import loggers
except ImportError, e:
    print "You need the 'Helpful Tools' module to be installed first."
    print "https://github.com/univ-of-utah-marriott-library-apple/helpful_tools"
    print
    print "You can use the '-n' switch to ignore this."
    sys.exit(3)

class ChDir:
    def __init__(self, newPath):
        self.savedPath = os.getcwd()
        os.chdir(newPath)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.savedPath)

def set_globals ():
    '''Global options are set here.
    '''

    global options
    options = {}
    options['long_name'] = 'Python Executable Bundler'
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = '1.1'

def setup_logger ():
    '''Creates the logger to be used throughout.

    If it was not specified not to create a log, the log will be created in either
    the default location (as per helpful_tools) or a specified location.

    Otherwise, the logger will just be console output.
    '''

    global logger
    if options['log']:
        # A logger!
        if not options['log_dest']:
            if os.access('/var/log', os.W_OK):
                logger = loggers.file_logger(options['name'])
            else:
                logger = loggers.file_logger(options['name'], path=os.path.expanduser('~/.logs'))
        else:
            logger = loggers.file_logger(options['name'], path=options['log_dest'])
    else:
        # A dummy logger.  It won't record anything to file.
        logger = loggers.stream_logger(1)

def parse_options ():
    parser = argparse.ArgumentParser(description="Bundles groups of Python files together into a single executable.")

    parser.add_argument('-v', '--version', action='version', version=options['long_name'] + ' ' + options['version'], help="Display version information.")
    parser.add_argument('-n', '--no-log', action='store_true', help="Don't write logs to file.")
    parser.add_argument('-l', '--log', help="Set a manual logging directory to LOG.")
    parser.add_argument('-i', '--input', default='', help="The input DIRECTORY containing the files to be bundled.")
    parser.add_argument('-o', '--output', default='', help="The output FILE name to use for the executable.")
    args = parser.parse_args()

    options['input'] = args.input
    options['output'] = args.output
    options['log'] = not args.no_log
    options['log_dest'] = args.log

def main ():
    set_globals()
    parse_options()
    setup_logger()

    # Proper formatting for the input.
    if not options['input']:
        options['input'] = './'
    else:
        options['input'] = os.path.expanduser(options['input'])
        if not os.path.isdir(options['input']):
            logger.error("You must specify a directory for input.")
            sys.exit(5)
    options['input'] = os.path.abspath(options['input'])
    if not options['input'].endswith('/'):
        options['input'] += '/'
    if not os.path.isfile(options['input'] + '__main__.py'):
        logger.error("You must have a '__main__.py' file in the input directory.")
        sys.exit(5)

    # Proper formatting for the output.
    if not options['output']:
        options['output'] = options['input'] + os.path.basename(os.path.dirname(options['input']))
    else:
        options['output'] = os.path.abspath(os.path.expanduser(options['output']))
        if not os.path.isdir(os.path.dirname(options['output'])):
            logger.error("You must specify a filename with a valid pre-existing path.")
            sys.exit(5)
    if not os.access(os.path.dirname(options['output']), os.W_OK):
        logger.error("You do not have permission to save to: " + options['output'])
        sys.exit(5)

    logger.info("Bundling Python files in '" + options['input'] + "' to '" + options['output'] + "'")

    # Create the .zip file.
    # The 'zip' command will make everything relative, so we've gotta cd there.
    with ChDir(options['input']) as c:
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
        try:
            subprocess.call(['zip', options['output'] + '.zip'] + files)
        except:
            logger.error("There was an issue with zipping.")
            sys.exit(10)

    # Create the bundled file.
    with open(options['output'], 'w') as outfile:
        echo = subprocess.Popen(['echo', r'#!/usr/bin/env python'], stdout=subprocess.PIPE)
        subprocess.call(['cat', '-', options['output'] + '.zip'], stdin=echo.stdout, stdout=outfile)

    logger.info("Cleaning up...")

    # Make it executable and delete the .zip.
    os.chmod(options['output'], 0755)
    os.remove(options['output'] + '.zip')

    logger.info("Done!  Bundled executable at '" + options['output'] + "'")

if __name__ == "__main__":
    main()
