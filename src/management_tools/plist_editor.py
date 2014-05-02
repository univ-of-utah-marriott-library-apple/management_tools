import os
import subprocess

class PlistEditor:
    '''Creates an object which can directly interact with a plist.  This makes
    it easier to go about editing plist files in non-standard locations.
    '''

    def __init__(self, path):
        '''Creates the PlistEditor object.  The specified plist must be readable
        and exist for this to pass successfully (does not create a new plist).

        path -- the location of the plist in the file system
        '''
        if not path.endswith('.plist'):
            path = path + '.plist'
        if not os.path.isfile(path):
            raise IOError(".plist file '" + str(path) + "' is not a valid path.")
        if not os.access(path, os.R_OK):
            raise IOError(".plist file '" + str(path) + "' is not readable.")
        self.path = str(path)
        self.list = str(path[:-6])

    def __repr__(self):
        '''Returns a nicely formatted string.
        '''

        return str(self.path)

    def read(self, key=None):
        '''Returns either the entire plist (if key is left blank) or the
        specified key's value as a string.

        key -- the key in the plist to read
        '''
        result = ''
        if not key:
            try:
                result = subprocess.check_output(['defaults', 'read', self.list])
            except subprocess.CalledProcessError:
                return ''
        else:
            try:
                result = subprocess.check_output(['defaults', 'read', self.list, str(key)])
            except subprocess.CalledProcessError:
                return ''
        if result.endswith('\n'):
            result = result[:-1]
        return result

    def type(self, key):
        '''Returns the type of the specified key as a string.

        key -- the key to get the type of
        '''
        if not key:
            raise ValueError("Must provide a key.")
        try:
            result = subprocess.check_output(['defaults', 'read-type', self.list, str(key)])
        except subprocess.CalledProcessError:
            raise ValueError("Must provide a valid key for '" + self.path + "'.")
        return result.split()[-1]

    def write(self, key, value, type="string"):
        '''Writes the specified value to the specified key in a given type.  If
        no type is given, the default is 'string'.  Returns the exit code of the
        defaults command.

        key   -- the key to write to
        value -- the value to put in the key
        type  -- the type of value (boolean, integer, etc.)
        '''
        if not os.access(self.path, os.W_OK):
            raise IOError(".plist file '" + self.path + "' is not writable.")
        if not key:
            raise ValueError("Must provide a key.")
        valids = ['string', 'data', 'int', 'integer', 'float', 'bool', 'boolean', 'data', 'array', 'array-add', 'dict', 'dict-add']
        if not type in valids:
            raise ValueError("Type not valid.  Must be one of " + str(valids))
        elif type == 'array':
            option = '-array-add'
        elif type == 'dict':
            option = '-dict-add'
        else:
            option = '-' + type
        return subprocess.call(['defaults', 'write', self.list, str(key), option, str(value)])

    def dict_add(self, key, nestedKey, value, type="string"):
        '''
        '''
        if not os.access(self.path, os.W_OK):
            raise IOError(".plist file '" + self.path + "' is not writable.")
        if not key:
            raise ValueError("Must provide a key.")
        if not nestedKey:
            raise ValueError("Dictionaries require inner keys.")
        valids = ['string', 'data', 'int', 'integer', 'float', 'bool', 'boolean', 'data', 'array', 'array-add', 'dict', 'dict-add']
        if not type in valids:
            raise ValueError("Type not valid.  Must be one of " + str(valids))
        elif type == 'array':
            option = '-array-add'
        elif type == 'dict':
            option = '-dict-add'
        else:
            option = '-' + type

        return subprocess.call(['defaults', 'write', self.list, str(key), '-dict-add', str(nestedKey), option, str(value)])

    def delete(self, key=None):
        '''Deletes either the entire plist (if no key is given) or the specified
        entry.  This does NOT ask for confirmation, so be careful!  Returns the
        exit code of the defaults command.

        key -- the key to delete
        '''
        if not os.access(self.path, os.W_OK):
            raise IOError(".plist file '" + self.path + "' is not deletable.")
        if not key:
            return subprocess.call(['defaults', 'delete', self.list])
        else:
            return subprocess.call(['defaults', 'delete', self.list, str(key)])
