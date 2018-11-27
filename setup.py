# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

from setuptools import setup

import chisel

setup(
    name='chisel',
    version=chisel.__version__,
    author='Craig Hobbs',
    author_email='craigahobbs@gmail.com',
    description=('Schema-validated JSON web APIs for humans.'),
    keywords='api json framework schema wsgi',
    url='https://github.com/craigahobbs/chisel',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=['chisel'],
    test_suite='chisel.tests'
)
