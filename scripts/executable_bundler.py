#!/usr/bin/env python

import argparse
import os
import sys

# Check that the logging imports properly.
try:
    from helpful_tools import loggers
except ImportError, e:
    print "You need the 'Helpful Tools' module to be installed first."
    print "https://github.com/univ-of-utah-marriott-library-apple/helpful_tools"
    print
    print "You can use the '-n' switch to ignore this:"
    print "  $ location_services_manager -n ..."
    sys.exit(3)

def set_globals ():
    '''Global options are set here.
    '''

    global options
    options = {}
    options['long_name'] = 'Python Executable Bundler'
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = '1.0'

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
            logger = loggers.file_logger(options['name'])
        else:
            logger = loggers.file_logger(options['name'], path=options['log_dest'])
    else:
        # A dummy logger.  It won't record anything to file.
        logger = loggers.stream_logger(1)

def parse_options ():
    parser = argparse.ArgumentParser(description="Bundles groups of Python files together into a single executable.")

    parser.add_argument('-i', help="The input directory containing the files to be bundled.")
    parser.add_argument('-o', help="The output file name to use.")
    parser.add_argument('-v', '--version', action='version', version=options['long_name'] + ' ' + options['version'], help="Display version information.")
    parser.add_argument('-l', '--log', help="Set a manual logging location.")
    parser.add_argument('-n', '--no-log', action='store_true', help="Don't write logs to file.")
    args = parser.parse_args()

    options['log'] = not args.no_log
    options['log_dest'] = args.log

def main ():
    parse_options()

if __name__ == "__main__":
    main()
