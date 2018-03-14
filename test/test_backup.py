import os
import pytest
import yaml
import boto3
import logging
from random import random
from botocore.stub import Stubber, ANY
from lambert.backup import Backup
from lambert.config import Config
from lambert.database import Database
from lambert.directory import Directory
from lambert.archive import Archive
from lambert.backupdirectory import BackupDirectory


def create_config_file(tmpdir, changes=None):
    config_values = {
        'profile': 'default',
        'temp_directory': str(tmpdir),
        'max_archive_size': '16777216',
        'db_file': os.path.join(tmpdir, 'lambert.sqlite'),
        'log_file': os.path.join(tmpdir, 'lambert.log'),
        'old_backups': '1',
        'compression_method': 'gzip'
    }
    if changes:
        for key, value in changes.items():
            config_values[key] = value
    config_file = os.path.join(tmpdir, 'config')  
    with open(config_file, 'w+') as f:
        yaml.dump(config_values, f)
    return config_file
    

def get_stubbed_check_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    stubber = Stubber(client)
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.activate()
    return client


def get_stubbed_recursive_single_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    stubber = Stubber(client)
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.add_response('upload_archive', {
            'location': '/path/to/archive1',
            'archiveId': 'archive-id-123'
        }, {
            'vaultName': ANY,
            'archiveDescription': ANY,
            'body': ANY
        })
    stubber.add_response('upload_archive', {
            'location': '/path/to/archive2',
            'archiveId': 'archive-id-321'
        }, {
            'vaultName': ANY,
            'archiveDescription': ANY,
            'body': ANY
        })
    stubber.activate()
    return client


def get_stubbed_recursive_multi_part_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    stubber = Stubber(client)
    initiate_multipart_upload_response = {'uploadId': 'upload-id-456'}
    initiate_multipart_upload_expected_params = {
        'vaultName': ANY,
        'partSize': ANY,
        'archiveDescription': ANY
    }
    upload_multipart_part_response = {'checksum': 'string'}
    upload_multipart_part_expected_params = {
        'vaultName': ANY,
        'uploadId': 'upload-id-456',
        'body': ANY,
        'range': ANY
    }
    complete_multipart_upload_response = {
        'location': '/path/to/multi_archive',
        'archiveId': 'archive-id-456'
    }
    complete_multipart_upload_expected_params = {
        'vaultName': ANY,
        'uploadId': ANY,
        'archiveSize': ANY,
        'checksum': ANY,
    }
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.add_response('initiate_multipart_upload', initiate_multipart_upload_response, initiate_multipart_upload_expected_params)
    stubber.add_response('upload_multipart_part', upload_multipart_part_response, upload_multipart_part_expected_params)
    stubber.add_response('upload_multipart_part', upload_multipart_part_response, upload_multipart_part_expected_params)
    stubber.add_response('complete_multipart_upload', complete_multipart_upload_response, complete_multipart_upload_expected_params)
    stubber.add_response('initiate_multipart_upload', initiate_multipart_upload_response, initiate_multipart_upload_expected_params)
    stubber.add_response('upload_multipart_part', upload_multipart_part_response, upload_multipart_part_expected_params)
    stubber.add_response('upload_multipart_part', upload_multipart_part_response, upload_multipart_part_expected_params)
    stubber.add_response('complete_multipart_upload', complete_multipart_upload_response, complete_multipart_upload_expected_params)
    stubber.activate()
    return client


def get_stubbed_single_single_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    stubber = Stubber(client)
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.add_response('upload_archive', {
            'location': '/path/to/archive1',
            'archiveId': 'archive-id-123'
        }, {
            'vaultName': ANY,
            'archiveDescription': ANY,
            'body': ANY
        })
    stubber.activate()
    return client


def get_stubbed_deleted_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    stubber = Stubber(client)
    upload_archive_expected_params = {
        'vaultName': ANY,
        'archiveDescription': ANY,
        'body': ANY
    }
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.add_response('upload_archive', {
        'location': '/path/to/archive1',
        'archiveId': 'archive-id-123'
    }, upload_archive_expected_params)
    stubber.add_response('upload_archive', {
        'location': '/path/to/archive1',
        'archiveId': 'archive-id-234'
    }, upload_archive_expected_params)
    stubber.add_response('upload_archive', {
        'location': '/path/to/archive1',
        'archiveId': 'archive-id-345'
    }, upload_archive_expected_params)
    stubber.add_response('delete_archive', {}, {'vaultName': ANY, 'archiveId': ANY})
    stubber.activate()
    return client


def get_stubbed_single_multi_part_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    stubber = Stubber(client)
    initiate_multipart_upload_response = {'uploadId': 'upload-id-456'}
    initiate_multipart_upload_expected_params = {
        'vaultName': ANY,
        'partSize': ANY,
        'archiveDescription': ANY
    }
    upload_multipart_part_response = {'checksum': 'string'}
    upload_multipart_part_expected_params = {
        'vaultName': ANY,
        'uploadId': 'upload-id-456',
        'body': ANY,
        'range': ANY
    }
    complete_multipart_upload_response = {
        'location': '/path/to/multi_archive',
        'archiveId': 'archive-id-456'
    }
    complete_multipart_upload_expected_params = {
        'vaultName': ANY,
        'uploadId': ANY,
        'archiveSize': ANY,
        'checksum': ANY,
    }
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.add_response('initiate_multipart_upload', initiate_multipart_upload_response, initiate_multipart_upload_expected_params)
    stubber.add_response('upload_multipart_part', upload_multipart_part_response, upload_multipart_part_expected_params)
    stubber.add_response('upload_multipart_part', upload_multipart_part_response, upload_multipart_part_expected_params)
    stubber.add_response('complete_multipart_upload', complete_multipart_upload_response, complete_multipart_upload_expected_params)
    stubber.activate()
    return client


def get_stubbed_error_client():
    session = boto3.Session(
        aws_access_key_id='a',
        aws_secret_access_key='b',
        aws_session_token='c',
        region_name='us-west-2'
    )
    client = session.client('glacier')
    error_params = {
        'vaultName': ANY,
        'archiveDescription': ANY,
        'body': ANY
    }
    stubber = Stubber(client)
    stubber.add_response('describe_vault', {}, {'vaultName': ANY})
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.add_client_error('upload_archive', service_error_code='', service_message='', http_status_code=400, expected_params = error_params)
    stubber.activate()
    return client



class MockArgs():
    def __init__(self, tmpdir, config_changes=None):
        self.backup_directory = 'backup_directory'
        self.vault_name = 'vault_name'
        self.recursive = False
        self.hidden = False
        self.verbose = False
        self.test = False
        self.encrypt = False
        self.config = create_config_file(tmpdir, config_changes)


class TestBackup():
    def create_single_directory(self, tmpdir, multi_part=False):
        test_dir = os.path.join(tmpdir, 'test_dir')
        os.mkdir(test_dir)
        with open(os.path.join(test_dir, 'file1'), 'w+') as f:
            f.write('here is my content')
        with open(os.path.join(test_dir, 'file2'), 'w+') as f:
            f.write('here is more of my content')
        return test_dir

    def create_recursive_directory(self, tmpdir, multi_part=False):
        test_dir = os.path.join(tmpdir, 'test_dir')
        os.mkdir(test_dir)
        sub_dir_1 = os.path.join(test_dir, 'sub_dir_1')
        sub_dir_2 = os.path.join(test_dir, 'sub_dir_2')
        for sub_dir in [sub_dir_1, sub_dir_2]:
            os.mkdir(sub_dir)
            with open(os.path.join(sub_dir, 'file1'), 'w+') as f:
                f.write('here is my content')
            with open(os.path.join(sub_dir, 'file2'), 'w+') as f:
                f.write('here is more of my content')
        return test_dir

    def test_init(self, tmpdir):
        args = MockArgs(tmpdir)
        client = get_stubbed_check_client()
        backup = Backup(args, client)
        assert type(backup.config) == Config
        assert type(backup.database) == Database
    
    def test_run_recursive_single_part(self, tmpdir):
        backup_dir = self.create_recursive_directory(tmpdir)
        args = MockArgs(tmpdir)
        args.backup_directory = backup_dir
        args.recursive = True
        client = get_stubbed_recursive_single_client()
        backup = Backup(args, client)
        backup.run(client)
        backups_1 = backup.database.get_backups(os.path.join(tmpdir, 'test_dir/sub_dir_1'))
        backups_2 = backup.database.get_backups(os.path.join(tmpdir, 'test_dir/sub_dir_2'))
        assert len(backups_1) == 1
        assert backups_1[0][6] == 0
        assert len(backups_2) == 1
        assert backups_2[0][6] == 0
    
    def test_run_recursive_multi_part(self, tmpdir):
        backup_dir = self.create_recursive_directory(tmpdir)
        args = MockArgs(tmpdir)
        args.backup_directory = backup_dir
        args.recursive = True
        client = get_stubbed_recursive_multi_part_client()
        backup = Backup(args, client)
        backup.config.max_archive_size = 128
        backup.run(client)
        backups_1 = backup.database.get_backups(os.path.join(tmpdir, 'test_dir/sub_dir_1'))
        backups_2 = backup.database.get_backups(os.path.join(tmpdir, 'test_dir/sub_dir_2'))
        assert len(backups_1) == 1
        assert backups_1[0][6] == 1
        assert len(backups_2) == 1
        assert backups_2[0][6] == 1

    def test_run_single_single_part(self, tmpdir):
        backup_dir = self.create_single_directory(tmpdir)
        args = MockArgs(tmpdir)
        args.backup_directory = backup_dir
        client = get_stubbed_single_single_client()
        backup = Backup(args, client)
        backup.run(client)
        backups = backup.database.get_backups(os.path.join(tmpdir, 'test_dir'))
        assert len(backups) == 1
        assert backups[0][6] == 0
    
    def test_run_single_multi_part(self, tmpdir):
        backup_dir = self.create_single_directory(tmpdir)
        args = MockArgs(tmpdir)
        args.backup_directory = backup_dir
        client = get_stubbed_single_multi_part_client()
        backup = Backup(args, client)
        backup.config.max_archive_size = 128
        backup.run(client)
        backups = backup.database.get_backups(os.path.join(tmpdir, 'test_dir'))
        assert len(backups) == 1
        assert backups[0][6] == 1

    def test_deleted(self, tmpdir):
        backup_dir = self.create_single_directory(tmpdir)
        args = MockArgs(tmpdir)
        args.backup_directory = backup_dir
        client = get_stubbed_deleted_client()
        backup = Backup(args, client)
        backup.run(client)
        backup.run(client)
        backup.run(client)
        backup_path = os.path.join(tmpdir, 'test_dir')
        backups = backup.database.get_backups(backup_path)
        assert len(backups) == 2
        assert backups[0][2] == 'archive-id-234'
    
    def test_exit_config_exception(self, tmpdir, caplog):
        backup_dir = self.create_single_directory(tmpdir)
        changes = {'max_archive_size': 1889}
        args = MockArgs(tmpdir, changes)
        args.backup_directory = backup_dir
        client = get_stubbed_check_client()
        with pytest.raises(SystemExit) as excinfo:
            backup = Backup(args, client)
        assert excinfo.type == SystemExit
        assert 'power of 2' in caplog.text

    def test_exit_file_exception(self, tmpdir, caplog):
        backup_dir = self.create_single_directory(tmpdir)
        changes = {'log_file': '/does/not/exist.log'}
        args = MockArgs(tmpdir, changes)
        args.backup_directory = backup_dir
        client = get_stubbed_check_client()
        with pytest.raises(SystemExit) as excinfo:
            backup = Backup(args, client)
        assert excinfo.type == SystemExit
        assert 'Cannot create' in caplog.text

    def test_exit_directory_exception(self, tmpdir, caplog):
        backup_dir = self.create_single_directory(tmpdir)
        changes = {'temp_directory': '/does/not/exist/'}
        args = MockArgs(tmpdir, changes)
        args.backup_directory = backup_dir
        client = get_stubbed_check_client()
        with pytest.raises(SystemExit) as excinfo:
            backup = Backup(args, client)
        assert excinfo.type == SystemExit
        assert 'Cannot open' in caplog.text

    def test_exit_database_exception(self, tmpdir, caplog):
        db_file_path = os.path.join(tmpdir, 'lambert.sqlite')
        with open(db_file_path, 'w+') as f:
            f.write('This is not a valid database file')
        backup_dir = self.create_single_directory(tmpdir)
        changes = {'database_file': db_file_path}
        args = MockArgs(tmpdir, changes)
        args.backup_directory = backup_dir
        client = get_stubbed_check_client()
        with pytest.raises(SystemExit) as excinfo:
            backup = Backup(args, client)
        assert excinfo.type == SystemExit
        assert 'not correctly formatted' in caplog.text

    def test_exit_upload_exception(self, tmpdir, caplog):
        backup_dir = self.create_single_directory(tmpdir)
        args = MockArgs(tmpdir)
        args.backup_directory = backup_dir
        client = get_stubbed_error_client()
        backup = Backup(args, client)
        backup.config.upload_retry_time = 0
        backup.run()
        backups = backup.database.get_backups(os.path.join(tmpdir, 'test_dir'))
        assert len(backups) == 0
