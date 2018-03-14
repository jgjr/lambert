import os
import logging
from .directory import Directory
from .file import File
from .backupdirectory import BackupDirectory

class BackupRoot(Directory):
    '''
    When performing a recursive backup, this class serves as the parent.
    It extends the Directory class and adds ability to retrieve child 
    directories, and filter those directories with a .lambert_ignore file.
    '''
    def __init__(self, config):
        Directory.__init__(self, config.backup_directory)
        self.children = self.get_children(config.hidden)
        if '.lambert_ignore' in os.listdir(config.backup_directory):
            self.ignore_file = File(os.path.join(self.path, '.lambert_ignore'))
            self.filter_ignored_directories()
        logging.debug('Initialized backup root')

    def get_children(self, hidden):
        children = []
        items = os.listdir(self.path)
        for item in items:
            child = os.path.join(self.path, item)
            if hidden:
                if os.path.isdir(child):
                    children.append(child)
            else:
                if os.path.isdir(child) and not item.startswith('.'):
                    children.append(child)
        return sorted(children)

    def filter_ignored_directories(self):
        for dir_name in self.ignore_file.get_contents():
            dir_path = os.path.join(self.path, dir_name.strip())
            if dir_path[-1] == '/':
                dir_path = dir_path[:-1]
            if dir_path in self.children:
                self.children.remove(dir_path)
