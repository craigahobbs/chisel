# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

import re
import os

from setuptools import setup

PACKAGE_NAME = MODULE_NAME = 'chisel'

def main():
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', MODULE_NAME, '__init__.py'), encoding='utf-8') as init_file:
        version = re.search(r"__version__ = '(.+?)'", init_file.read()).group(1)
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    setup(
        name=PACKAGE_NAME,
        description=('Schema-validated JSON web APIs for humans.'),
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
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7'
        ],
        package_dir={'': 'src'},
        packages=[MODULE_NAME],
        test_suite='tests'
    )

if __name__ == '__main__':
    main()
