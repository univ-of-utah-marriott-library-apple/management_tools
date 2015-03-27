import os
import subprocess


def get_filesystems():
    """
    Get all of the currently-mounted filesystems, both local and remote.
    
    :return: a list of Filesystem objects
    """
    fs_info = get_raw_fs_info().split('\n')
    fs_info = [x for x in fs_info if x]
    filesystem_names = [x.split(' on')[0] for x in fs_info]
    
    filesystems = []
    
    for name in filesystem_names:
        filesystem = Filesystem(name)
        filesystems.append(filesystem)
    
    return filesystems


def get_raw_fs_info(fs=None, strict=False):
    """
    Obtain the output from `mount`. This can either be generic and include all
    of the information (including headers), or you can specify a particular
    filesystem to poll for information (no headers will be returned).
    
    If 'strict' is left as False, then a partial match for the given name will
    be attempted. This can result in an error if multiple mounted filesystems
    have 'fs' in their names.
    
    :param fs: the name of a filesystem to check (None for generic)
    :param strict: whether to match filesystem name exactly
    """
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
    """
    Get the output from `df`. This can either be generic and include all of the
    information outputted by `df -Pk` (including headers), or you can specify a
    particular filesystem to poll for information (no headers will be returned).
    
    :param mount_point: the name of a filesystem to check (None for generic)
    """
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


def get_responsible_fs(target):
    """
    Given a target on disk, determines which filesystem is responsible for it
    (i.e. where the target file or directory lives).
    
    :param target: the file or directory to locate
    :return: a string containing the name of the filesystem
    """
    # Check that the target is valid.
    if not os.path.exists(target):
        raise ValueError("Given file or directory '{}' does not exist.".format(target))
    
    # Call `df` to find the information.
    df = ['/bin/df', '-P', '-k', str(target)]
    df_info = subprocess.check_output(df).split('\n')
    df_info = [x for x in df_info if x]
    if len(df_info) != 2:
        raise RuntimeError("Unable to find responsible filesystem for '{}'.".format(target))
    
    # Parse the returned information for the filesystem device identifier.
    info = df_info[1].split()
    index = 0
    for index in range(len(info)):
        try:
            int(info[index])
            break
        except ValueError:
            pass
    
    # Return the value.
    fs_name = ' '.join(info[:index])
    return fs_name


class Filesystem(object):
    def __init__(self, name):
        """
        Set all of the initial properties of the object.
        
        :param name: the filesystem name
        """
        self.__name          = name
        self.__mount_point   = None
        self.__type          = None
        self.__kblocks       = None
        self.__kblocks_used  = None
        self.__kblocks_free = None
        self.__capacity      = None
        self.__properties    = None
        
        # Update all of the information.
        self.update()
    
    def update(self):
        """
        Update all of the information regarding this filesystem. This will check
        the `df` output and parse it to update this object's properties.
        """
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
        self.__kblocks_free = info[index + 2]
        self.__capacity      = info[index + 3][:-1] # remove the "%" off the end
    
    def __repr__(self):
        """
        :return: the identifier used to create this object
        """
        return "{}".format(self.name)
    
    def __str__(self):
        """
        :return: a string representing this object
        """
        result = (
            "{name} mounted on {mount_point}, type: {type}\n"
            "    total kblocks:      {kblocks}\n"
            "    used kblocks:       {kblocks_used}\n"
            "    available kblocks:  {kblocks_free}\n"
            "    remaining capacity: {capacity}\n"
            "    other properties:   {properties}"
        ).format(
            name = self.name, mount_point = self.mount_point, type = self.type,
            kblocks       = self.kblocks,
            kblocks_used  = self.kblocks_used,
            kblocks_free = self.kblocks_free,
            capacity      = self.capacity,
            properties    = ', '.join(self.properties)
        )
        
        return result
    
    ########
    # PROPERTIES
    #
    # These are defined just to make the attributes more difficult to modify
    # outside of the object.
    ########
    
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
        return int(self.__kblocks) if self.__kblocks else None
    
    @property
    def kblocks_used(self):
        return int(self.__kblocks_used) if self.__kblocks_used else None
    
    @property
    def kblocks_free(self):
        return int(self.__kblocks_free) if self.__kblocks_free else None
    
    @property
    def bytes(self):
        return 1024 * self.kblocks if self.kblocks else None
    
    @property
    def bytes_used(self):
        return 1024 * self.kblocks_used if self.kblocks_used else None
    
    @property
    def bytes_free(self):
        return 1024 * self.kblocks_free if self.kblocks_free else None
    
    @property
    def capacity(self):
        return int(self.__capacity) if self.__capacity else None
    
    @property
    def properties(self):
        return self.__properties if self.__properties else None
