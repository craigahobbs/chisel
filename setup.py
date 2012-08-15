#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import os
from setuptools import setup

# Utility function to read the README file
def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), 'rb') as fh:
        return fh.read()

setup(
    name = "wads",
    version = "0.1.0",
    author = "Craig Hobbs",
    author_email = "craigahobbs@gmail.com",
    description = ("Web APIs Dirt-Simple (WADS)"),
    keywords = "json api server framework",
    packages = ['wads'],
    long_description = read('README.txt')
    )
