import subprocess
from itertools import groupby

def get_filesystems(local_only=False):
    """
    """
    fs_info = get_raw_fs_info().split('\n')
    fs_info = [x for x in fs_info if x]
    print(fs_info)
    filesystem_names = [x.split(' on')[0] for x in fs_info]
    print(filesystem_names)
    
    filesystems = []
    
    for name in filesystem_names:
        filesystem = Filesystem(name)
        filesystems.append(filesystem)
    
    return filesystems

def get_raw_fs_info(fs=None, strict=False):
    # Get a list of all the currently-mounted disks' names.
    fs_info = subprocess.check_output(['/sbin/mount'])
    
    if not fs:
        return fs_info
    
    # Split the input and clean out blank lines.
    fs_info = fs_info.split('\n')
    fs_info = [x for x in fs_info if x]
    # Check for the filesystem being in the list.
    if strict:
        result = [x for x in fs_info if fs == x.split(' on')[0]]
    else:
        result = [x for x in fs_info if fs in x.split(' on')[0]]
    if len(result) > 1:
        raise RuntimeError("Too many matches for filesystem '{}'.".format(fs))
    elif len(result) == 0:
        raise RuntimeError("No matches for filesystem '{}'.".format(fs))
    else:
        return result[0]

def get_raw_fs_usage(mount_point=None):
    df = ['/bin/df', '-P', '-k']
    if mount_point:
        df.append(mount_point)
    df_info = subprocess.check_output(df)
    
    if not mount_point:
        return df_info
    
    # Split the input and clean out blank lines, as well as the leading line
    # that consists of just headers.
    df_info = df_info.split('\n')
    df_info = [x for x in df_info if x]
    if len(df_info) > 2:
        raise RuntimeError("Specified mount point '{}' exists on two filesystems.".format(mount_point))
    # We only need the raw form of the numbers and values.
    return df_info[1]

class Filesystem(object):
    def __init__(self, name):
        self.__name          = name
        self.__mount_point   = None
        self.__type          = None
        self.__kblocks       = None
        self.__kblocks_used  = None
        self.__kblocks_avail = None
        self.__capacity      = None
        self.__properties    = None
        
        self.update()
    
    def update(self):
        info = get_raw_fs_info(fs=self.name, strict=True)
        # 'info' now contains a line like:
        #   /dev/disk1s1 on /Volumes/External (hfs, local, journaled)
        #   ------+-----    --------+--------  -+-
        #       name           mount point    filesystem type
        info = info.split('on ')[1]
        self.__mount_point, properties = info.split(' (')
        properties = properties[:-1]
        properties = properties.split(', ')
        if properties[0].endswith('fs'):
            self.__type = properties[0]
        self.__properties = properties
        
        info = get_raw_fs_usage(self.mount_point)
        # 'info' now contains a line like:
        #   /dev/disk1s1  100    70    30    70%   /Volumes/External
        #   ------+-----  -+-   -+-   -+-    -+-   --------+--------
        #        name    blocks used avail capacity   mount point
        info = info.split()
        index = 0
        for index in range(len(info)):
            try:
                int(info[index])
                break
            except ValueError:
                pass
        self.__kblocks       = info[index]
        self.__kblocks_used  = info[index + 1]
        self.__kblocks_avail = info[index + 2]
        self.__capacity      = info[index + 3]
    
    def __repr__(self):
        return super(Filesystem, self).__repr__()
    
    @property
    def name(self):
        return self.__name if self.__name else None
    
    @property
    def mount_point(self):
        return self.__mount_point if self.__mount_point else None
    
    @property
    def type(self):
        return self.__type if self.__type else None
    
    @property
    def kblocks(self):
        return self.__kblocks if self.__kblocks else None
    
    @property
    def kblocks_used(self):
        return self.__kblocks_used if self.__kblocks_used else None
    
    @property
    def kblocks_avail(self):
        return self.__kblocks_avail if self.__kblocks_avail else None
    
    @property
    def capacity(self):
        return self.__capacity if self.__capacity else None
    
    @property
    def properties(self):
        return self.__properties if self.__properties else None
