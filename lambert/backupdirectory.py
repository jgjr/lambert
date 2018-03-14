import os
import subprocess
from datetime import date
import logging
from .directory import Directory


class BackupDirectory(Directory):
    '''
    This class extends the Directory class and adds the name and
    archive_name properties, needed when creating an archive and
    uploading.
    '''
    def __init__(self, directory_path):
        Directory.__init__(self, directory_path)
        self.name = os.path.basename(self.path)
        self.archive_name = '_'.join([
            self.name.lower().replace(' ', '-'),
            date.today().isoformat()])
        logging.debug(f'Initialized {self.path} as backup directory')
