#!/usr/bin/python

import os
import plistlib
import filelock

CONFIG_DIRECTORY = '/Library/Management/Configuration'

__all__ = [
    "ConfigManager"
]

class ConfigManager(object):
    def __init__(self, id):
        ## Create the config directory if it doesn't exist
        if not os.path.exists(CONFIG_DIRECTORY):
            os.makedirs(CONFIG_DIRECTORY)
        
        self.file = '{}/{}.plist'.format(CONFIG_DIRECTORY,id)
            
        ## create a lockfile to block race conditions
        self.lockfile = self.file + '.lockfile'
        self.lock = filelock.FileLock(self.lockfile, timeout=10)
    
    def write(self, data):
        with self.lock:
            plistlib.writePlist(data, self.file)
        
    def read(self):
        with self.lock:
            # try to read the config if it exists, otherwise return None
            try:
                return plistlib.readPlist(self.file) 
            except:
                return None
    
    def __del__(self):
        # remove lockfile when we are done using the config
        if os.path.exists(self.lockfile):
            os.remove(self.lockfile)
            
    def __repr__(self):
        return "CONFIG:   {}\nLOCKFILE: {}".format(self.file, self.lockfile)
        
        
## MAIN ##
def main():
    return 0

if __name__ == '__main__':
    main()

