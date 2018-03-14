import os
import pytest
from lambert.directory import Directory, DirectoryException

class TestDirectory():
    def test_non_existant(self, tmpdir):
        with pytest.raises(DirectoryException) as excinfo:
            Directory(os.path.join(tmpdir, 'non-existant-directory'))
        assert 'Cannot open' in str(excinfo.value)

    def test_bad_permissions(self, tmpdir):
        test_dir = os.path.join(tmpdir, 'dirname/')  
        os.mkdir(test_dir)
        os.chmod(test_dir, 0000)
        with pytest.raises(DirectoryException) as excinfo:
            Directory(test_dir, 'dirname')
        assert 'Cannot open' in str(excinfo.value)

    def test_bad_write_permissions(self, tmpdir):
        test_dir = os.path.join(tmpdir, 'dirname/')  
        os.mkdir(test_dir)
        os.chmod(test_dir, 0o400)
        with pytest.raises(DirectoryException) as excinfo:
            Directory(test_dir, writable=True)
        assert 'Cannot write' in str(excinfo.value)

    def test_good_directory(self, tmpdir):
        dir_path = os.path.join(tmpdir, 'dirname')  
        os.mkdir(dir_path)
        os.chmod(dir_path, 0o400)
        test_dir = Directory(dir_path, writable=False)
        assert dir_path in test_dir.path

    def test_good_write_directory(self, tmpdir):
        dir_path = os.path.join(tmpdir, 'dirname')  
        os.mkdir(dir_path)
        os.chmod(dir_path, 0o700)
        test_dir = Directory(dir_path, writable=True)
        assert dir_path in test_dir.path

