import os
import pytest
from lambert.file import File, FileException

class TestFile():
    def test_non_existant_directory(self, tmpdir):
        with pytest.raises(FileException) as excinfo:
            File(os.path.join(tmpdir, 'non-existant-directory/file'))
        assert 'invalid directory' in str(excinfo.value)

    def test_non_existant_file(self, tmpdir):
        with pytest.raises(FileException) as excinfo:
            File(os.path.join(tmpdir, 'non-existant-file'), must_exist=True)
        assert 'Cannot locate' in str(excinfo.value)

    def test_bad_permissions_directory(self, tmpdir):
        test_dir = os.path.join(tmpdir, 'dirname/')  
        test_file = os.path.join(test_dir, 'filename')
        os.mkdir(test_dir)
        os.chmod(test_dir, 0000)
        with pytest.raises(FileException) as excinfo:
            File(test_file)
        assert 'Cannot create' in str(excinfo.value)

    def test_bad_permissions_file(self, tmpdir):
        test_file = os.path.join(tmpdir, 'filename')  
        open(test_file, 'w+').close()
        os.chmod(test_file, 0000)
        with pytest.raises(FileException) as excinfo:
            File(test_file)
        assert 'Cannot open' in str(excinfo.value)

    def test_bad_write_permissions_file(self, tmpdir):
        test_file = os.path.join(tmpdir, 'filename')  
        open(test_file, 'w+').close()
        os.chmod(test_file, 0o400)
        with pytest.raises(FileException) as excinfo:
            File(test_file, must_exist=True, writable=True)
        assert 'Cannot write' in str(excinfo.value)

    def test_create_file(self, tmpdir):
        file_path = os.path.join(tmpdir, 'test_file')
        new_file = File(file_path, must_exist=False)
        assert new_file.path == file_path

    def test_existing_file(self, tmpdir):
        file_path = os.path.join(tmpdir, 'test_file')
        open(file_path, 'w+').close()
        os.chmod(file_path, 0o400)
        existing_file = File(file_path, must_exist=True, writable=False)
        assert existing_file.path == file_path

    def test_write_existing_file(self, tmpdir):
        file_path = os.path.join(tmpdir, 'test_file')
        open(file_path, 'w+').close()
        os.chmod(file_path, 0o700)
        existing_file = File(file_path, must_exist=True, writable=True)
        assert existing_file.path == file_path
