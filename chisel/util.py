#
# Copyright (C) 2012-2015 Craig Hobbs
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

from .compat import string_isidentifier, xrange_

import itertools
import os
import sys


def load_modules(moduleDir, moduleExt='.py', excludedSubmodules=None):
    """
    Recursively load Python modules
    """

    # Does the path exist?
    if not os.path.isdir(moduleDir):
        raise IOError('%r not found or is not a directory' % (moduleDir,))

    # Where is this module on the system path?
    moduleDirParts = moduleDir.split(os.sep)

    def findModuleNameIndex():
        for sysPath in sys.path:
            for iModulePart in xrange_(len(moduleDirParts) - 1, 0, -1):
                moduleNameParts = moduleDirParts[iModulePart:]
                if not any(not string_isidentifier(part) for part in moduleNameParts):
                    sysModulePath = os.path.join(sysPath, *moduleNameParts)
                    if os.path.isdir(sysModulePath) and os.path.samefile(moduleDir, sysModulePath):
                        # Make sure the module package is import-able
                        moduleName = '.'.join(moduleNameParts)
                        try:
                            __import__(moduleName)
                        except ImportError:
                            pass
                        else:
                            return len(moduleDirParts) - len(moduleNameParts)
        raise ImportError('%r not found on system path' % (moduleDir,))
    ixModuleName = findModuleNameIndex()

    # Recursively find module files
    excludedSubmodulesDot = None if excludedSubmodules is None else [x + '.' for x in excludedSubmodules]
    for dirpath, dummy_dirnames, filenames in os.walk(moduleDir):

        # Skip Python 3.x cache directories
        if os.path.basename(dirpath) == '__pycache__':
            continue

        # Is the sub-package excluded?
        subpkgParts = dirpath.split(os.sep)
        subpkgName = '.'.join(itertools.islice(subpkgParts, ixModuleName, None))
        if excludedSubmodules is not None and \
           (subpkgName in excludedSubmodules or any(subpkgName.startswith(x) for x in excludedSubmodulesDot)):
            continue

        # Load each sub-module file in the directory
        for filename in filenames:

            # Skip non-module files
            (basename, ext) = os.path.splitext(filename)
            if ext != moduleExt:
                continue

            # Skip package __init__ files
            if basename == '__init__':
                continue

            # Is the sub-module excluded?
            submoduleName = subpkgName + '.' + basename
            if excludedSubmodules is not None and \
               (submoduleName in excludedSubmodules or any(submoduleName.startswith(x) for x in excludedSubmodules)):
                continue

            # Load the sub-module
            yield __import__(submoduleName, globals(), locals(), ['.'])
