Management Tools
================

A collection of Python scripts and packages to simplify OS X management.

## Contents

* [Modules](#modules)
  * [app_info](#app-info) - access applications' information
  * [loggers](#loggers) - output data to logs
  * [plist_editor](#plist-editor) - modify plists properly
* [Scripts](#scripts)
  * [App Lookup](#app-lookup) - lookup an application's information
  * [Python Executable Bundler](#python-executable-bundler) - bundle a Python project into a standalone script
  * [Management Logger](#management-logger) - log data easily

## Modules

In Python, modules are designed to be imported into another project to make your life easier.  These can be integrated into your packages by simply using:

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

This module contains a class, `AppInfo`, which can be used to get information about applications.  Generally, you will do:

```python
from management_tools.app_info import AppInfo
```

Then the class can be used to get information.  It requires an argument upon creation which should tell it something identifiable about the application, such as a valid short name, a bundle path, or a bundle identifier.  Once it has been created, you can access various useful bits about the application.

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

### loggers

In our deployment, we like to log stuff.  Logging things is a useful way to record information for later perusal, which can be quite helpful.  Since I kept having to copy/paste our logging mechanisms from script to script, I just created a dedicated logging module.

There are two methods in this module: `file_logger` and `stream_logger`.  These methods return logger objects from Python's `logging` module.  However, they are set up in a particular way to make our job easier.

#### file_logger

The `file_logger` method returns a logger that outputs to a file.  All that it requires is a name, and it will put that log in a default location that you have write access to (`/var/log/management` for administrators, `~/Library/Logs/Management` for non-privileged) and then you can write to the log the same as any other Python logger.

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

`stream_logger` is a console-only logger.  This is useful if you want to output log-formatted information to the command line at runtime.

In my scripts, I usually provide an option to not output to a log.  If this is specified, then a `stream_logger` is used instead.  That way the information still gets out, but isn't written to disk.

### plist_editor

Many Apple services and applications utilize property list files, usually referred to simply as 'plists'.  These files can be modified to contain all kinds of information.

However, *editing* the files can be somewhat of a hassle.  Since Mac OS X 10.9 "Mavericks", plist files are periodically cached and then rewritten asynchronously to the disk.  What this means is that if you modify a plist with a plaintext editor, **there is no guarantee that the changes will remain permanently**.  This is not exactly the ideal way for things to be done.

OS X contains a command called `defaults`.  This command provides the necessary mechanism to modify plist files without the asynchronous caching having a negative effect on your work.  This `plist_editor` module contains a class, `PlistEditor`, which allows you to modify plist files using this `defaults` command (but without you having to actually make the calls).

```python
from management_tools.plist_editor import PlistEditor

plist = PlistEditor('/path/to/file.plist')
```

## Scripts

The scripts are mostly just simple frontends for using the modules above.  For example: perhaps you want to log something, but you don't want to go through the trouble of importing the logger and setting it up.  Instead, just use the Management Logger script and it will do the work for you.

### App Lookup

This serves as a quick interface to the `app_info` module.  When calling the script, simply supply identifiers for applications and it will return the application's given name, bundle ID, path, and Info.plist path.

```
$ app_lookup.py safari
Safari
    BID:       com.apple.Safari
    Path:      /Applications/Web Browsers/Safari.app
    Info.Plist /Applications/Web Browsers/Safari.app/Contents/Info.plist
```

### Python Executable Bundler

A while ago I learned that Python scripts can be bundled together in standalone 'executables'.  I did this manually for a while, and then created this script to automate it.

Effectively what happens is this takes the Pythonic contents of a directory (i.e. all the `.py` files) and compresses them into a zipped structure.  A shebang is catted in to the zip and then chmoded to produce an 'executable'.  Note that that main entrance point of the script must be named `__main__.py` for this to work properly.

Usage of the script is simple.  If you are within the directory of Python files:

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

The Management Logger is an interface for the `file_logger` from above.  Calling Management Logger allows you to easily write a log entry to a file quickly and efficiently.  Calling the script involves:

```
$ management_logger.py file "This is an entry in my log."
```

This will log the line `"This is an entry in my log."` to a file named `file.log` located in one of two places: either `/var/log/management/` if the calling user has root privileges, or else `~/Library/Logs/Management/`.
