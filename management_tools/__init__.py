import app_info
import loggers
import plist_editor

__version__ = '1.6.3'
__all__     = ['app_info', 'loggers', 'plist_editor']

# This provides the ability to get the version from the command line.
# Do something like:
#   $ python -m management_tools.__init__
if __name__ == "__main__":
    print("Management Tools, version: {}".format(__version__))
