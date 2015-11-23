# -*- makefile-gmake -*-
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

PACKAGE_NAME := chisel

include Makefile.base

# Static source/build dirs
STATIC_SRC := static
STATIC_BUILD := $(PACKAGE_NAME)/static

# Helper function to recursively find files from a set of file extensions
FIND_EXTS_FN = $(shell find $(1) -name "*.$(firstword $(2))" $(foreach X, $(wordlist 2, 100, $(2)),-o -name "*.$(X)"))

# Create the js compile rules
JS_EXTS := js
$(foreach F, $(call FIND_EXTS_FN, $(STATIC_SRC), $(JS_EXTS)), \
    $(eval $(call COPY_RULE, $(F), $(PACKAGE_NAME)/$(F), babel "$$<" -o "$$@")))

# Create static copy rules
STATIC_EXTS = css html png
$(foreach F, $(call FIND_EXTS_FN, $(STATIC_SRC), $(STATIC_EXTS)), \
    $(eval $(call COPY_RULE, $(F), $(PACKAGE_NAME)/$(F))))

build:
	jshint --reporter=unix "$(STATIC_SRC)"

clean:
	rm -rf "$(STATIC_BUILD)"
