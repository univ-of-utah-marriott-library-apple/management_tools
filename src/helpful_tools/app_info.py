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

    Accessible parts are:
        path  - the path to the .app bundle
        plist - the plist at [path]/Contents/Info.plist
        bid   - the bundle identifier of the application in the plist
                given by CFBundleIdentifier
        name  - the name of the application in the plist given by
                CFBundleName
    '''

    def __init__ (self, app):

        self.path = None
        self.plist = None
        self.bid = None
        self.name = None

        # First, find the path of the app.
        if os.path.isdir(app):
            # Clearly it's a path.
            if app.endswith('/'):
                self.path = app[:-1]
            else:
                self.path = app
        elif '.' in app and app.find('.app', len(app) - 4) < 0:
            # Let's try and use it as a Bundle ID.
            self.path = subprocess.check_output(['mdfind', 'kMDItemCFBundleIdentifier', '=', app]).strip()
            if not self.path:
                raise ValueError("Invalid bundle identifier.  No path found.")
        else:
            # They probably tried to supply just a simple name for the application.  Silly user!
            # We shall try to accommodate...
            app = app.replace('.app', '')
            p = re.compile('.*' + app + '.*', re.IGNORECASE)
            # We use 'mdfind' (aka Spotlight) to find all applications and search through their names.
            apps = subprocess.check_output(['mdfind', '-onlyin', '/Applications', 'kMDItemKind==Application']).split('\n')
            for item in apps:
                result = p.search(item)
                if result:
                    self.path = result.group().strip('\n')
                    if os.path.isdir(self.path):
                        break

        # If the path hasn't been found by now, something didn't go very well.
        if not self.path:
            raise ValueError("Invalid application: no path found.")

        # Since we now have the path, get the rest of the info!
        if os.path.exists(self.path + '/Contents/Info.plist'):
            self.plist = PlistEditor(self.path + '/Contents/Info.plist')
            self.bid = self.plist.read('CFBundleIdentifier')
            self.name = self.plist.read('CFBundleName')
        else:
            raise ValueError("Invalid application: no valid Info.plist found.")

    def __repr__ (self):
        result = str(self.name)
        result += "\n\tBID:        " + str(self.bid)
        result += "\n\tPath:       " + str(self.path)
        result += "\n\tInfo.plist: " + str(self.plist)
        return result
