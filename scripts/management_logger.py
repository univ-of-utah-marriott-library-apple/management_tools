#!/usr/bin/env python

import argparse
import os
import sys

from management_tools import loggers

def main ():
    '''Parses the options supplied on the command line and writes to a log.

    The first item is assumed to be the name of the log to write to in the path.
    Ther est of the arguments are joined as the message for the log entry.
    '''

    parser = argparse.ArgumentParser(prog='Management Logger',
                                     description="Used to output information to a log.  The first word is the name of the log, and the rest is the message.")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.2')
    parser.add_argument('-p', '--path',
                        help="A different directory to put the log file in.",
                        default='')
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

    logger = loggers.file_logger(name=args.name, level=-5, path=args.path)
    message = ' '.join(args.message)

    logger.log(args.level, message)

if __name__ == "__main__":
    main()
