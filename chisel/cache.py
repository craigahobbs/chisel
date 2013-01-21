#
# Copyright (C) 2012-2013 Craig Hobbs
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

from .compat import iteritems, pickle

from datetime import datetime, timedelta
import threading


# Simple TTL cache decorator object
class Cache:

    def __init__(self, ttl, multipleKeys = False, keyArg = 0, nowFn = None):

        self._ttl = ttl if isinstance(ttl, timedelta) else timedelta(seconds = ttl)
        self._ttlSeconds = self._timedelta_total_seconds(self._ttl)
        self._multipleKeys = multipleKeys
        self._keyArg = keyArg
        self._nowFn = nowFn
        self._cacheLock = threading.Lock()
        self._cache = {}
        self._cacheOld = {}
        self._updateThreads = {}

        # Set expiration time
        self._expire = None
        self._isExpired()

    def __call__(self, updateFn):

        def get(*args):
            return self._get(updateFn, args)
        return get

    @staticmethod
    def _timedelta_total_seconds(td):

        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.**6

    def _isExpired(self, updateExpire = True):

        # Expired?
        now = datetime.now() if self._nowFn is None else self._nowFn()
        isExpired = self._expire is None or now >= self._expire

        # Yes, compute next expiration time...
        if isExpired and updateExpire:
            today = datetime(now.year, now.month, now.day)
            if self._ttl >= timedelta(days = 1):
                self._expire = today + self._ttl
            else:
                secondsToday = self._timedelta_total_seconds(now - today)
                periodsToday = (secondsToday + self._ttlSeconds / 2) // self._ttlSeconds
                self._expire = today + timedelta(seconds = (periodsToday + 1) * self._ttlSeconds)

        return isExpired

    def _get(self, updateFn, args):

        result = {}

        # Get the keys argument
        if self._multipleKeys:
            keys = args[self._keyArg]
        else:
            keys = (args[self._keyArg],)

        # Lock the cache...
        with self._cacheLock:

            # TTL expired?
            if self._isExpired():
                self._cacheOld = self._cache
                self._cache = {}

            # Get cached values - keep track of un-cached key/values
            resultPickle = {}
            keysUpdate = set()
            keysWait = set()
            threadsWait = set()
            for key in keys:

                # Cached value?
                if key in self._cache:

                    # Add the pickled value (unpickle outside of lock)
                    resultPickle[key] = self._cache[key]

                else:

                    # Add key to update list (if not already updating)
                    if key not in self._updateThreads:
                        keysUpdate.add(key)

                    # Add the (old) pickled value (unpickle outside of lock)
                    if key in self._cacheOld:
                        resultPickle[key] = self._cacheOld[key]
                    else:
                        keysWait.add(key)

            # Start threads to update expired or unknown values
            if keysUpdate:
                updateThread = threading.Thread(target = lambda: self._updateKey(updateFn, tuple(keysUpdate), args))
                for key in keysUpdate:
                    self._updateThreads[key] = updateThread
                updateThread.start()

            # Get the threads to wait for
            for key in keysWait:
                threadsWait.add(self._updateThreads[key])

        # Un-pickle values (outside of lock)
        for key, valuePickle in iteritems(resultPickle):
            result[key] = pickle.loads(valuePickle)

        # Wait for any unknown result values
        for thread in threadsWait:
            thread.join()

        # Un-pickle the waited-for values
        for key in keysWait:
            valuePickle = self._cache[key]
            result[key] = pickle.loads(valuePickle)

        # Return the result
        if self._multipleKeys:
            return result
        else:
            return result[keys[0]]

    def _updateKey(self, updateFn, keys, args):

        # Call the update function
        try:
            if self._multipleKeys:
                updateArgs = args[:self._keyArg] + (keys,) + args[self._keyArg + 1:]
                result = updateFn(*updateArgs)
                assert isinstance(result, dict), "Multiple-key cache update functions must return dict"
            else:
                updateArgs = args[:self._keyArg] + keys + args[self._keyArg + 1:]
                result = { keys[0]: updateFn(*updateArgs) }
        except:
            # The update function raised - cleanup the update threads dict
            for key in keys:
                del self._updateThreads[key]
            raise

        # Pickle the the cache values
        resultPickle = {}
        for key, value in iteritems(result):
            resultPickle[key] = pickle.dumps(value)

        # Lock the cache...
        with self._cacheLock:

            # Update the cache with the pickled values
            for key, valuePickle in iteritems(resultPickle):
                self._cache[key] = valuePickle

            # Remove the key from the update threads dict
            for key in keys:
                del self._updateThreads[key]
