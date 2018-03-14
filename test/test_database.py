import os
import pytest
import sqlite3
from lambert.file import File
from lambert.database import Database, DatabaseException

class TestDatabase():
    def test_bad_db_file(self, tmpdir):
        db_file_path = os.path.join(tmpdir, 'lambert.sqlite')
        with open(db_file_path, 'w+') as f:
            f.write('This is not a valid database file')
        db_file = File(db_file_path, writable=True) 
        with pytest.raises(DatabaseException) as excinfo:
            Database(db_file)
        assert 'not correctly formatted' in str(excinfo.value)

    def test_bad_db_schema(self, tmpdir):
        db_file_path = os.path.join(tmpdir, 'lambert.sqlite')
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.execute(("CREATE TABLE backups"
                "(id INTEGER PRIMARY KEY ASC, directory TEXT, archive_id TEXT,"
                "vault TEXT, location TEXT, encrypted TEXT, multi_part INTEGER, size INTEGER,"
                "deleted INTEGER, date INTEGER);"))
        db_file = File(db_file_path, writable=True) 
        with pytest.raises(DatabaseException) as excinfo:
            Database(db_file)
        assert 'incorrect schema' in str(excinfo.value)

    def test_good_db_file(self, tmpdir):
        db_file_path = os.path.join(tmpdir, 'lambert.sqlite')
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.execute(("CREATE TABLE backups"
                "(id INTEGER PRIMARY KEY ASC, directory TEXT, archive_id TEXT,"
                "vault TEXT, location TEXT, encrypted TEXT, multi_part INTEGER, size INTEGER,"
                "deleted INTEGER, date TEXT);"))
        db_file = File(db_file_path, writable=True) 
        database = Database(db_file)
        assert type(database) == Database

    def test_write_db_entry(self, tmpdir):
        data = {
            'directory': '/path/to/directory',
            'archive_id': 'VsjYaAN5LPMg7D1jITg',
            'vault': 'vault_name',
            'location': '/glacier/archive/location',
            'encrypted': '',
            'multi_part': 0,
            'size': 10000, 
            'deleted': 0
        }
        database = Database(File(os.path.join(tmpdir, 'lambert.sqlite')))
        database.write_entry(data)
        db_file = database.file.path
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM backups")
        result = cursor.fetchone()
        for key, value in data.items():
            assert value in result

    def test_get_backups(self, tmpdir):
        b1 = {
            'directory': '/path/to/directory',
            'archive_id': 'VsjYaAN5LPMg7D1jITg',
            'vault': 'vault_name',
            'location': '/glacier/archive/location',
            'encrypted': '',
            'multi_part': 0,
            'size': 10000, 
            'deleted': 1
        }
        b2 = {
            'directory': '/path/to/directory',
            'archive_id': 'VsjYaAN5LPMg7D1jITg',
            'vault': 'vault_name',
            'location': '/glacier/archive/location',
            'encrypted': '',
            'multi_part': 0,
            'size': 10000, 
            'deleted': 0
        }
        b3 = {
            'directory': '/path/to/directory',
            'archive_id': 'VsjYaAN5LPMg7D1jITg',
            'vault': 'vault_name',
            'location': '/glacier/archive/location',
            'encrypted': '',
            'multi_part': 0,
            'size': 10000, 
            'deleted': 0
        }
        database = Database(File(os.path.join(tmpdir, 'lambert.sqlite')))
        database.write_entry(b1)
        database.write_entry(b2)
        database.write_entry(b3)
        results = database.get_backups('/path/to/directory')
        for key, value in b2.items():
            assert value in results[0]
        for key, value in b3.items():
            assert value in results[1]

    def test_delete_backup(self, tmpdir):
        data = {
            'directory': '/path/to/directory',
            'archive_id': 'VsjYaAN5LPMg7D1jITg',
            'vault': 'vault_name',
            'location': '/glacier/archive/location',
            'encrypted': '',
            'multi_part': 0,
            'size': 10000, 
            'deleted': 0
        }
        database = Database(File(os.path.join(tmpdir, 'lambert.sqlite')))
        database.write_entry(data)
        database.delete_backup(data['archive_id'])
        results = database.get_backups('/path/to/directory')
        assert len(results) == 0
