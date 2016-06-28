#
# Copyright (C) 2012-2016 Craig Hobbs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import unittest

import json

from chisel.util import JSONFloat


class TestModelJSONFloat(unittest.TestCase):

    def test(self):

        obj = JSONFloat(2.25, 2)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2.25')
        self.assertEqual(str(obj), '2.25')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2.25}')

    def test_default(self):

        obj = JSONFloat(2.1234567)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2.123457')
        self.assertEqual(str(obj), '2.123457')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2.123457}')

    def test_round_up(self):

        obj = JSONFloat(2.256, 2)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2.26')
        self.assertEqual(str(obj), '2.26')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2.26}')

    def test_round_down(self):

        obj = JSONFloat(2.254, 2)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2.25')
        self.assertEqual(str(obj), '2.25')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2.25}')

    # Two decimal places float repr - ugly in Python 2.6
    def test_ugly(self):

        obj = JSONFloat(2.03, 2)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2.03')
        self.assertEqual(str(obj), '2.03')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2.03}')

    # Two decimal places float repr with end-zero trimming
    def test_zero_trim(self):

        obj = JSONFloat(2.5, 2)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2.5')
        self.assertEqual(str(obj), '2.5')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2.5}')

    # Two decimal places float repr with end-point trimming
    def test_point_trim(self):

        obj = JSONFloat(2., 2)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2')
        self.assertEqual(str(obj), '2')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2}')

    # Zero decimal places
    def test_zero_prec(self):

        obj = JSONFloat(2.25, 0)
        self.assertTrue(isinstance(obj, float))
        self.assertTrue(float(obj) is obj)
        self.assertEqual(repr(obj), '2')
        self.assertEqual(str(obj), '2')
        self.assertEqual(json.dumps({'v': obj}), '{"v": 2}')
