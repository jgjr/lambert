import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Lambert",
    version = "0.1",
    author = "John Greenwood",
    author_email = "john@greenwoodlomax.com",
    description = ("A command line backup utility for AWS Glacier written in Python"),
    license = "GPL-3.0",
    keywords = "AWS Glacier backup boto3",
    url = "https://github.com/jgjr/lambert",
    packages=['lambert', 'test'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
