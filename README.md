Management Tools
================

A collection of Python scripts and packages to simplify OS X management.

## Contents

* [Download](#download) - get the .pkg
* [System Requirements](#system-requirements) - what you need
* [Contact](#contact) - how to reach us
* [Uninstall](#uninstall) - removal of Management Tools
* [Modules](#modules)
  * [app_info](#app_info) - access applications' information
  * [loggers](#loggers) - output data to logs
  * [plist_editor](#plist_editor) - modify plists properly
* [Scripts](#scripts)
  * [App Lookup](#app-lookup) - lookup an application's information
  * [Python Executable Bundler](#python-executable-bundler) - bundle a Python project into a standalone script
  * [Management Logger](#management-logger) - log data easily
  * [Management Email](#management-email) - simple email sender
  * [Python Package Creator](#python-package-creator) - an automated .pkg creator for Python projects using 'setup.py'

## Download

[Download the latest installer here!](../../releases/)

## System Requirements

Management Tools has been tested to work with Mac OS X 10.8 through 10.10, and uses Python version 2.7.

## Contact

If you have any comments, questions, or other input, either [file an issue](../../issues) or [send an email to us](mailto:mlib-its-mac-github@lists.utah.edu). Thanks!

## Uninstall

To uninstall Management Tools (not that you'd ever want to), run:

```
$ sudo /usr/local/bin/uninstall-management-tools-VERSION.sh
```

This will remove all traces of the package from the system.

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

### loggers

In our deployment, we like to log stuff. Logging things is a useful way to record information for later perusal, which can be quite helpful. Since I kept having to copy/paste our logging mechanisms from script to script, I just created a dedicated logging module.

There are two methods in this module: `file_logger` and `stream_logger`. These methods return logger objects from Python's `logging` module. However, they are set up in a particular way to make our job easier.

#### file_logger

The `file_logger` method returns a logger that outputs to a file. All that it requires is a name, and it will put that log in a default location that you have write access to (`/var/log/management` for administrators, `~/Library/Logs/Management` for non-privileged) and then you can write to the log the same as any other Python logger.

Example usage:

```python
>>> from management_tools.loggers import file_logger
>>> logger = file_logger('test')
>>> logger.info("This is regular information.")
>>> logger.debug("Super verbose (not logged by default, unless the level is changed).")
>>> logger.error("This is an error.")
>>> logger.fatal("Danger, Will Robinson! Danger!")
```

If we then go and look in (assuming this was run unprivileged) `~/Library/Logs/Management/test.log`:

```
2014-05-05 14:41:55,719 INFO: This is regular information.
2014-05-05 14:42:01,399 ERROR: This is an error.
2014-05-05 14:42:18,688 CRITICAL: Danger, Will Robinson! Danger!
```

#### stream_logger

`stream_logger` is a console-only logger. This is useful if you want to output log-formatted information to the command line at runtime.

In my scripts, I usually provide an option to not output to a log. If this is specified, then a `stream_logger` is used instead. That way the information still gets out, but isn't written to disk.

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

| Option | Purpose |
|--------|---------|
| `-h`, `--help` | Prints usage instructions. |
| `-v`, `--version` | Prints version information. |
| `-n`, `--no-log` | Prevents logs from being written to file (instead they'll come through stdio). |
| `-l log`, `--log log` | Uses `log` as the destination for logging output. |
| `-f file`, `--file file` | Attaches `file` to the email as a plaintext document. |
| `-u subject`, `--subject subject` | Places `subject` in the message header. |
| `-s server`, `--smtp-server server` | Send the mail through `server`. |
| `-p port`, `--smtp-port port` | Connect to the server via port `port`. |
| `-U user`, `--smtp-username user` | Connect to the server as `user`. |
| `-P pass`, `--smtp-password pass` | Connect to the server with password `pass`. |
| `-F address`, `--smtp-from address` | Send the mail from `address`. |
| `-T address`, `--smtp-to address` | Send the mail to `address`. |

Additionally, a message can be supplied by itself in a quoted string.

In an effort to simplify administration, many of the options can be set through environment variables. These variables are:

| Variable Name | Correlating command-line flag |
|---------------|-------------------------------|
| `MANAGEMENT_SMTP_SERVER` | `-s`, `--smtp-server` |
| `MANAGEMENT_SMTP_PORT` | `-p`, `--smtp-port` |
| `MANAGEMENT_SMTP_USER` | `-U`, `--smtp-username` |
| `MANAGEMENT_SMTP_PASS` | `-P`, `--smtp-password` |
| `MANAGEMENT_SMTP_FROM` | `-F`, `--smtp-from` |
| `MANAGEMENT_SMTP_TO` | `-T`, `--smtp-to` |

Environment variables can easily be set by running a command such as:

```
$ export MANAGEMENT_SMTP_SERVER='mail.example.com'
```

Note that environment variables must be declared using the `export` functionality for the script to be able to pick up on them. It is conceivable to have these set globally, but that is outside the scope of this summary.

### Python Package Creator

The Python Package Creator (also 'PyPkg') will create an OS X-compatible `.pkg` file containing the contents of a Python project. The project *must* use the `setup.py` system, which is documented [here](https://docs.python.org/2/distutils/setupscript.html). If you aren't using this system to manage your Python projects, you may want to consider changing to it.

There are a few options that can be given to the script:

| Option | Purpose |
|--------|---------|
| `-h`, `--help` | Prints usage information. |
| `-v`, `--version` | Prints version information. |
| `--dirty` | Prevents cleanup after the package has been created. |
| `--name file_name` | The name of the `.pkg` file will be `file_name`. The special values `#NAME` and `#VERSION` can be used to get the name and version information from `setup.py`. |
| `--pkg-version version` | Manually sets the version information for the package, both for the name and for the package's receipt once installed. |
| `--dest destination` | The `.pkg` file will be created at `destination`. Note that this is relative to the path given to the script. |
| `--python python_executable` | The `setup.py` script will be run using the Python executable at `python_executable`. |

As an example, this Management Tools package (in the [`/pkg/`](pkg) directory) was created by running the following from within the Management Tools directory:

```
$ pypkg.py edu.utah.scl.management-tools ./setup.py --python /usr/bin/python --dest pkg
```

#### Uninstaller

PyPkg automatically produces another `.pkg` file to *uninstall* whatever package you just produced. You can simply double-click it and it will remove the contents of the previously-installed package, and it will also forget that package from the receipts database. This is significantly easier than the previous method of running an uninstallation script from the terminal. By default this uninstallation package will be produced on the same level as the installation package, so you will be able to decide how to distribute them.
