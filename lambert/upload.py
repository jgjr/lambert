import boto3
import botocore
import logging
import time
import hashlib

class UploadException(Exception):
    '''
    Exceptions related to the Upload class that result 
    in the skipping of the backup of 1 directory.
    '''
    pass


class Upload():
    '''
    Handles the interaction with Glacier.
    Single part uploads call the upload_archive() function.
    Multi-part uploads call the initiate_multipart_upload(),
    upload_multipart_part() and complete_multipart_upload()
    functions. 
    '''
    def __init__(self, archive, config, client=None):
        if client:
            self.client = client
        else:
            self.session = boto3.Session(profile_name=config.profile)
            self.client = self.session.client('glacier')
        self.archive = archive
        self.config = config
        self.upload()

    def upload(self):
        if self.archive.multi_part:
            logging.debug(
                f'Starting multi-part upload for {self.archive.name}')
            self.multi_part_upload()

        else:
            logging.debug(
                f'Starting single-part upload for {self.archive.name}')
            self.single_part_upload()
        logging.info(f'Upload of {self.archive.name} complete')

    def single_part_upload(self, attempt=1):
        try:
            single_part_response = self.client.upload_archive(
                vaultName = self.config.vault_name,
                archiveDescription = (
                    f'Directory: {self.archive.backup_directory.path}. '
                    f'Archive: {self.archive.name}'),
                body = self.archive.get_file_object(),
            )
            self.location = single_part_response['location']
            self.archive_id = single_part_response['archiveId']
        except(botocore.exceptions.BotoCoreError, 
            boto3.exceptions.Boto3Error,
            botocore.exceptions.ClientError,
            botocore.vendored.requests.exceptions.ConnectTimeout,
            botocore.exceptions.ConnectionClosedError):
            if attempt <= 10:
                time.sleep(self.config.upload_retry_time)
                attempt += 1
                logging.debug(
                    f'Retrying upload of {self.archive.name} '
                    f'- attempt {attempt}')
                self.single_part_upload(attempt)
            else:
                raise UploadException(
                    f'Cannot upload {self.archive.name}')

    def multi_part_upload(self):
        self.checksums = []
        self.initiate_upload()
        for part in range(self.archive.parts):
            self.upload_part(part)
        self.complete_upload()

    def initiate_upload(self, attempt=1):
        try:
            initiate_response = self.client.initiate_multipart_upload(
                vaultName = self.config.vault_name,
                partSize = str(self.config.max_archive_size),
                archiveDescription = (
                    f'Directory: {self.archive.backup_directory.path}. '
                    f'Archive: {self.archive.name}')
            )
            self.upload_id = initiate_response['uploadId']
        except(botocore.exceptions.BotoCoreError, 
            boto3.exceptions.Boto3Error,
            botocore.exceptions.ClientError,
            botocore.vendored.requests.exceptions.ConnectTimeout,
            botocore.exceptions.ConnectionClosedError):
            if attempt <= 10:
                time.sleep(self.config.upload_retry_time)
                attempt += 1
                logging.debug(f'Retrying initiation of {self.archive.name}')
                self.initiate_upload(attempt)
            else:
                raise UploadException(
                    f'Cannot initiate upload for {self.archive.name}')

    def upload_part(self, part, attempt=1):
        start = part * self.config.max_archive_size
        end = start + self.archive.get_part_size(part) - 1
        try:
            logging.debug((
                f'Attempting upload of part {part + 1}/'
                f'{self.archive.parts} of {self.archive.name}'))
            upload_response = self.client.upload_multipart_part(
                vaultName = self.config.vault_name,
                uploadId = self.upload_id,
                range = f'bytes {start}-{end}/*',
                body = self.archive.get_data(part)
            )
            logging.debug((
                f'Uploaded part {part + 1}/{self.archive.parts} '
                f'of {self.archive.name}'))
        except(botocore.exceptions.BotoCoreError, 
            boto3.exceptions.Boto3Error,
            botocore.exceptions.ClientError,
            botocore.vendored.requests.exceptions.ConnectTimeout,
            botocore.exceptions.ConnectionClosedError):
            if attempt <= 10:
                time.sleep(self.config.upload_retry_time)
                attempt += 1
                logging.debug((
                    f'Retrying upload of {self.archive.name} part {part + 1} '
                    f'- attempt {attempt}'))
                self.upload_part(part, attempt)
            else:
                raise UploadException(
                    f'Cannot upload {self.archive.name} part {part + 1}')

    def complete_upload(self, attempt=1):
        try:
            checksum = botocore.utils.calculate_tree_hash(
                self.archive.get_file_object()) 
            complete_response = self.client.complete_multipart_upload(
                vaultName = self.config.vault_name,
                uploadId = self.upload_id,
                archiveSize = str(self.archive.size),
                checksum = checksum
            )
            self.location = complete_response['location']
            self.archive_id = complete_response['archiveId']
        except(botocore.exceptions.BotoCoreError, 
            boto3.exceptions.Boto3Error,
            botocore.exceptions.ClientError,
            botocore.vendored.requests.exceptions.ConnectTimeout,
            botocore.exceptions.ConnectionClosedError):
            if attempt <= 10:
                time.sleep(self.config.upload_retry_time)
                attempt += 1
                logging.debug(f'Retrying completion of {self.archive.name}')
                self.complete_upload(attempt)
            else:
                raise UploadException(
                    f'Cannot upload {self.archive.name}')
