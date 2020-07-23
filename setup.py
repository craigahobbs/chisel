# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
The package build script
"""

import re
import os

from setuptools import setup

MODULE_NAME = 'chisel'
PACKAGE_NAME = MODULE_NAME
TESTS_REQUIRE = []

def main():
    """
    The package build script's main entry point
    """

    # Read the package version
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', MODULE_NAME, '__init__.py'), encoding='utf-8') as init_file:
        version = re.search(r"__version__ = '(.+?)'", init_file.read()).group(1)

    # Read the readme for use as the long description
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    # Do the setup
    setup(
        name=PACKAGE_NAME,
        description=('Light-weight WSGI application framework, schema-validated JSON APIs, and API documentation.'),
        long_description=long_description,
        long_description_content_type='text/x-rst',
        version=version,
        author='Craig Hobbs',
        author_email='craigahobbs@gmail.com',
        keywords='api json framework schema wsgi',
        url='https://github.com/craigahobbs/' + PACKAGE_NAME,
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Topic :: Internet :: WWW/HTTP :: WSGI',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
            'Topic :: Software Development :: Libraries :: Application Frameworks'
        ],
        package_dir={
            '': 'src'
        },
        packages=[MODULE_NAME],
        package_data={
            '': [
                'static/*'
            ]
        },
        test_suite='tests',
        tests_require=TESTS_REQUIRE,
        extras_require={
            'tests': TESTS_REQUIRE
        }
    )

if __name__ == '__main__':
    main()
