import yaml
import boto3
import botocore
import logging
import subprocess
from .file import File
from .directory import Directory

class ConfigException(Exception):
    '''
    Exceptions related to the Config class that will cause the
    application to terminate.
    '''
    pass


class Config():
    '''
    This class handles all config data, gathered from both the command 
    line arguments and the config file.
    '''
    def __init__(self, config_file, args, client=None):
        '''
        Takes an argparse.ArgumentParser().parse_args() object 
        as an argument an an optional boto3 client. This client
        should only be specified for testing purposes, and used
        with a stubber.
        '''
        self.file = File(config_file, must_exist=True)
        self.load_config_file()
        self.load_config_args(args)
        self.validate(client)
        self.upload_retry_time = 60

    def load_config_args(self, args):
        self.backup_directory = args.backup_directory
        self.vault_name = args.vault_name
        self.recursive = args.recursive
        self.hidden = args.hidden
        self.verbose = args.verbose
        self.test = args.test
        if args.encrypt:
            self.encrypted = args.encrypt
        else:
            self.encrypted = ''

    def load_config_file(self):
        try:
            with open(self.file.path, 'r') as f:
                config_yaml = yaml.safe_load(f)
            self.profile = config_yaml['profile']
            self.temp_directory = Directory(config_yaml['temp_directory'], writable=True)
            self.max_archive_size = int(config_yaml['max_archive_size'])
            self.db_file = File(config_yaml['db_file'], must_exist=False, writable=True)
            self.log_file = File(config_yaml['log_file'], must_exist=False, writable=True)
            self.old_backups = int(config_yaml['old_backups'])
            self.compression_method = config_yaml['compression_method']
        except (ValueError, KeyError):
            raise ConfigException(
                'Config file is not formatted correctly')

    def validate(self, client):
        self.check_max_archive_size()
        self.check_compression_method()
        if self.encrypted:
            self.check_encryption_id()
        self.check_aws(client)

    def check_max_archive_size(self):
        if (self.max_archive_size == 0 or 
            (self.max_archive_size & (self.max_archive_size - 1)) != 0):
            raise ConfigException(
                'Max archive size must be a power of 2 e.g. 8388608, 16777216')

    def check_encryption_id(self):
        try:
            result = subprocess.run(
                f'gpg --fingerprint {self.encrypted}', 
                shell=True, check=True, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            raise ConfigException('Encryption ID error')

    def check_compression_method(self):
        methods = ['gz', 'gzip', 'bzip2', 'bz2', 'lzma', 'lzop']
        if self.compression_method not in methods:
            raise ConfigException((
                'Compression method must be one of the following: '
                f'{", ".join(methods)}'))
        # We use the compression method property when building the 
        # archive creation command, so here we convert the string
        if self.compression_method == 'gzip':
            self.compression_method = 'gz'
        elif self.compression_method == 'bzip2':
            self.compression_method = 'bz2'

    def check_old_backups(self):
        if self.old_backups < 0:
            raise ConfigException('Old backups must be a positive integer')

    def check_aws(self, client):
        '''Check all AWS credentials are valid and that we can connect'''
        if not client:
            session = boto3.Session(profile_name=self.profile)
            client = session.client('glacier')
        try:
            response = client.describe_vault(
                vaultName=self.vault_name
            )
            logging.debug('AWS checks passed')
        except botocore.exceptions.NoRegionError:
            raise ConfigException(
                'No region specified in AWS config file')
        except botocore.exceptions.EndpointConnectionError:
            raise ConfigException('Could not connect to AWS')
        except botocore.exceptions.NoCredentialsError:
            raise ConfigException(
                'Profile not found in .aws/credentials')
        except botocore.exceptions.ClientError:
            raise ConfigException(
                'AWS credentials or vault name not valid')
        except client.exceptions.ResourceNotFoundException:
            raise ConfigException(
                f'Glacier vault {self.vault_name} not found')
