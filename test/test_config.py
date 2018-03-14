import os
import pytest
import yaml
import boto3
from botocore.stub import Stubber, ANY
from lambert.config import Config, ConfigException


class MockArgs():
    def __init__(self, args):
        self.backup_directory = args['backup_directory']
        self.vault_name = args['vault_name']
        self.recursive = args['recursive']
        self.hidden = args['hidden']
        self.verbose = args['verbose']
        self.test = args['test']
        self.encrypt = args['encrypt']

class TestConfig():
    def create_config_file(self, tmpdir, changes=None):
        config_values = {
            'profile': 'default',
            'temp_directory': str(tmpdir),
            'max_archive_size': '16777216',
            'db_file': os.path.join(tmpdir, 'lambert.sqlite'),
            'log_file': os.path.join(tmpdir, 'lambert.log'),
            'old_backups': '2',
            'compression_method': 'gzip'
        }
        if changes:
            for key, value in changes.items():
                config_values[key] = value
        config_file = os.path.join(tmpdir, 'config')  
        with open(config_file, 'w+') as f:
            yaml.dump(config_values, f)
        return config_file

    def get_args(self, changes=None):
        args = {
            'backup_directory': '~',
            'vault_name': 'backups',
            'recursive': False,
            'hidden': False,
            'verbose': True,
            'test': False,
            'encrypt': False
        }
        if changes:
            for key, value in changes.items():
                args[key] = value
        return MockArgs(args)

    def get_stubbed_client(self, response, expected_params, exclude=None):
        session = boto3.Session(
            aws_access_key_id='a',
            aws_secret_access_key='b',
            aws_session_token='c',
            region_name='us-west-2'
        )
        client = session.client('glacier')
        stubber = Stubber(client)
        stubber.add_response('describe_vault', response, expected_params)
        stubber.activate()
        return client

    def test_incomplete_config_file(self, tmpdir):
        config_file = os.path.join(tmpdir, 'config')  
        config_values = {
            'profile': 'profile_name',
        }
        with open(config_file, 'w+') as f:
            yaml.dump(config_values, f)
        args = self.get_args()
        with pytest.raises(ConfigException) as excinfo:
            Config(os.path.join(config_file), args)
        assert 'Config file is not formatted correctly' in str(excinfo.value)

    def test_bad_compression(self, tmpdir):
        config_file = self.create_config_file(tmpdir, {'compression_method': 'zip'})
        args = self.get_args()
        client = self.get_stubbed_client({}, {'vaultName': ANY})
        with pytest.raises(ConfigException) as excinfo:
            config = Config(config_file, args, client)
        assert 'Compression method' in str(excinfo.value)

    def test_bad_archive_size(self, tmpdir):
        config_file = self.create_config_file(tmpdir, {'max_archive_size': '16777217'})
        args = self.get_args()
        client = self.get_stubbed_client({}, {'vaultName': ANY})
        with pytest.raises(ConfigException) as excinfo:
            config = Config(config_file, args, client)
        assert 'archive size' in str(excinfo.value)

    def test_bad_old_backups(self, tmpdir):
        config_file = self.create_config_file(tmpdir, {'old_backups': 'abc'})
        args = self.get_args()
        client = self.get_stubbed_client({}, {'vaultName': ANY})
        with pytest.raises(ConfigException) as excinfo:
            config = Config(config_file, args, client)
        assert 'not formatted' in str(excinfo.value)

    def test_bad_encryption(self, tmpdir):
        config_file = self.create_config_file(tmpdir)
        args = self.get_args({'encrypt': 'nonexistant@address.baddomain'})
        client = self.get_stubbed_client({}, {'vaultName': ANY})
        with pytest.raises(ConfigException) as excinfo:
            config = Config(config_file, args, client)
        assert 'Encryption ID' in str(excinfo.value)

    def test_good_encryption(self, tmpdir):
        config_file = self.create_config_file(tmpdir)
        args = self.get_args({'encrypt': 'lambert_test'})
        client = self.get_stubbed_client({}, {'vaultName': ANY})
        config = Config(config_file, args, client)
        assert type(config) == Config
        assert config.encrypted == 'lambert_test'

    def test_init(self, tmpdir):
        config_file = self.create_config_file(tmpdir)
        args = self.get_args()
        client = self.get_stubbed_client({}, {'vaultName': ANY})
        config = Config(config_file, args, client)
        assert type(config) == Config
        assert config.encrypted == ''
