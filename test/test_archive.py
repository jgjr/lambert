import os
import sys
import pytest
import subprocess
from lambert.directory import Directory
from lambert.backupdirectory import BackupDirectory
from lambert.archive import Archive, ArchiveException

class MockConfig():
    def __init__(self, tmpdir):
        self.max_archive_size = 8388608
        self.temp_directory = Directory(str(tmpdir))
        self.encrypted = ''
        self.compression_method = 'gz'

class TestArchive():
    def create_directory(self, tmpdir):
        test_dir = os.path.join(tmpdir, 'test_dir')
        os.mkdir(test_dir)
        with open(os.path.join(test_dir, 'file1'), 'w+') as f:
            f.write('here is my content')
        with open(os.path.join(test_dir, 'file2'), 'w+') as f:
            f.write('here is more of my content')
        return test_dir

    def create_archive(self, tmpdir, encrypted=''):
        test_dir = self.create_directory(tmpdir)
        config = MockConfig(tmpdir)
        config.encrypted = encrypted
        backup_directory = BackupDirectory(test_dir)
        archive = Archive(backup_directory, config)
        return (backup_directory, archive)

    def test_init(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir)
        filecount = 0
        for filename in os.listdir(tmpdir):
            print(filename)
            if backup_directory.archive_name in filename:
                filecount += 1
        assert filecount == 1

    def test_encrypted_init(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir, 'lambert_test')
        filecount = 0
        for filename in os.listdir(tmpdir):
            print(filename)
            if backup_directory.archive_name in filename and 'gpg' in filename:
                filecount += 1
        assert filecount == 1

    def test_bad_encrypted_init(self, tmpdir):
        with pytest.raises(ArchiveException) as excinfo:
            backup_directory, archive = self.create_archive(tmpdir, 'nonexistant@address.baddomain')
        assert 'could not be created' in str(excinfo.value)

    def test_size(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir)
        assert archive.size > 0

    def test_get_part_size(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir)
        assert archive.get_part_size(0) > 0

    def test_get_data(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir)
        data = archive.get_data(0)
        assert sys.getsizeof(data) > 0

    def test_get_file_object(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir)
        file_object = archive.get_file_object()
        assert len(file_object.read()) > 0

    def test_remove(self, tmpdir):
        backup_directory, archive = self.create_archive(tmpdir)
        archive.remove()
        filecount = 0
        for filename in os.listdir(tmpdir):
            if backup_directory.archive_name in filename:
                filecount += 1
        assert filecount == 0
