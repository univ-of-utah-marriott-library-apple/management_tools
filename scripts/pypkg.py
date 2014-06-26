#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

options = {}
options['long_name'] = "Python Package Creator"
options['name']      = "pypkg.py"
options['version']   = '1.3'

from management_tools import loggers

def main(path, identifier, name, version, python, destination, clean, image):
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
        if not version:
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
        if os.path.isdir(destination):
            logger.info("Removing all old files in " + os.path.basename(path) + destination[1:])
            pre = os.listdir(destination)
            try:
                for item in pre:
                    subprocess.check_call(
                        ['rm', '-rf', destination + item],
                        stderr=subprocess.STDOUT,
                        stdout=open(os.devnull, 'w')
                    )
            except:
                raise RuntimeError("Could not clean directory.")

        # Call setup.py bdist to build the distribution archive.
        logger.info("Building distribution.")
        try:
            subprocess.check_call(
                [python, 'setup.py', 'bdist', '-d', destination],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Distribution did not build.")

        # Extract the archive to get at its contents.
        logger.info("Extracting contents to " + os.path.basename(path) + destination[1:] + '/source')
        try:
            archive = [destination + x for x in os.listdir(destination) if x.endswith('.tar.gz')]
            if len(archive) == 1:
                archive = archive[0]
            else:
                raise RuntimeError("Could not identify unique archive.")
            os.makedirs(destination + '/source')
            subprocess.check_call(
                ['/usr/bin/tar', 'xzf', archive, '-C', destination + '/source'],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Could not extract tar archive.")

        # Find all files post-extraction.
        files = os.listdir(destination)
        files = [destination + x for x in files]

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

        # Format the file name.
        name = name.replace('#NAME', proj_name).replace('#VERSION', version)
        if not name.endswith('.pkg'):
            name += '.pkg'

        # Create the .pkg file.
        logger.info("Building package using file name: " + name)
        try:
            subprocess.check_call(
                [
                    '/usr/bin/pkgbuild',
                    '--identifier', identifier,
                    '--root', destination + '/source',
                    '--version', version,
                    destination + name
                ],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Could not build package.")

        # Create the uninstaller package postinstall script.
        script_dir = destination + '/source/scripts'
        if not os.path.isdir(script_dir):
            os.makedirs(script_dir)
        with open(os.path.join(script_dir, 'postinstall'), 'w') as f:
            f.write('''\
#!/bin/bash
# There is no spoon.
/usr/sbin/pkgutil --forget {identifier}
'''.format(identifier=identifier))
        os.chmod(os.path.join(script_dir, 'postinstall'), 0700)
        uninstaller_name = 'Uninstall ' + name
        logger.info("Building uninstaller using file name: " + uninstaller_name)
        try:
            subprocess.check_call(
                [
                    '/usr/bin/pkgbuild',
                    '--identifier', identifier,
                    '--nopayload',
                    '--scripts', script_dir,
                    destination + uninstaller_name
                ],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Could not build uninstaller package.")

        if clean:
            # Create a manifest of all files and subdirectories.
            manifest = []
            for path, subdirs, files in os.walk(destination + '/source'):
                for subdir in subdirs:
                    manifest.append(os.path.join(path, subdir))
                for file in files:
                    manifest.append(os.path.join(path, file))

            # Sort the manifest without case sensitivity (to preserve proper
            # file hierarchies).
            manifest.sort(key=lambda s: s.lower())
            # Remove everything else in the directory.
            logger.info("Cleaning up.")
            try:
                for item in sorted(manifest, reverse=True):
                    subprocess.check_call(
                        ['rm', '-rf', item],
                        stderr=subprocess.STDOUT,
                        stdout=open(os.devnull, 'w')
                    )
                os.rmdir(destination + '/source')
            except:
                raise RuntimeError("Could not clean directory.")

        if image:
            logger.info("Creating disk image to bundle .pkgs.")
            try:
                pkgs = [x for x in os.listdir(destination)
                        if x.endswith('.pkg')]
                if not os.path.isdir(destination + '/pkgs'):
                    os.makedirs(destination + '/pkgs')
                for pkg in pkgs:
                    os.rename(os.path.join(destination, pkg),
                              os.path.join(destination + '/pkgs', pkg))
                subprocess.check_call(
                    [
                        '/usr/bin/hdiutil',
                        'create',
                        '-srcfolder', destination + '/pkgs',
                        '-format', 'UDRO',
                        '-volname', name[:-4],
                        '-fs', 'HFS+',
                        destination + name[:-4]
                    ],
                    stderr=subprocess.STDOUT,
                    stdout=open(os.devnull, 'w')
                )
                if clean:
                    for pkg in pkgs:
                        os.remove(os.path.join(destination + '/pkgs', pkg))
                    os.rmdir(destination + '/pkgs')
            except:
                raise RuntimeError("Could not produce image of packages.")

    logger.info("Done. Package created.")

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

    print('''\
usage: {name} [-hv] [--name file_name] [--dest destination]
\t[--python python_executable] identifier path

{name} helps you to create .pkg installer packages from Python projects. If your
project uses the standard 'setup.py' mechanism for installation, this script can
produce an easy-to-use installer package from it, as well as an uninstaller for
simple removal. By default, these packages are bundled into a single .dmg file
for easy distribution.

    -h, --help
        Prints this help information.
    -v, --version
        Prints the version information.
    --dirty
        Leaves all files in the destination directory. The .pkg file will be at
        the top level, alongside the other files.
    --no-image
        This will leave the .pkg files intact and will not bundle them into a
        single .dmg file.
        If you want the .pkg files *and* the .dmg, use --dirty. The packages
        will be in the 'pkgs' folder and the source material in 'source'.
    --name file_name
        The resulting .pkg file will have the name 'file_name'. There are two
        variables you can use in this naming scheme:
            '#NAME':    the name given by `setup.py --name`
            '#VERSION': the version given by `setup.py --version`
        Default: #NAME [#VERSION]
    --pkg-version version
        This will manually set the version to be used by the package, both for
        the naming and for the package's receipt once installed onto a system.
        Default: whatever is returned by `setup.py --version`
    --dest destination
        The output .pkg file will be created in this subdirectory. Note that
        this directory will be RELATIVE TO THE MAIN PATH. You cannot use an
        absolute path here.
        Default: pkg
    --python python_executable
        Files created by `setup.py bdist` can be in different locations
        depending on which executable of python is used.
        Default: $(/usr/bin/which python)\
'''.format(name=options['name']))

    if not short:
        print('''
'IDENTIFIER'
    All packages must have an identifier. These are generally given in
    reverse-DNS format, such as 'com.apple.Safari'. Your package MUST have an
    identifier declared.

'PATH'
    This is the path to a 'setup.py' file. If no path is given, the current
    directory is scanned for the file and if it is found, the current directory
    is used.

LOGGING
    Logging is automatic and is written to file at:
        /var/log/management/python_package_creator.log

UNINSTALLER
    Packages created with pypkg.py will come with an "installer package" that
    will remove the contents of the actually installer. By default, this package
    will be named "Uninstall (name)", where (name) is the name of the real
    package.

    The uninstaller is a payload-free package that shares the identifier
    with the original package, thus replacing everything with nothing. It also
    executes a postinstallation script to forget the original package in the
    receipts database, effectively removing all traces of the original package.

    NOTE that files created as a by-product of running whatever was installed
    with the original package WILL REMAIN. This only removes the contents of the
    installed package itself.\
''')

class ArgumentParser(argparse.ArgumentParser):
    '''I like my own style of error-handling, thank you.'''

    def error(self, message):
        print("Error: {}\n".format(message))
        usage(short=True)
        self.exit(2)

if __name__ == '__main__':
    setup_logger()
    parser = ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('--dirty', action='store_true')
    parser.add_argument('--no-image', action='store_true')
    parser.add_argument('--name', default="#NAME [#VERSION]")
    parser.add_argument('--pkg-version')
    parser.add_argument('--dest', default='./pypkg/')
    parser.add_argument('--python',
                        default=subprocess.check_output(['/usr/bin/which',
                                                        'python']).strip('\n'))
    parser.add_argument('identifier', nargs='?')
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()

    if not args.path:
        args.path = os.getcwd()

    if args.path.endswith('setup.py'):
        args.path = os.path.dirname(os.path.abspath(args.path))

    if not args.dest.startswith('./'):
        args.dest = './' + args.dest
    if not args.dest.endswith('/'):
        args.dest += '/'

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
            main(
                path        = args.path,
                identifier  = args.identifier,
                name        = args.name,
                version     = args.pkg_version,
                python      = args.python,
                destination = args.dest,
                clean       = not args.dirty,
                image       = not args.no_image
            )
        except:
            logger.error(sys.exc_info()[0].__name__ + ": " + sys.exc_info()[1].message)
            sys.exit(5)
