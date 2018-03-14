import os
import argparse
from .config import Config
from .backup import Backup


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--test', help='Enables test mode', action='store_true')
    parser.add_argument(
        '-v', '--verbose', help='Enables verbose output', action='store_true')
    parser.add_argument(
        '-r', '--recursive', help=('Upload each directiry within the backup directory '
            'as a separate archive'), action='store_true')
    parser.add_argument(
        '--hidden', help='Backs up hidden directories', action='store_true')
    parser.add_argument(
        '-c', '--config',
        help='Specify a config file (default in ~/.lambert/config)')
    parser.add_argument(
        '-e', '--encrypt',
        help='Specify the recipient\'s ID used for GPG encryption')
    parser.add_argument('backup_directory', help='The parent directory of the backup')
    parser.add_argument('vault_name', help='The glacier vault user for the backup')
    return parser.parse_args()


def main():
    args = get_args()
    backup = Backup(args)
    backup.run()
