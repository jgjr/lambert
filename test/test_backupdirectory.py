import os
import pytest
import subprocess
from datetime import date
from lambert.backupdirectory import BackupDirectory

class TestBackupDirectory():
    def test_init(self, tmpdir):
        test_dir = os.path.join(tmpdir, 'Test dir')
        os.mkdir(test_dir)
        backup_directory = BackupDirectory(test_dir)
        assert backup_directory.name == 'Test dir'
        assert 'test-dir' in backup_directory.archive_name 
        assert date.today().isoformat() in backup_directory.archive_name 
