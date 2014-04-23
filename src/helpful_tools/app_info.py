import os
import re
import subprocess

from plist_editor import PlistEditor

class AppInfo:
    '''A class to help you find your applications and their info.  Can take in either:
        1. A path to an application bundle ('.app')
        2. A bundle identifier ('com.apple.Safari')
        3. A short name ('Safari')

    After this, the name, path, bid, and plist are easily accessible.
    '''

    def __init__ (self, app):

        self.app = app

        # First, find the path of the app.
        if os.path.isdir(self.app):
            # Clearly it's a path.
            if self.app.endswith('/'):
                self.path = self.app[:-1]
            else:
                self.path = self.app
        elif '.' in self.app and self.app.find('.self.app', len(self.app) - 4) < 0:
            # Let's try and use it as a Bundle ID.
            self.path = subprocess.check_output(['mdfind', 'kMDItemCFBundleIdentifier', '=', self.app]).strip()
            if not self.path:
                raise ValueError("Invalid bundle identifier.  No path found.")
        else:
            # They probably tried to supply just a simple name for the self.application.  Silly user!
            # We shall try to accommodate...
            self.app = self.app.replace('.app', '')
            p = re.compile('.*' + self.app + '.*', re.IGNORECASE)
            apps = subprocess.check_output(['mdfind', '-onlyin', '/Applications', 'kMDItemKind==Application']).split('\n')
            for item in apps:
                result = p.search(item)
                if result:
                    self.path = result.group().strip('\n')
                    if os.path.isdir(self.path):
                        break

        if not self.path:
            raise ValueError("Invalid bundle identifier.  No path found.")
        # Since we now have the path, get the rest of the info!
        if os.path.exists(self.path + '/Contents/Info.plist'):
            self.plist = PlistEditor(self.path + '/Contents/Info.plist')
            self.bid = self.plist.read('CFBundleIdentifier')
            self.name = self.plist.read('CFBundleName')

    def __repr__ (self):
        return self.name + "\n\tBID:  " + self.bid + "\n\tPath: " + self.path
