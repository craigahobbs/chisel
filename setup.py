# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE

# pylint: disable=missing-function-docstring, missing-module-docstring

import os

from setuptools import setup


def main():
    # Read the readme for use as the long description
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    # Do the setup
    setup(
        name='chisel',
        description='Lightweight WSGI application framework, schema-validated JSON APIs, and API documentation.',
        long_description=long_description,
        long_description_content_type='text/x-rst',
        version='1.1.11',
        author='Craig A. Hobbs',
        author_email='craigahobbs@gmail.com',
        keywords='api json framework schema wsgi',
        url='https://github.com/craigahobbs/chisel',
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Topic :: Internet :: WWW/HTTP :: WSGI',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
            'Topic :: Software Development :: Libraries :: Application Frameworks'
        ],
        package_dir={'': 'src'},
        packages=['chisel'],
        install_requires=[
            'schema-markdown >= 1.1.12'
        ]
    )


if __name__ == '__main__':
    main()
