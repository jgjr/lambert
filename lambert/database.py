import sqlite3
import logging
from datetime import datetime
from .file import File


class DatabaseException(Exception):
    '''
    Exceptions related to the database that 
    will cause the application to exit
    '''
    pass


class Database():
    '''This class handles the connection with the sqlite3 database.'''
    def __init__(self, db_file):
        '''
        Takes an instance of the File class as an argument.
        The file does not have to exist, but it will raise an error
        if it does exist and is not a sqlite database, or if there
        is an existing 'backups' table with an incorrect schema.
        '''
        self.table_name = 'backups'
        self.columns = [
            ('id', 'INTEGER PRIMARY KEY ASC'),
            ('directory', 'TEXT'),
            ('archive_id', 'TEXT'),
            ('vault', 'TEXT'),
            ('location', 'TEXT'),
            ('encrypted', 'TEXT'),
            ('multi_part', 'INTEGER'),
            ('size', 'INTEGER'),
            ('deleted', 'INTEGER'),
            ('date', 'TEXT'),
        ]
        self.file = db_file
        self.connect_db_file()
        if self.has_backups_table():
            self.check_backups_table()
        else:
            self.create_backups_table()
        logging.debug('Initialized database')

    def connect_db_file(self):
        try:
            self.conn = sqlite3.connect(self.file.path)
            self.cursor = self.conn.cursor()
        except sqlite3.OperationalError:
            raise DatabaseException('Unable to open database file')

    def has_backups_table(self):
        try:
            self.cursor.execute((
                'SELECT sql FROM sqlite_master '
                'WHERE type="table" AND name="backups";'))
            return bool(len(self.cursor.fetchall()))
        except sqlite3.DatabaseError:
            raise DatabaseException(
                'Database file is not correctly formatted')

    def check_backups_table(self):
        self.cursor.execute((
            'SELECT sql FROM sqlite_master '
            'WHERE type="table" AND name="backups";'))
        self.conn.commit()
        schema = self.cursor.fetchone()[0]
        for column in self.columns:
            if ' '.join(column) not in schema:
                raise DatabaseException('Backups table has incorrect schema')

    def create_backups_table(self):
        columns = []
        for column in self.columns:
            columns.append(" ".join(column))
        command = (f'CREATE TABLE {self.table_name} ('
            f'{", ".join(columns)});')
        self.cursor.execute(command)
        self.conn.commit()

    def write_entry(self, data):
        self.cursor.execute((
            'INSERT INTO backups '
            '(directory, archive_id, vault, location,'
            'multi_part, encrypted, size, deleted, date)'
            'VALUES(?,?,?,?,?,?,?,?,?);'), (
                data['directory'],
                data['archive_id'],
                data['vault'],
                data['location'],
                data['multi_part'],
                data['encrypted'],
                data['size'],
                data['deleted'],
                datetime.now().isoformat(' ')
            ))
        self.conn.commit()

    def get_backups(self, directory):
        backups = self.cursor.execute(('SELECT * FROM backups WHERE '
            'directory=? AND deleted=0 ORDER BY date ASC'),
            (directory,)).fetchall()
        return backups

    def delete_backup(self, archive_id):
        self.cursor.execute(
            'UPDATE backups SET deleted=1 WHERE archive_id=?', (archive_id,))
        self.conn.commit()

