#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

import chisel

from datetime import datetime, timedelta
try:
    import cPickle as pickle
except:
    import pickle
import time
import unittest


# Cache decorator tests
class TestCache(unittest.TestCase):

    # now helpers
    def makeNow(self, s, d = 1):
        return datetime(2013, 1, d, 0, 0, s)
    def setNow(self, s, d = 1):
        self.now = self.makeNow(s, d = d)
    def nowFn(self):
        return self.now

    # Test basic caching behavior
    def test_cache_expire(self):

        # Test sub-day ttl
        self.setNow(5)
        cache = chisel.Cache(ttl = 10, nowFn = self.nowFn)
        self.assertTrue(not cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(20))
        self.setNow(19)
        self.assertTrue(not cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(20))
        self.setNow(20)
        self.assertTrue(cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(30))
        self.setNow(34)
        self.assertTrue(cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(40))

        # Test ttl of more than a day
        self.setNow(5)
        cache = chisel.Cache(ttl = timedelta(days = 1, seconds = 10), nowFn = self.nowFn)
        self.assertTrue(not cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(10) + timedelta(days = 1))
        self.setNow(9, d = 1)
        self.assertTrue(not cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(10) + timedelta(days = 1))
        self.setNow(10, d = 2)
        self.assertTrue(cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(10) + timedelta(days = 2))
        self.setNow(50, d = 2)
        self.assertTrue(not cache._isExpired())
        self.assertEqual(cache._expire, self.makeNow(10) + timedelta(days = 2))

    # Test basic caching behavior
    def test_cache(self):

        # Update function
        def myCache(keys, arg1, arg2):
            result = {}
            for key in keys:
                if key in ("a",):
                    result["a"] = arg1
                elif key in ("b", "c"):
                    result["b"] = arg2
                    result["c"] = arg2 * 10
            return result

        # Define the cache
        self.setNow(5)
        cache = chisel.Cache(ttl = 10, nowFn = self.nowFn)
        self.assertTrue(not cache._isExpired(updateExpire = False))
        self.assertEqual(cache._expire, self.makeNow(20))

        # Helper to flush cache update threads
        def flushThreads():
            for thread in list(cache._updateThreads.itervalues()):
                thread.join()

        # Get the initial cache values
        self.assertEqual(cache._get(myCache, ["a"], (1, 2)), {"a": 1})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._get(myCache, ["a", "b"], (3, 2)), {"a": 1, "b": 2})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._get(myCache, ["a", "b", "c"], (3, 4)), {"a": 1, "b": 2, "c": 20})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._get(myCache, ["b"], (3, 4)), {"b": 2})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._get(myCache, ["c"], (3, 4)), {"c": 20})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._cacheOld, {})
        self.assertEqual(cache._cache, {"a": pickle.dumps(1), "b": pickle.dumps(2), "c": pickle.dumps(20)})

        # Missing value
        try:
            cache._get(myCache, ["d"], (3, 4))
        except KeyError:
            pass
        else:
            self.fail()
        self.assertEqual(len(cache._updateThreads), 0)

        # Expire the cache
        self.setNow(21)
        self.assertTrue(cache._isExpired(updateExpire = False))
        self.assertEqual(cache._expire, self.makeNow(20))
        self.assertEqual(cache._get(myCache, ["a"], (3, 4)), {"a": 1})
        flushThreads()
        self.assertEqual(cache._expire, self.makeNow(30))
        self.assertEqual(cache._get(myCache, ["a"], (5, 6)), {"a": 3})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._cacheOld, {"a": pickle.dumps(1), "b": pickle.dumps(2), "c": pickle.dumps(20)})
        self.assertEqual(cache._cache, {"a": pickle.dumps(3)})

        # Expire the cache again
        self.setNow(31)
        self.assertTrue(cache._isExpired(updateExpire = False))
        self.assertEqual(cache._expire, self.makeNow(30))
        self.assertEqual(cache._get(myCache, ["b"], (5, 6)), {"b": 6})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._expire, self.makeNow(40))
        self.assertEqual(cache._get(myCache, ["b", "c"], (5, 6)), {"b": 6, "c": 60})
        self.assertEqual(len(cache._updateThreads), 0)
        self.assertEqual(cache._cacheOld, {"a": pickle.dumps(3)})
        self.assertEqual(cache._cache, {"b": pickle.dumps(6), "c": pickle.dumps(60)})

    # Test cache decorator
    def test_cache_decorator(self):

        # Create the cache
        self.setNow(5)
        @chisel.Cache(ttl = 10)
        def myCache(keys, arg1, arg2):
            result = {}
            for key in keys:
                if key in ("a",):
                    result["a"] = arg1
                elif key in ("b", "c"):
                    result["b"] = arg2
                    result["c"] = arg2 * 10
            return result

        # Get the initial cache values
        self.assertEqual(myCache(["a"], 1, 2), {"a": 1})
        self.assertEqual(myCache(["a", "b"], 3, 2), {"a": 1, "b": 2})
