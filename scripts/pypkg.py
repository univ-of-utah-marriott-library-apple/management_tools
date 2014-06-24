#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

options = {}
options['long_name'] = "Python Package Creator"
options['name']      = '_'.join(options['long_name'].lower().split())
options['version']   = '0.1'

from management_tools import loggers

def main(path, identifier, name, python):
    if not os.path.isdir(path):
        raise ValueError("Invalid path specified: " + str(path))
    if path.endswith('/'):
        path = path[:-1]
    logger.info("Using path: " + str(path))
    if not identifier:
        raise RuntimeError("Must provide a valid identifier (e.g. com.apple.Safari)")
    logger.info("Using identifier: " + str(identifier))
    if not os.path.isfile(python):
        logger.error("Invalid Python executable given: " + str(python))
        python = subprocess.check_output(['/usr/bin/which', 'python']).strip('\n')
    logger.info("Using Python executable: " + str(python))
    with ChDir(path):
        logger.info("Changed directory to: " + str(path))
        if not os.path.isfile('./setup.py'):
            raise ValueError("You must use Python's 'setup.py' system.")

        proj_name = subprocess.check_output(
            [python, 'setup.py', '--name'],
            stderr=open(os.devnull, 'w')
        ).strip('\n')
        logger.info("Using project name: " + str(proj_name))
        version = subprocess.check_output(
            [python, 'setup.py', '--version'],
            stderr=open(os.devnull, 'w')
        ).strip('\n')
        if not version:
            logger.error("No version information available.")
        else:
            logger.info("Using version: " + str(version))

        # Find all pre-existing files.
        pre = []
        if os.path.isdir('./pypkg'):
            pre = os.listdir('./pypkg')

        logger.info("Removing all old files in " + os.path.basename(path) + "/pypkg.")
        try:
            for item in pre:
                subprocess.check_call(
                    ['rm', '-rf', './pypkg/' + item],
                    stderr=subprocess.STDOUT,
                    stdout=open(os.devnull, 'w')
                )
        except:
            raise RuntimeError("Could not clean directory.")

        # Call setup.py bdist to build the distribution archive.
        logger.info("Building distribution.")
        try:
            subprocess.check_call(
                [python, 'setup.py', 'bdist', '-d', 'pypkg'],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Distribution did not build.")

        # Extract the archive to get at its contents.
        logger.info("Extracting contents to " + os.path.basename(path) + "/pypkg.")
        try:
            archive = ['./pypkg/' + x for x in os.listdir('./pypkg') if x.endswith('.tar.gz')]
            if len(archive) == 1:
                archive = archive[0]
            else:
                raise RuntimeError("Could not identify unique archive.")
            subprocess.check_call(
                ['/usr/bin/tar', 'xzf', archive, '-C', './pypkg'],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Could not extract tar archive.")

        # Find all files post-extraction.
        files = os.listdir('./pypkg')
        files = ['./pypkg/' + x for x in files]

        # Remove the archive file (don't want that in the package).
        logger.info("Removing tar archive.")
        try:
            archive = [x for x in files if x.endswith('.tar.gz')]
            if len(archive) == 1:
                archive = archive[0]
            else:
                raise RuntimeError("Could not identify unique archive.")
            os.remove(archive)
        except:
            raise RuntimeError("Could not remove tar archive.")

        # Create a manifest of all files and subdirectories.
        manifest = []
        for path, subdirs, files in os.walk('./pypkg'):
            for subdir in subdirs:
                manifest.append(os.path.join(path, subdir))
            for file in files:
                manifest.append(os.path.join(path, file))

        manifest.sort(key=lambda s: s.lower())
        with open('./pypkg/uninstall.sh', 'w') as f:
            f.write("#!/bin/bash" + '\n')
            f.write("UNINSTALL_FROM=\"/\"" + '\n')
            f.write("cd $UNINSTALL_FROM" + '\n')
            f.write('\n')
            for item in sorted(manifest, reverse=True):
                if os.path.isdir(item):
                    f.write(
                        'rmdir ' + item.replace('/pypkg/', '/') + '/\n'
                    )
                else:
                    f.write(
                        'rm ' + item.replace('/pypkg/', '/') + '\n'
                    )

        # Format the file name.
        name = name.replace('#NAME', proj_name).replace('#VERSION', version)
        if not name.endswith('.pkg'):
            name += '.pkg'
        logger.info("Using file name: " + name)

        # Create the .pkg file.
        logger.info("Building package.")
        try:
            subprocess.check_call(
                [
                    '/usr/bin/pkgbuild',
                    '--identifier', identifier,
                    '--root', './pypkg',
                    './pypkg/{}'.format(name)
                ],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Could not build package.")

        # Remove everything else in the directory.
        logger.info("Cleaning up.")
        try:
            for item in sorted(manifest, reverse=True) + ['./pypkg/uninstall.sh']:
                subprocess.check_call(
                    ['rm', '-rf', item],
                    stderr=subprocess.STDOUT,
                    stdout=open(os.devnull, 'w')
                )
        except:
            raise RuntimeError("Could not clean directory.")
    logger.info("Done. Package created at pypkg/{}".format(name))

class ChDir:
    '''Changes directories to the new path and retains the old directory.

    Use this in a 'with' statement for the best effect:

    # If we start in oldPath:
    os.getcwd()
    # returns oldPath
    with ChDir(newPath):
        os.getcwd()
        # returns newPath
    os.getcwd()
    # returns oldPath
    '''

    def __init__(self, new_path):
        self.saved_path = os.getcwd()
        os.chdir(new_path)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.saved_path)

def setup_logger():
    '''Creates the logger to be used throughout.'''

    global logger
    logger = loggers.file_logger(options['name'])

def version():
    '''Prints the version information.'''

    print("{name}, version {version}\n".format(name=options['long_name'],
                                               version=options['version']))

def usage(short=False):
    '''Prints usage information.'''

    if not short:
        version()


class ArgumentParser(argparse.ArgumentParser):
    '''I like my own style of error-handling, thank you.'''

    def error(self, message):
        print("Error: {}\n".format(message))
        usage(short=True)
        self.exit(2)

if __name__ == '__main__':
    setup_logger()
    parser = ArgumentParser(add_help=False)
    parser.add_argument('identifier', nargs='?')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('path', nargs='?')
    parser.add_argument('--name', default="#NAME [#VERSION]")
    parser.add_argument('--python',
                        default=subprocess.check_output(['/usr/bin/which',
                                                        'python']).strip('\n'))
    args = parser.parse_args()

    if not args.path:
        args.path = os.getcwd()

    if args.path.endswith('setup.py'):
        args.path = os.path.dirname(os.path.abspath(args.path))

    if args.help:
        usage()
    elif args.version:
        version()
    else:
        if not args.identifier:
            print("Error: must specify an identifier.")
            usage(short=True)
            sys.exit(2)
        try:
            main(args.path, args.identifier, args.name, args.python)
        except:
            logger.error(sys.exc_info()[1].message)
            sys.exit(5)
