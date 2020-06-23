# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

import os
from tempfile import TemporaryDirectory
import unittest


class TestCase(unittest.TestCase):
    """
    TODO
    """

    @staticmethod
    def create_test_files(file_defs):
        """
        TODO
        """

        tempdir = TemporaryDirectory()
        for path_parts, content in file_defs:
            if isinstance(path_parts, str):
                path_parts = [path_parts]
            path = os.path.join(tempdir.name, *path_parts)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file_:
                file_.write(content)
        return tempdir
