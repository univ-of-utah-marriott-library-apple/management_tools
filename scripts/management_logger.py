#!/usr/bin/env python

import argparse
import os
import sys
from management_logging import loggers

def main ():
    '''Parses the options supplied on the command line and writes to a log.

    The first item is assumed to be the name of the log to write to in the path.
    '/var/log/management' is the default for the root user, '~/.logs/' is the
    default for non-privileged users.  The rest of the items are compiled
    together into a single line of text to be written into that log.
    '''

    parser = argparse.ArgumentParser(prog='management_logger',
                                     description='''Used to output information to a log.  The first word is the name of the log, and the rest is the message.
                                     The default location for the root user is /var/log/management/<name>.log.
                                     The default location for other users is ~/.logs/<name>.log.''')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.1')
    parser.add_argument('-p', '--path',
                        help="A different directory to put the log file in.")
    parser.add_argument('-l', '--level',
                        type=int,
                        default=20,
                        help="Specify the logging level.  Lower numbers mean that the logger will record more events (higher numbers are more restrictive).")
    parser.add_argument('name',
                        help="The name of the log file.")
    parser.add_argument('message',
                        nargs='+',
                        help="The stuff to put into the log entry.")
    args = parser.parse_args()

    if not args.path:
        if os.geteuid() == 0:
            args.path = '/var/log/management/'
        else:
            args.path = os.path.expanduser('~/.logs/')

    print "Logging to '" + args.path + args.name + ".log'."

    logger = loggers.file_logger(args.name, level=-5, path=args.path)
    message = ' '.join(args.message)

    logger.log(args.level, message)

if __name__ == "__main__":
    main()
