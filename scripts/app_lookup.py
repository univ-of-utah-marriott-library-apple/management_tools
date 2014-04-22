import sys

from helpful_tools.app_info import AppInfo

def main (args):
    for item in args:
        print AppInfo(item)

if __name__ == "__main__":
    main(sys.argv)
