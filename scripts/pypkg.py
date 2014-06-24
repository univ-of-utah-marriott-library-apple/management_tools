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

def main(path, identifier, name, python, destination, clean):
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
        logger.info("Extracting contents to " + os.path.basename(path) + destination[1:])
        try:
            archive = [destination + x for x in os.listdir(destination) if x.endswith('.tar.gz')]
            if len(archive) == 1:
                archive = archive[0]
            else:
                raise RuntimeError("Could not identify unique archive.")
            subprocess.check_call(
                ['/usr/bin/tar', 'xzf', archive, '-C', destination],
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

        # Create ('touch') the uninstallation file.
        if not os.path.isdir(destination + '/usr/local/bin'):
            os.makedirs(destination + '/usr/local/bin')
        uninstall_name = (
            destination +
            '/usr/local/bin/uninstall-' +
            proj_name +
            ' ' +
            version +
            '.sh'
        )
        uninstall_name = uninstall_name.lower().replace(' ', '-')
        with open(uninstall_name, 'w'):
            os.utime(uninstall_name, None)

        # Create a manifest of all files and subdirectories.
        manifest = []
        for path, subdirs, files in os.walk(destination):
            for subdir in subdirs:
                manifest.append(os.path.join(path, subdir))
            for file in files:
                manifest.append(os.path.join(path, file))

        # Sort the manifest without case sensitivity (to preserve proper file
        # hierarchies).
        manifest.sort(key=lambda s: s.lower())

        # Create the uninstallation script for this package.
        with open(uninstall_name, 'w') as f:
            f.write('''\
#!/bin/bash

# This script will remove all files installed with {proj_name} v. {version}
# Requires root permissions.
if [ "$(id -u)" != "0" ]; then
    echo "Must be root to run this script!"
    exit 1
fi

UNINSTALL_FROM=$(/usr/sbin/pkgutil --info {identifier} 2>/dev/null | grep volume | awk '{{ print substr($0, index($0,$2)) }}')

if [ "$UNINSTALL_FROM" == "" ]; then
    echo "Could not find a package receipt for {identifier}."
    echo "Maybe it's not installed?"
    exit 2
fi

echo "The following files will be removed: "

'''.format(proj_name=proj_name, version=version, identifier=identifier))

            # f.write("#!/bin/bash\n\n")
            # f.write("# This script will remove all files installed with " + proj_name + " v" + version + ".\n")
            # f.write("UNINSTALL_FROM=$(/usr/sbin/pkgutil --info " + identifier + " | grep volume | awk '{ print substr($0, index($0,$2)) }')\n")
            # f.write('cd "$UNINSTALL_FROM"\n')
            # f.write('echo The following files will be removed:\n')
            for item in sorted(manifest, reverse=True):
                if os.path.isdir(item):
                    f.write(
                        "echo \"  " + item.replace(destination, '${UNINSTALL_FROM}') + '/\"\n'
                    )
                else:
                    f.write(
                        "echo \"  " + item.replace(destination, '${UNINSTALL_FROM}') + '\"\n'
                    )
            f.write('''
# Query the user for confirmation of removing these files.
echo
echo "NOTE: non-empty directories will *not* be deleted."
echo
read -r -p "Continue with uninstallation? [y/N] " response
case $response in
    [yY][eE][sS]|[yY])
        echo "Performing uninstallation..."
        ;;
    *)
        echo "Canceling uninstallation."
        exit 1
        ;;
esac

# The following performs the removal.
''')
            for item in sorted(manifest, reverse=True):
                if os.path.isdir(item):
                    f.write(
                        'rmdir ' + item.replace(destination, '${UNINSTALL_FROM}') + '/\n'
                    )
                else:
                    f.write(
                        'rm ' + item.replace(destination, '${UNINSTALL_FROM}') + '\n'
                    )
            f.write('''
# Now forget that the package was installed...
echo "Forgetting package {identifier}..."
/usr/sbin/pkgutil --forget {identifier}

# Done!
echo "Uninstallation completed."
'''.format(identifier=identifier))
        os.chmod(uninstall_name, 0755)

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
                    '--root', destination,
                    destination + name
                ],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, 'w')
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Could not build package.")

        if clean:
            # Remove everything else in the directory.
            logger.info("Cleaning up.")
            try:
                for item in sorted(manifest, reverse=True) + [uninstall_name]:
                    subprocess.check_call(
                        ['rm', '-rf', item],
                        stderr=subprocess.STDOUT,
                        stdout=open(os.devnull, 'w')
                    )
            except:
                raise RuntimeError("Could not clean directory.")
    logger.info("Done. Package created at {}".format(os.path.join(destination, name)))

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
usage: {} [-hv] [--name file_name] [--dest destination]
         [--python python_executable] identifier path

    -h, --help
        Prints this help information.
    -v, --version
        Prints the version information.
    --dirty
        Leaves all files in the destination directory. The .pkg file will be at
        the top level, alongside the other files.
    --name file_name
        The resulting .pkg file will have the name 'file_name'. There are two
        variables you can use in this naming scheme:
            '#NAME':    the name given by `setup.py --name`
            '#VERSION': the version given by `setup.py --version`
        Default: #NAME [#VERSION]
    --dest destination
        The output .pkg file will be created in this subdirectory. Note that
        this directory will be RELATIVE TO THE MAIN PATH. You cannot use an
        absolute path here.
        Default: pkg
    --python python_executable
        Files created by `setup.py bdist` can be in different locations
        depending on which executable of python is used.
        Default: $(/usr/bin/which python)\
'''.format(options['name']))

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
        /var/log/management/python_package_creator.log\
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
    parser.add_argument('identifier', nargs='?')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('path', nargs='?')
    parser.add_argument('--name', default="#NAME [#VERSION]")
    parser.add_argument('--dest', default='./pypkg/')
    parser.add_argument('--dirty', action='store_true')
    parser.add_argument('--python',
                        default=subprocess.check_output(['/usr/bin/which',
                                                        'python']).strip('\n'))
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
                python      = args.python,
                destination = args.dest,
                clean       = not args.dirty
            )
        except:
            logger.error(sys.exc_info()[0].__name__ + ": " + sys.exc_info()[1].message)
            sys.exit(5)
