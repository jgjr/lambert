import os
import io
import logging
import subprocess
import math


class ArchiveException(Exception):
    '''
    Exceptions encountered when creating or using an archive.
    These will result in one directory being skipped, and the 
    application will carry on.
    '''
    pass


class Archive():
    '''
    The class is responsible for creating archives, returning 
    their contents, calculating the size of each part, and
    removing the archive after upload.
    '''
    def __init__(self, backup_directory, config):
        '''
        Takes an instance of the backup directory 
        class and a config object as arguments
        '''
        self.backup_directory = backup_directory
        self.name = backup_directory.archive_name
        self.config = config
        self.make_archive()
        self.size = os.path.getsize(self.filepath)
        self.multi_part = (self.size > self.config.max_archive_size)
        self.parts = math.ceil(self.size / self.config.max_archive_size)

    def make_archive(self):
        self.filepath = (
            f'{os.path.join(self.config.temp_directory.path, self.name)}'
            f'.tar.{self.config.compression_method}')
        if self.config.encrypted:
            self.filepath += '.gpg'
        command = self.get_archive_command()
        logging.debug('Creating the archive')
        try:
            result = subprocess.run(
                command, shell=True, check=True, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            logging.debug(
                    'Received the following error while creating the archive, '
                    f'may not be critical: {e}')
        if os.path.isfile(self.filepath):
            logging.debug(
                f'{self.backup_directory.name} archive created')
        else:
            raise ArchiveException('The archive could not be created')

    def get_archive_command(self):
        '''
        Returns a different command to be executed depending 
        on the compression method and when it needs to be encrypted, 
        both set in the config object.
        '''
        if self.config.compression_method == 'gz':
            command = 'tar -czf '
        if self.config.compression_method == 'bz2':
            command = 'tar -cjf '
        if self.config.compression_method == 'lzma':
            command = 'tar --lzma -cf '
        if self.config.compression_method == 'lzop ':
            command = 'tar --lzop -cf '
        if self.config.encrypted:
            command += (f'- -C {self.backup_directory.parent} '
                f'"{self.backup_directory.name}" --warning=no-file-changed | '
                f'gpg --encrypt --recipient "{self.config.encrypted}" '
                f'--output {self.filepath}')
        else:
            command += (f'{self.filepath} -C {self.backup_directory.parent} '
                f'"{self.backup_directory.name}" --warning=no-file-changed')
        return command

    def get_data(self, part):
        start = part * self.config.max_archive_size
        archive = open(self.filepath, 'rb')
        archive.seek(start)
        return archive.read(self.get_part_size(part))

    def get_file_object(self):
        return open(self.filepath, 'rb')

    def get_part_size(self, part):
        if part < (self.parts - 1):
            return self.config.max_archive_size
        elif part == (self.parts - 1):
            return self.size % self.config.max_archive_size

    def remove(self):
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)
            logging.debug(f'{self.backup_directory.name} archive removed')
