# Lambert
Lambert is a command line backup utility for [AWS Glacier](https://aws.amazon.com/glacier/) written in Python. You specify a directory and a Glacier vault as a command line arguments, along with several other optional flags. Other options are set in a config file. Every archive uploaded is recorded in an sqlite3 database, so that archives can be deleted or downloaded without having to wait for an inventory from Amazon.

## Installation
The python modules required to run lambert are in the requirements.txt file. Lambert will also require a [valid profile](http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html) in the ~/.aws/credentials file as well as a [valid region](http://docs.aws.amazon.com/general/latest/gr/rande.html) in the ~/.aws/config file for the [boto3 module](https://github.com/boto/boto3) to work.
A YAML formatted configuration file needs to either be specified with the -c argument, or located at ~/.lambert/config. An example configuration file can be found in this repository (config.sample). The database and log file do not need to have been created prior to running lambert, as long as their parent directory has write permissions.
This has only been tested on Linux systems running python 3.6, as it has been developed mainly as a way to backup content on web servers in a cron job.
`python setup.py install` or `pip install .` should install Lambert on your system. Various other options can be supplied to these commands, please see their documentation for a full list.
* [setup.py](https://docs.python.org/3.6/install/index.html)
* [pip](https://pip.pypa.io/en/stable/installing/)

## The config file
Various options are set in the config file. They are:
* profile - your chosen AWS profile (located in the ~/.aws/credentials file)
* temp_directory - where to store the archive while it is being uploaded
* max_archive_size - the maximum size of a part to upload to Glacier. This must be a power of 2, e.g. 8388608, 16777216
* db_file - the file to use as an sqlite3 database, which does not need to exist already
* log_file - the file to use as a log, which does not need to exist already
* old_backups - the number of old backups of each directory to keep on Glacier
* compression_method - the method of compression to use when creating the archive, the options are:
    - lzop (fastest, least compression)
    - gzip (fast, more compression)
    - bzip2 (slow, even more compression)
    - lzma (slowest, most compression)
[Source for comparison](https://binfalse.de/2011/04/04/comparison-of-compression/)


## Usage
There are two required command line argument, the backup directory and the Glacier vault. The three other optional arguments are:
* -c / --config - allows you to specify a config file other than ~/.lambert/config
* -r / --recursive - without this argument, only the chosen backup directory is archived and uploaded, with this argument its children are each archived and uploaded individually
* -e / encrypt <valid GPG id> - this option will encrypt the archive if a valid public key for the GPG id (often an email address) is found on your system.
* -t / --test - runs lambert in test mode. This performs all the checks before the backup process occurs and lists the directories that will be uploaded to Glacier in the log file.
* -v / --verbose - the log generated with running Lambert will have a greater level of detail.
* --hidden - hidden directories will also be archived. 

Example executions:

```
python -m lambert ~/documents/projects/ project_backup
python -m lambert -vr ~/documents/projects/ project_backup
python -m lambert -e email@address.com ~/documents/projects/ project_backup
python -m lambert -v -c ~/documents/backups/lambertconfig.yml ~/documents/projects/ project_backup
```

If a .lambert_ignore file is found in the root of the backup and a recursive flag has been specified, the directories listed in that file will not be archived and uploaded to Glacier. 
No output is printed to the screen when running Lambert. If you would like to keep an eye on the progress of your backup you can run 'tail -f ~/.lambert/lambert.log' (and replace the path with the path to your log file).

## Testing
Tests can be run with the command `pytest test/`. A GPG key with the ID 'lambert_test' will need to be present in order to run the tests successfully.

## The backup process
When Lambert runs it performs the following steps:
* Parses the config variables, either from the file specified with the -c argument or from the .lambert/config file
* Checks that the AWS credentials supplied are valid and that a connection can be made to Glacier
* Connects to or creates the sqlite3 database
* Sets up the log with the desired level of detail (specify the -v option for greater detail)
* Performs a backup of each directory specified (only one if not used in recursive mode)
    - Creates an archive of the directory
    - Uploads either the entire archive or its parts one-by-one to Glacier
    - Creates a database entry with the directory name, archive id and location (from the Glacier response), size, and date
    - Deletes the archive from the temporary directory
    - Looks through the database and sends a delete request to Glacier for the old backups (the number of old backups to keep is set in the config file)
And that's it!

## Why the name?
The [Lambert Glacier](https://en.wikipedia.org/wiki/Lambert_Glacier) is the world's largest glacier.
