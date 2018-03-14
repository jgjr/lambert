import os

class FileException(Exception):
    '''Exceptions that related to the File class.'''
    pass

class File():
    '''
    This class handles various files required by the application. 
    The must_exist and writable flags determine whether an exception
    will be raised if those two conditions are not met.
    '''
    def __init__(self, file_path, must_exist=False, writable=False):
        if '~' in file_path:
            self.path = os.path.expanduser(file_path)
        else:
            self.path = os.path.abspath(file_path)
        if os.path.isfile(self.path):
            self.check_existing()
        elif not os.path.isfile(self.path) and not must_exist:
            self.create_new()
        elif not os.path.isfile(self.path) and must_exist:
            raise FileException(f'Cannot locate {self.path} file')
        if writable:
            self.check_writable()

    def create_new(self):
        try:
            open(self.path, 'w+').close()
        except PermissionError:
            raise FileException(
                f'Cannot create {self.path} file - permissions error')
        except FileNotFoundError:
            raise FileException(
                f'Cannot create {self.path} file - invalid directory')

    def check_existing(self):
        try:
            open(self.path, 'r').close()
        except PermissionError:
            raise FileException(
                f'Cannot open {self.path} file - permissions error')

    def check_writable(self):
        try:
            open(self.path, 'a').close()
        except PermissionError:
            raise FileException(
                f'Cannot write to {self.path} file - permissions error')

    def get_contents(self):
        with open(self.path) as f:
            return f.readlines()
