# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

"""
TODO
"""

import os
import tempfile
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

        tempdir = tempfile.TemporaryDirectory()
        for path_parts, content in file_defs:
            path = os.path.join(tempdir.name, *path_parts)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file_:
                file_.write(content)
        return tempdir
