import os
import pytest
from lambert.directory import Directory
from lambert.backuproot import BackupRoot

class MockConfig():
    def __init__(self, tmpdir, backup_dir):
        self.temp_directory = Directory(tmpdir)
        self.backup_directory = backup_dir
        self.hidden = False

class TestBackupRoot():
    def test_children(self, tmpdir):
        backup_dir = os.path.join(tmpdir, 'backup_dir')
        os.mkdir(backup_dir)
        os.mkdir(os.path.join(backup_dir, 'dir1'))
        os.mkdir(os.path.join(backup_dir, 'dir2'))
        config = MockConfig(tmpdir, backup_dir)
        backup_root = BackupRoot(config)
        dir1 = os.path.abspath(os.path.join(backup_dir, 'dir1'))
        dir2 = os.path.abspath(os.path.join(backup_dir, 'dir2'))
        for child_dir in [dir1, dir2]:
            assert child_dir in backup_root.children

    def test_ignore_child(self, tmpdir):
        backup_dir = os.path.join(tmpdir, 'backup_dir')
        os.mkdir(backup_dir)
        os.mkdir(os.path.join(backup_dir, 'dir1'))
        os.mkdir(os.path.join(backup_dir, 'dir2'))
        os.mkdir(os.path.join(backup_dir, 'dir3'))
        os.mkdir(os.path.join(backup_dir, 'dir4'))
        with open(os.path.join(backup_dir, '.lambert_ignore'), 'w+') as f:
            f.write('dir2\ndir4/')
        config = MockConfig(tmpdir, backup_dir)
        backup_root = BackupRoot(config)
        dir1 = os.path.abspath(os.path.join(backup_dir, 'dir1'))
        dir2 = os.path.abspath(os.path.join(backup_dir, 'dir2'))
        dir3 = os.path.abspath(os.path.join(backup_dir, 'dir3'))
        dir4 = os.path.abspath(os.path.join(backup_dir, 'dir4'))
        assert dir1 in backup_root.children
        assert dir2 not in backup_root.children
        assert dir3 in backup_root.children
        assert dir4 not in backup_root.children

    def test_no_hidden(self, tmpdir):
        backup_dir = os.path.join(tmpdir, 'backup_dir')
        os.mkdir(backup_dir)
        os.mkdir(os.path.join(backup_dir, 'dir1'))
        os.mkdir(os.path.join(backup_dir, '.dir2'))
        os.mkdir(os.path.join(backup_dir, 'dir3'))
        os.mkdir(os.path.join(backup_dir, '.dir4'))
        config = MockConfig(tmpdir, backup_dir)
        backup_root = BackupRoot(config)
        dir1 = os.path.abspath(os.path.join(backup_dir, 'dir1'))
        dir2 = os.path.abspath(os.path.join(backup_dir, '.dir2'))
        dir3 = os.path.abspath(os.path.join(backup_dir, 'dir3'))
        dir4 = os.path.abspath(os.path.join(backup_dir, '.dir4'))
        assert dir1 in backup_root.children
        assert dir2 not in backup_root.children
        assert dir3 in backup_root.children
        assert dir4 not in backup_root.children

    def test_hidden(self, tmpdir):
        backup_dir = os.path.join(tmpdir, 'backup_dir')
        os.mkdir(backup_dir)
        os.mkdir(os.path.join(backup_dir, 'dir1'))
        os.mkdir(os.path.join(backup_dir, '.dir2'))
        os.mkdir(os.path.join(backup_dir, 'dir3'))
        os.mkdir(os.path.join(backup_dir, '.dir4'))
        config = MockConfig(tmpdir, backup_dir)
        config.hidden = True
        backup_root = BackupRoot(config)
        dir1 = os.path.abspath(os.path.join(backup_dir, 'dir1'))
        dir2 = os.path.abspath(os.path.join(backup_dir, '.dir2'))
        dir3 = os.path.abspath(os.path.join(backup_dir, 'dir3'))
        dir4 = os.path.abspath(os.path.join(backup_dir, '.dir4'))
        assert dir1 in backup_root.children
        assert dir2 in backup_root.children
        assert dir3 in backup_root.children
        assert dir4 in backup_root.children

