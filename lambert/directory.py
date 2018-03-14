import os
from datetime import datetime


class DirectoryException(Exception):
    '''Exceptions related to the Directory class.'''
    pass


class Directory():
    '''
    Handles directories needed by the application.
    The writable argument determines whether an exception
    is raised if a directory is not writable.
    '''
    def __init__(self, directory_path, writable=False):
        if '~' in str(directory_path):
            self.path = os.path.expanduser(directory_path)
        else:
            self.path = os.path.abspath(directory_path)
        try:
            os.listdir(self.path)
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            raise DirectoryException(
                f'Cannot open the {self.path} directory')
        self.parent = os.path.dirname(self.path)
        if writable:
            self.write_temp_file()

    def write_temp_file(self):
        temp_file = os.path.join(self.path, f'lambert_{datetime.now().isoformat()}')
        try:
            open(temp_file, 'w+').close()
            os.remove(temp_file)
        except (PermissionError, IOError):
            raise DirectoryException(
                f'Cannot write to the {self.path} directory')
