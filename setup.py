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
    version = "0.1.0",
    author = "Craig Hobbs",
    author_email = "craigahobbs@gmail.com",
    description = ("Chisel - JSON web APIs made dirt simple"),
    keywords = "json api server framework",
    packages = [
        "chisel",
        "chisel/resource",
        "chisel/test",
        "chisel/test/resource"
        ],
    package_data = {
        "chisel/test": [
            "test_api_files/*",
            "test_app_files/*"
            ]
        },
    long_description = read("README.txt")
    )
