import os
import sys
import logging
import boto3
from .directory import Directory, DirectoryException
from .config import Config, ConfigException
from .database import Database, DatabaseException
from .file import File, FileException
from .archive import Archive, ArchiveException
from .backuproot import BackupRoot
from .backupdirectory import BackupDirectory
from .upload import Upload, UploadException


class Backup():
    '''
    This class is responsible for setting up and carrying out the 
    whole backup process. The process will differ slightly if a 
    recursive backup is specified in the args.
    '''
    def __init__(self, args, client=None):
        '''
        Takes an argparse.ArgumentParser().parse_args() object 
        as an argument an an optional boto3 client. This client
        should only be specified for testing purposes, and used
        with a stubber.
        '''
        if args.config:
            config_file = args.config
        else: 
            config_file = os.path.expanduser('~/.lambert/config')
        try:
            self.config = Config(config_file, args, client)
            self.database = Database(self.config.db_file)
            self.log_init()
        except (ConfigException, FileException,
            DirectoryException, DatabaseException) as e:
            logging.critical(e)
            sys.exit(1)

    def log_init(self):
        '''Log to the file specified in the config file'''
        root = logging.getLogger()
        if root.handlers:
            for handler in root.handlers:
                root.removeHandler(handler)
        if self.config.verbose:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        logging.basicConfig(
            filename=self.config.log_file.path, level=log_level, filemode='a',
            format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug('Initialized log')
        # Boto3 gets very noisy, this hides unnecessary log calls
        logging.getLogger('boto3').setLevel(logging.CRITICAL)
        logging.getLogger('botocore').setLevel(logging.CRITICAL)
        logging.getLogger('nose').setLevel(logging.CRITICAL)
        logging.getLogger('s3transfer').setLevel(logging.CRITICAL)

    def run(self, client=None):
        if self.config.recursive:
            self.recursive_backup(client)
        else:
            self.single_directory_backup(self.config.backup_directory, client)

    def single_directory_backup(self, directory, client):
        backup_directory = BackupDirectory(directory) 
        logging.debug(f'Starting backup of {backup_directory.path}')
        if self.config.test:
            logging.debug('Skipping backup process, test mode enabled')
        else:
            try:
                archive = Archive(backup_directory, self.config)
            except ArchiveException:
                logging.error(f'Skipping backup of {backup_directory.path}')
                return
            try:
                upload = Upload(archive, self.config, client)
                self.write_db_entry(archive, upload)
                self.delete_old_backups(archive, client)
            except UploadException:
                logging.error(f'Skipping backup of {backup_directory.path}')
            finally:
                archive.remove()

    def recursive_backup(self, client):
        backup_root = BackupRoot(self.config)
        for child in backup_root.children:
            self.single_directory_backup(child, client)

    def write_db_entry(self, archive, upload):
        entry = {
            'directory': archive.backup_directory.path,
            'archive_id': upload.archive_id,
            'vault': self.config.vault_name,
            'location': upload.location,
            'encrypted': self.config.encrypted,
            'multi_part': int(archive.multi_part),
            'size': archive.size,
            'deleted': 0
        }
        self.database.write_entry(entry)
        logging.debug(f'Database entry written for {archive.name}')

    def delete_old_backups(self, archive, client=None):
        '''
        We can choose not to keep too many backups on Glacier. The number
        of old backups is specified in the config file. Here the IDs of
        old backups are retrieved from the database and a delete request
        is sent to AWS.
        '''
        backups = self.database.get_backups(archive.backup_directory.path)
        to_keep = self.config.old_backups + 1
        if not client:
            session = boto3.Session(profile_name=self.config.profile)
            client = session.client('glacier')
        if len(backups) > to_keep:
            for backup in backups[0:-to_keep]:
                archive_id = backup[2]
                response = client.delete_archive(
                    vaultName=self.config.vault_name,
                    archiveId=archive_id
                )
                self.database.delete_backup(archive_id)
            logging.debug(f'Old backups of {archive.name} deleted')
