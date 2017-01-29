# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from setuptools import setup

import chisel

TESTS_REQUIRE = []

setup(
    name='chisel',
    version=chisel.__version__,
    author='Craig Hobbs',
    author_email='craigahobbs@gmail.com',
    description=('JSON web APIs made dirt simple'),
    keywords='json api wsgi framework',
    url='https://github.com/craigahobbs/chisel',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['chisel'],
    test_suite='chisel.tests',
    tests_require=TESTS_REQUIRE,
    extras_require={
        'tests': TESTS_REQUIRE,
    },
)
