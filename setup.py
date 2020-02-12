# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

import re
import os

from setuptools import setup

PACKAGE_NAME = MODULE_NAME = 'chisel'
TESTS_REQUIRE = []

def main():
    """
    TODO
    """

    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', MODULE_NAME, '__init__.py'), encoding='utf-8') as init_file:
        version = re.search(r"__version__ = '(.+?)'", init_file.read()).group(1)
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    setup(
        name=PACKAGE_NAME,
        description=('Lightweight WSGI application framework, schema-validated JSON APIs, and API documentation.'),
        long_description=long_description,
        long_description_content_type='text/markdown',
        version=version,
        author='Craig Hobbs',
        author_email='craigahobbs@gmail.com',
        keywords='api json framework schema wsgi',
        url='https://github.com/craigahobbs/chisel',
        license='MIT',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Topic :: Internet :: WWW/HTTP :: WSGI',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
            'Topic :: Software Development :: Libraries :: Application Frameworks'
        ],
        package_dir={'': 'src'},
        packages=[MODULE_NAME],
        package_data={
            '': [
                'static/chisel.js',
                'static/doc.css',
                'static/doc.html',
                'static/doc.js'
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
