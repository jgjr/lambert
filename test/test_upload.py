import os
import pytest
import boto3
from botocore.stub import Stubber, ANY
from lambert.archive import Archive
from lambert.directory import Directory
from lambert.backupdirectory import BackupDirectory
from lambert.upload import Upload, UploadException

class MockConfig():
    def __init__(self, tmpdir):
        self.vault_name = 'vault_name'
        self.max_archive_size = 8388608
        self.temp_directory = Directory(str(tmpdir))
        self.encrypted = ''
        self.compression_method = 'gz'
        self.upload_retry_time = 0


class TestUpload():
    def create_archive(self, tmpdir, multi_part=False):
        test_dir = os.path.join(tmpdir, 'test_dir')
        os.mkdir(test_dir)
        with open(os.path.join(test_dir, 'file1'), 'w+') as f:
            f.write('here is my content')
        with open(os.path.join(test_dir, 'file2'), 'w+') as f:
            f.write('here is more of my content')
        config = MockConfig(tmpdir)
        if multi_part:
            config.max_archive_size = 128
        backup_directory = BackupDirectory(test_dir)
        archive = Archive(backup_directory, config)
        return archive

    def get_stubbed_single_client(self):
        session = boto3.Session(
            aws_access_key_id='a',
            aws_secret_access_key='b',
            aws_session_token='c',
            region_name='us-west-2'
        )
        client = session.client('glacier')
        stubber = Stubber(client)
        stubber.add_response('upload_archive', {
                'location': '/path/to/archive',
                'archiveId': 'archive-id-123'
            }, {
                'vaultName': ANY,
                'archiveDescription': ANY,
                'body': ANY
            })
        stubber.activate()
        return client

    def get_stubbed_multi_part_client(self):
        session = boto3.Session(
            aws_access_key_id='a',
            aws_secret_access_key='b',
            aws_session_token='c',
            region_name='us-west-2'
        )
        client = session.client('glacier')
        stubber = Stubber(client)
        stubber.add_response('initiate_multipart_upload', {
                'uploadId': 'upload-id-456'
            }, {
                'vaultName': ANY,
                'partSize': ANY,
                'archiveDescription': ANY
            })
        stubber.add_response('upload_multipart_part', {
                'checksum': 'string'
            }, {
                'vaultName': ANY,
                'uploadId': ANY,
                'body': ANY,
                'range': ANY
            })
        stubber.add_response('upload_multipart_part', {
                'checksum': 'string'
            }, {
                'vaultName': ANY,
                'uploadId': ANY,
                'body': ANY,
                'range': ANY
            })
        stubber.add_response('complete_multipart_upload', {
                'location': '/path/to/multi_archive',
                'archiveId': 'archive-id-456'
            }, {
                'vaultName': ANY,
                'uploadId': ANY,
                'archiveSize': ANY,
                'checksum': ANY,
            })
        stubber.activate()
        return client

    def get_stubbed_error_client(self):
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

    def test_single_part_upload(self, tmpdir):
        archive = self.create_archive(tmpdir)
        client = self.get_stubbed_single_client()
        config = MockConfig(tmpdir)
        upload = Upload(archive, config, client)
        assert upload.location == '/path/to/archive'
        assert upload.archive_id == 'archive-id-123'

    def test_multi_part_upload(self, tmpdir):
        archive = self.create_archive(tmpdir, multi_part=True)
        client = self.get_stubbed_multi_part_client()
        config = MockConfig(tmpdir)
        upload = Upload(archive, config, client)
        assert upload.location == '/path/to/multi_archive'
        assert upload.archive_id == 'archive-id-456'

    def test_error_upload(self, tmpdir):
        archive = self.create_archive(tmpdir)
        client = self.get_stubbed_error_client()
        config = MockConfig(tmpdir)
        with pytest.raises(UploadException) as excinfo:
            upload = Upload(archive, config, client)
        assert excinfo.type == UploadException

