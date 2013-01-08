#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import os
from setuptools import setup

# Utility function to read the README file
def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), "rb") as fh:
        return fh.read()

setup(
    name = "chisel",
    version = "0.1.3",
    author = "Craig Hobbs",
    author_email = "craigahobbs@gmail.com",
    description = ("Chisel - JSON web APIs made dirt simple"),
    long_description = read("README.txt"),
    keywords = "json api server framework",
    license = "MIT",
    classifiers = [
        "Environment :: Web Environment",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7"
        ],
    packages = [
        "chisel",
        "chisel/resource",
        "chisel/tests",
        "chisel/tests/resource"
        ],
    package_data = {
        "chisel/test": [
            "test_api_files/*",
            "test_app_files/*"
            ]
        },
    test_suite = "chisel.tests"
    )
