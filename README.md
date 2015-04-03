Management Tools
================

A collection of Python scripts and packages to simplify OS X management.

## Contents

* [Download](#download) - get the .dmg
* [System Requirements](#system-requirements) - what you need
* [Contact](#contact) - how to reach us
* [Uninstall](#uninstall) - removal of Management Tools
* [Modules](#modules)
  * [app_info](#app_info) - access applications' information
  * [fs_analysis](#fs_analysis) - analyze mounted filesystems
  * [loggers](#loggers) - output data to logs
  * [plist_editor](#plist_editor) - modify plists properly
* [Scripts](#scripts)
  * [App Lookup](#app-lookup) - lookup an application's information
  * [Python Executable Bundler](#python-executable-bundler) - bundle a Python project into a standalone script
  * [Management Logger](#management-logger) - log data easily
  * [Management Email](#management-email) - simple email sender
  * [Python Package Creator](#python-package-creator) - an automated .pkg creator for Python projects using 'setup.py'
* [Update History](#update-history) - all of the major updates to Management Tools

## Download

[Download the latest installer here!](../../releases/)

## System Requirements

Management Tools has been tested to work with Mac OS X 10.8 through 10.10, and uses Python version 2.7.

## Contact

If you have any comments, questions, or other input, either [file an issue](../../issues) or [send an email to us](mailto:mlib-its-mac-github@lists.utah.edu). Thanks!

## Uninstall

To remove Management Tools from your system, download the .dmg and run the "Uninstall Management Tools" package to uninstall it. (Note that it will say "Installation Successful" but don't believe it - it will only remove files.)

## Get Current Version

If you want to find your currently-installed Management Tools version, simply do:

```bash
$ python -m management_tools.__init__
Management Tools, version: x.y.z
```

## Modules

In Python, modules are designed to be imported into another project to make your life easier. These can be integrated into your packages by simply using:

```python
from package import module

# Or if you want a particular method from within a module:
from package.module import method

# For example, if we want the app_info module:
from management_tools import app_info

# Or just the AppInfo class:
from management_tools.app_info import AppInfo
```

### app_info

This module contains a class, `AppInfo`, which can be used to get information about applications. Generally, you will do:

```python
from management_tools.app_info import AppInfo
```

Then the class can be used to get information. It requires an argument upon creation which should tell it something identifiable about the application, such as a valid short name, a bundle path, or a bundle identifier. Once it has been created, you can access various useful bits about the application.

```python
app = AppInfo('application name')

app.path  # This reports the /path/to/the/application.app
app.plist # Returns a PlistEditor of the application's informational property
          # list, generally located at <app.path>/Contents/Info.plist
app.bid   # The application's bundle identifier
app.name  # The full name of the application
```

So, for example, if we use `com.apple.Safari` as our application (this is in interactive mode):

```python
>>> from management_tools.app_info import AppInfo
>>> app = AppInfo('com.apple.Safari')
>>> app.path
'/Applications/Web Browsers/Safari.app'
>>> app.plist
/Applications/Web Browsers/Safari.app/Contents/Info.plist
>>> app.bid
'com.apple.Safari'
>>> app.name
'Safari'
>>>
```

Alternatively, the information can also be returned more simply for outputting purposes:

```python
>>> from management_tools.app_info import AppInfo
>>> app = AppInfo('safari')
>>> app
Safari
    BID:        com.apple.Safari
    Path:       /Applications/Web Browsers/Safari.app
    Info.plist: /Applications/Web Browsers/Safari.app/Contents/Info.plist
>>>
```

#### Finding Bundle Identifiers Manually

Bundle identifiers are the method Apple uses to manage its TCC databases. The `AppInfo` class is good at finding them, but maybe you want to know more about where to find them yourself (for some reason).

In general, BIDs can be found in an application's `Info.plist` file. If your application is located at `/Applications/MyAwesomeApp.app`, then the plist file will most likely be located at `/Applications/MyAwesomeApp.app/Contents/Info.plist`. Within this plist, you'll need to search for the string corresponding to the key `CFBundleIdentifier`. So we could do:

```
$ defaults read /Applications/MyAwesomeApp.app/Contents/Info CFBundleIdentifier
```

The `CFBundleIdentifier` key is supposed to be included for every application. If it's not there, then the application's developers did something wrong (or maybe they just did something different for a very particular reason).

Brett Terpstra [detailed a shell script to help with looking these up](http://brettterpstra.com/2012/07/31/overthinking-it-fast-bundle-id-retrieval-for-mac-apps/), which I will reproduce here for your convenience:

```bash
# Allows for searching of Bundle IDs by application name
# Written by Brett Terpstra
bid() {
	local shortname location

	# combine all args as regex
	# (and remove ".app" from the end if it exists due to autocomplete)
	shortname=$(echo "${@%%.app}"|sed 's/ /.*/g')
	# if the file is a full match in apps folder, roll with it
	if [ -d "/Applications/$shortname.app" ]; then
		location="/Applications/$shortname.app"
	else # otherwise, start searching
		location=$(mdfind -onlyin /Applications -onlyin ~/Applications -onlyin /Developer/Applications 'kMDItemKind==Application'|awk -F '/' -v re="$shortname" 'tolower($NF) ~ re {print $0}'|head -n1)
	fi
	# No results? Die.
	[[ -z $location || $location = "" ]] && echo "$1 not found, I quit" && return
	# Otherwise, find the bundleid using spotlight metadata
	bundleid=$(mdls -name kMDItemCFBundleIdentifier -r "$location")
	# return the result or an error message
	[[ -z $bundleid || $bundleid = "" ]] && echo "Error getting bundle ID for \"$@\"" || echo "$location: $bundleid"
}
```

If you were to put this in your source file (e.g. `.bash_profile`), you can simply call it as a command and it will search for your application and return both the app's location and its bundle ID:

```
$ bid safari
/Applications/Safari.app: com.apple.Safari
```

### fs_analysis

Sometimes you might want to get information about mounted filesystems. Command line tools such as `df` and `mount` are useful if you're a human, but they leave something to be desired if you write a lot of scripts. Enter `fs_analysis` - a Python module designed to help you gather information on mounted filesystems.

`fs_analysis` has three methods for polling the system about mounted filesystems:
1. `get_responsible_fs(target)` finds which filesystem contains the given file or directory. The return value is the name of the filesystem, such as '/dev/disk0s2'.
2. `get_raw_fs_info(fs_name)` returns the `mount` information for the given filesystem, which will include the mount point and mount options.
3. `get_raw-fs_usage(mount_point)` gives output from `df -P -k $mount_point` (but without the headers that `df` usually puts on the first line).

#### Filesystem

Additionally (and most importantly), `fs_analysis` introduces a `Filesystem` class. To initialize a `Filesystem` object, you must supply the constructor with the raw device name of the filesystem you want it to keep track of. Sometimes you may not know the device name but you might know a file or folder on the specified device, or even the mount point. Here's how I initialize my `Filesystem` objects:

```python
from management_tools import fs_analysis

device_name = fs_analysis.get_responsible_fs('/path/to/target')
fs_object   = fs_analysis.Filesystem(device_name)
```

Objects of this type keep track of various bits of information regarding a particular filesystem:

| Property Name | Description                                                                                                                 |
|---------------|-----------------------------------------------------------------------------------------------------------------------------|
| name          | The raw device name for the filesystem (e.g. `/dev/disk2s1`).                                                               |
| mount_point   | Where the device is mounted (e.g. `/Volumes/MyFavoriteDisk`).                                                               |
| type          | What type of filesystem it is (HFS, NTFS, FAT, etc.).                                                                       |
| kblocks       | Total number of 1024-byte blocks on the device.                                                                             |
| kblocks_used  | Number of 1024-byte blocks that are used.                                                                                   |
| kblocks_free  | Number of 1024-byte blocks available for use. (`kblocks_free + kblocks_used = kblocks`)                                     |
| bytes         | Total number of bytes on the device (computed as `1024 x kblocks`).                                                         |
| bytes_used    | Number of bytes that are used (computed as `1024 x kblocks_used`).                                                          |
| bytes_free    | Number of bytes remaining unused (computed as `1024 x kblocks_free`).                                                       |
| capacity      | The percentage of space that has been used. (This is a rounded integer computed as `kblocks_used / kblocks` by the system.) |
| properties    | Any other properties the device may have (e.g. HFS, remote, nosuid, journaled, read-only, etc.).                            |

Additionally, the `Filesystem` object's data can be refreshed by using the `update()` method. This will cause the object to re-poll the system and gather new usage data.

Note that the properties are otherwise designed to be immutable, since they are descriptions of filesystems and not values for you to modify directly. I did this to ensure greater safety when using these objects. (What I mean is: you can't do `fs_object.bytes = 100` or something like that.)

### loggers

In our deployment, we like to log stuff. Logging things is a useful way to record information for later perusal, which can be quite helpful. Since I kept having to copy/paste our logging mechanisms from script to script, I just created a dedicated logging module.

There are three classes in this module: the generic `Logger`, and the more specific `FileLogger` and `StreamLogger` (which both extend the base `Logger` class). `FileLogger` is used to output information to a file and/or the console, and `StreamLogger` only outputs information to the console.

#### FileLogger

The `FileLogger` class is built on a rotating file handler. The default is set to keep five backup files (so up to six files total) that are 10MB each. This logger can also output information to the console, allowing an easy way to output information and control verbosity while logging everything. The default log location is either `/var/log/management/` for administrators with write access to that directory, or else `~/Library/Logs/Management/` for non-privileged users.

##### Example Usage

```
>>> from management_tools.loggers import FileLogger
>>> logger = FileLogger('test')
>>> logger.info("This is regular information.")
INFO: This is regular information.
>>> logger.debug("Super verbose (not logged by default, unless the level is changed).")
>>> logger.error("This is an error.")
ERROR: This is an error.
>>> logger.fatal("Danger, Will Robinson! Danger!")
CRITICAL: Danger, Will Robinson! Danger!
>>>
```

If we then go and look in (assuming this was run unprivileged) `~/Library/Logs/Management/test.log`:

```
2015-02-26 10:04:12,238 INFO: This is regular information.
2015-02-26 10:04:22,614 ERROR: This is an error.
2015-02-26 10:04:26,206 CRITICAL: Danger, Will Robinson! Danger!
```

There is also a `file_logger` method to provide backwards compatibility with scripts written to use Management Tools versions less than 1.6.0:

```python
def file_logger(name=None, level=INFO, path=None):
```

#### StreamLogger

`StreamLogger` is used in situations where you want to provide a logger, but you may not want to write the data to file. I use this in scripts where I give the user the option of enabling logging through a command line flag. If they specify that they do not want information logged to a file, a `StreamLogger` is used in place of the `FileLogger`.

By default, `StreamLogger` does *not* have the `print_default` field set to `True`. Instead, it redirects the actual log messages (with timestamps et al) and prints those to the console.

As with the `FileLogger`, there is also a `stream_logger` method to provide backwards compatibility with scripts written to use Management Tools versions less than 1.6.0:

```python
def stream_logger(level=DEBUG):
```

#### General Logger Specifics

To easily get a logger with the default specifications, the module provides a method for each logger: `FileLogger` has `file_logger()`, and `StreamLogger` has `stream_logger()`. Simply do:

```
>>> from management_tools.loggers import stream_logger
>>> logger = stream_logger()
>>> logger.info("Time is an illusion. Lunchtime doubly so.")
2015-02-26 12:11:50,837 INFO: Time is an illusion. Lunchtime doubly so.
>>>
```

In most of my scripts, I allow the user to specify whether log events will be outputted to file, and if they are where to put that file. To make my life easier (and possibly yours too!), there is now a method to allow the programmatic generation of loggers appropriate to these options: `get_logger()`.

```python
def get_logger(name=None, log=False, level=INFO, path=None):
```

A simple usage example would be:

```
>>> from management_tools.loggers import get_logger
>>> logger = get_logger(name='fjords', log=True, path='/zz9/earth/norway')
>>>
```

This would return a `FileLogger`, set to generate a file at `/zz9/earth/norway/fjords.log`. If `log` were set to `False`, the file would not be used.

##### Logging Levels and Methods

There are six different logging levels supported (all of them except for `VERBOSE` copy their values from the standard `logging` module):

| Logging Level | Default Value           |
|---------------|-------------------------|
| CRITICAL      | 50 (`logging.CRITICAL`) |
| ERROR         | 40 (`logging.ERROR`)    |
| WARNING       | 30 (`logging.WARNING`)  |
| INFO          | 20 (`logging.INFO`)     |
| DEBUG         | 10 (`logging.DEBUG`)    |
| VERBOSE       | 5                       |

Each of these levels of logging also has a corresponding method for generating logging output. Assuming you have a `Logger` object named `logger`:

| Method            | Purpose                                            |
|-------------------|----------------------------------------------------|
| `logger.critical` | Fatal errors that impede program flow.             |
| `logger.error`    | Important errors that may yield undesired results. |
| `logger.warning`  | Issues that are not halting, but not ideal.        |
| `logger.info`     | Regular information.                               |
| `logger.debug`    | Debugging information.                             |
| `logger.verbose`  | Very detailed information.                         |

##### Controlling Output

The console output can be controlled. Each of the logging methods has a signature such as:

```python
def info(self, message, print_out=None, log=None):
```

`print_out` and `log` take booleans for arguments. If you pass `True` to both (the default for `FileLogger`), you get output to both the console (`print_out`) and the logging file (`log`). The defaults can be changed by modifying the logger's `print_default` and `log_default` fields, for example:

```
>>> from management_tools.loggers import FileLogger
>>> logger = FileLogger('test')
>>> logger.info("This must be Thursday. I never could get the hang of Thursdays.")
INFO: This must be Thursday. I never could get the hang of Thursdays.
>>> logger.print_default = False
>>> logger.info("For a moment, nothing happened. Then, after a second or so, nothing continued to happen.")
>>> logger.log_default = False
>>> logger.info("Oh no, not again!")
>>> logger.info("So long, and thanks for all the fish!", print_out=True)
INFO: So long, and thanks for all the fish!
>>>
```

If we then go and look in `~/Library/Logs/Management/test.log` (assuming this was run unprivileged):

```
2015-02-26 11:37:44,394 INFO: This must be Thursday. I never could get the hang of Thursdays.
2015-02-26 11:38:00,347 INFO: For a moment, nothing happened. Then, after a second or so, nothing continued to happen.
```

##### Custom Prompts

When log messages are outputted to the console, they are by default prepended with their logging level name (in all caps). You can override the prompt for each level. Note that this is only for console output and not for the actual log messages.

```
>>> from management_tools import loggers
>>> logger = loggers.StreamLogger('ford', loggers.INFO, True, False)
>>> logger.info("How would you react if I said that I'm not from Guildford at all, but from a small planet somewhere in the vicinity of Betelgeuse?")
INFO: How would you react if I said that I'm not from Guildford at all, but from a small planet somewhere in the vicinity of Betelgeuse?
>>> logger.set_prompt(loggers.INFO, 'Ford: ')
>>> logger.info("The point is that I am now a perfectly safe penguin, and my colleague here is rapidly running out of limbs!")
Ford: The point is that I am now a perfectly safe penguin, and my colleague here is rapidly running out of limbs!
>>>
```

### plist_editor

Many Apple services and applications utilize property list files, usually referred to simply as 'plists'. These files can be modified to contain all kinds of information.

However, *editing* the files can be somewhat of a hassle. Since Mac OS X 10.9 "Mavericks", plist files are periodically cached and then rewritten asynchronously to the disk. What this means is that if you modify a plist with a plaintext editor, **there is no guarantee that the changes will remain permanently**. This is not exactly the ideal way for things to be done.

OS X contains a command called `defaults`. This command provides the necessary mechanism to modify plist files without the asynchronous caching having a negative effect on your work. This `plist_editor` module contains a class, `PlistEditor`, which allows you to modify plist files using this `defaults` command (but without you having to actually make the calls).

```python
from management_tools.plist_editor import PlistEditor

plist = PlistEditor('/path/to/file.plist')
```

## Scripts

The scripts are mostly just simple frontends for using the modules above. For example: perhaps you want to log something, but you don't want to go through the trouble of importing the logger and setting it up. Instead, just use the Management Logger script and it will do the work for you.

### App Lookup

This serves as a quick interface to the `app_info` module. When calling the script, simply supply identifiers for applications and it will return the application's given name, bundle ID, path, and Info.plist path.

```
$ app_lookup.py safari
Safari
    BID:       com.apple.Safari
    Path:      /Applications/Web Browsers/Safari.app
    Info.Plist /Applications/Web Browsers/Safari.app/Contents/Info.plist
```

### Python Executable Bundler

A while ago I learned that Python scripts can be bundled together in standalone 'executables'. I did this manually for a while, and then created this script to automate it.

Effectively what happens is this takes the Pythonic contents of a directory (i.e. all the `.py` files) and compresses them into a zipped structure. A shebang is catted in to the zip and then chmoded to produce an 'executable'. Note that that main entrance point of the script must be named `__main__.py` for this to work properly.

Usage of the script is simple. If you are within the directory of Python files:

```
$ executable_bundler.py -o mybundle
  adding: __main__.py (deflated 71%)
  adding: something.py (deflated 67%)
```

You will then find a file named `mybundle` in the current directory that can be run with:

```
$ ./mybundle
```

This produces the same results as:

```
$ python __main__.py
```

### Management Logger

The Management Logger is an interface for the `file_logger` from above. Calling Management Logger allows you to easily write a log entry to a file quickly and efficiently. Calling the script involves:

```
$ management_logger.py file "This is an entry in my log."
```

This will log the line `"This is an entry in my log."` to a file named `file.log` located in one of two places: either `/var/log/management/` if the calling user has root privileges, or else `~/Library/Logs/Management/`.

### Management Email

Management Email is designed to allow your scripts to send emails easily and with minimal setup. The script has many options available, but generally only a couple of them need to actually be supplied:

| Option                              | Purpose                                                                        |
|-------------------------------------|--------------------------------------------------------------------------------|
| `-h`, `--help`                      | Prints usage instructions.                                                     |
| `-v`, `--version`                   | Prints version information.                                                    |
| `-n`, `--no-log`                    | Prevents logs from being written to file (instead they'll come through stdio). |
| `-l log`, `--log log`               | Uses `log` as the destination for logging output.                              |
| `-f file`, `--file file`            | Attaches `file` to the email as a plaintext document.                          |
| `-u subject`, `--subject subject`   | Places `subject` in the message header.                                        |
| `-s server`, `--smtp-server server` | Send the mail through `server`.                                                |
| `-p port`, `--smtp-port port`       | Connect to the server via port `port`.                                         |
| `-U user`, `--smtp-username user`   | Connect to the server as `user`.                                               |
| `-P pass`, `--smtp-password pass`   | Connect to the server with password `pass`.                                    |
| `-F address`, `--smtp-from address` | Send the mail from `address`.                                                  |
| `-T address`, `--smtp-to address`   | Send the mail to `address`.                                                    |

Additionally, a message can be supplied by itself in a quoted string.

In an effort to simplify administration, many of the options can be set through environment variables. These variables are:

| Variable Name            | Correlating command-line flag |
|--------------------------|-------------------------------|
| `MANAGEMENT_SMTP_SERVER` | `-s`, `--smtp-server`         |
| `MANAGEMENT_SMTP_PORT`   | `-p`, `--smtp-port`           |
| `MANAGEMENT_SMTP_USER`   | `-U`, `--smtp-username`       |
| `MANAGEMENT_SMTP_PASS`   | `-P`, `--smtp-password`       |
| `MANAGEMENT_SMTP_FROM`   | `-F`, `--smtp-from`           |
| `MANAGEMENT_SMTP_TO`     | `-T`, `--smtp-to`             |

Environment variables can easily be set by running a command such as:

```
$ export MANAGEMENT_SMTP_SERVER='mail.example.com'
```

Note that environment variables must be declared using the `export` functionality for the script to be able to pick up on them. It is conceivable to have these set globally, but that is outside the scope of this summary.

### Python Package Creator

The Python Package Creator (also 'PyPkg') will create an OS X-compatible `.pkg` file containing the contents of a Python project. The project *must* use the `setup.py` system, which is documented [here](https://docs.python.org/2/distutils/setupscript.html). If you aren't using this system to manage your Python projects, you may want to consider changing to it.

There are a few options that can be given to the script:

| Option                       | Purpose |
|------------------------------|---------|
| `-h`, `--help`               | Prints usage information. |
| `-v`, `--version`            | Prints version information. |
| `--dirty`                    | Prevents cleanup after the package has been created. |
| `--no-image`                 | Does not produce the `.dmg` file and instead leaves the `.pkg`s in a `pkgs` subfolder. |
| `--name file_name`           | The name of the `.pkg` file will be `file_name`. The special values `#NAME` and `#VERSION` can be used to get the name and version information from `setup.py`. |
| `--pkg-version version`      | Manually sets the version information for the package, both for the name and for the package's receipt once installed. |
| `--dest destination`         | The `.pkg` file will be created at `destination`. Note that this is relative to the path given to the script. |
| `--extras directory`         | The contents of `directory` will be added to the top level of the disk image produced. This is useful for readmes and configuration files. |
| `--sign signature`           | Allows you to digitally sign the package with an identity so that it will be trusted. See [Apple's documentation on code signing](https://developer.apple.com/library/mac/documentation/security/conceptual/CodeSigningGuide/Procedures/Procedures.html). |
| `--python python_executable` | The `setup.py` script will be run using the Python executable at `python_executable`. |

As an example, this Management Tools package (in the [`/pkg/`](pkg) directory) was created by running the following from within the Management Tools directory:

```
$ pypkg.py edu.utah.scl.management-tools ./setup.py --python /usr/bin/python --dest pkg
```

#### Uninstaller

PyPkg automatically produces another `.pkg` file to *uninstall* whatever package you just produced. You can simply double-click it and it will remove the contents of the previously-installed package, and it will also forget that package from the receipts database. This is significantly easier than the previous method of running an uninstallation script from the terminal. By default this uninstallation package will be produced on the same level as the installation package, so you will be able to decide how to distribute them.

## Update History

This is a reverse-chronological list of updates to this project.

| Date       | Version | Update Description                                                                                                             |
|------------|:-------:|--------------------------------------------------------------------------------------------------------------------------------|
| 2015-03-26 | 1.8.1   | Updated `fs_analysis.Filesystem` objects to have `bytes` properties.                                                           |
| 2015-03-20 | 1.8.0   | Introduced `fs_analysis` - simple filesystem information for Python.                                                           |
| 2015-02-26 | 1.7.0   | Significant rewrite of the `loggers` module. Provides greater flexibility and more options in the creation of logger objects.  |
| 2015-02-24 | 1.6.4   | Custom logging prompts.                                                                                                        |
| 2015-02-19 | 1.6.3   | Now you can get the current installed version of Management Tools by doing `python -m management_tools.__init__`!              |
| 2015-02-06 | 1.6.2   | Logging level update (it was broken before).                                                                                   |
| 2015-02-05 | 1.6.1   | Can now set the logging level in `get_logger()` method.                                                                        |
| 2015-02-05 | 1.6.0   | Massive overhaul of `loggers` system. Now there's a `Logger` class that can be used more easily.                               |
| 2014-07-15 | 1.5.13  | PyPkg now supporst an "extras" directory option. Useful for readmes and config files for your package deployments.             |
| 2014-06-26 | 1.5.10  | Signing update. PyPkg supports code developer signatures. Good for deploying.                                                  |
| 2014-06-26 | 1.5.9   | After building the installation and uninstallation packages, PyPkg now wraps them in a disk image.                             |
| 2014-06-26 | 1.5.8   | Removed the uninstallation script and now PyPkg produces real uninstallation packages. Much better.                            |
| 2014-06-25 | 1.5.7   | Adjusted paths that were causing issues.                                                                                       |
| 2014-06-25 | 1.5.6   | Set custom version numbers for packages made with PyPkg.                                                                       |
| 2014-06-24 | 1.5.4   | Can now prevent PyPkg from doing post-clean (leaving files in-place to be perused).                                            |
| 2014-06-24 | 1.5.2   | PyPkg now supports custom installation locations.                                                                              |
| 2014-06-24 | 1.5.1   | New uninstaller script for PyPkg.                                                                                              |
| 2014-06-23 | 1.5.0   | Started on the "Python Package Creator" (`pypkg.py`). Much better than the executable bundler from before.                     |
| 2014-06-16 | 1.4.0   | Added new `management_email.py` script for sending of emails.                                                                  |
| 2014-06-11 | 1.3.2   | Increased the size of log files to 10MB.                                                                                       |
| 2014-05-14 | 1.3.1   | `app_info.py` now finds applications' executable files.                                                                        |
| 2014-05-07 | 1.2.1   | Updated `setup.py` and significant improvements to README documentation.                                                       |
| 2014-05-02 | 1.2     | Changed project name from "Helpful Tools" to "Management Tools". Probably a good move.                                         |
| 2014-04-22 | 0.9     | Began the project as a merge of some in-house tools.                                                                           |
