# -*- makefile-gmake -*-
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

PACKAGE_NAME = chisel
PACKAGE_TESTS = $(PACKAGE_NAME)/tests

# Local directories
ENV = env
COVER = cover

# Python version support
PYTHON_VERSIONS = \
    2.6 \
    2.7

# Run unit tests
.PHONY: test
test:
	python -m unittest discover -t . -s $(PACKAGE_TESTS) -p 'test_*.py' $(if $(VERBOSE),-v,)

# Pre-checkin check
.PHONY: check
check:
	$(foreach V, $(PYTHON_VERSIONS), \
		rm -rf $(ENV)/$(V); \
		virtualenv -p python$(V) $(ENV)/$(V); \
		. $(ENV)/$(V)/bin/activate; \
		python setup.py test; \
	)

# Run code coverage
.PHONY: cover
cover: $(ENV)/cover
	-rm -rf $(COVER)
	. $(ENV)/cover/bin/activate; \
		nosetests -w $(PACKAGE_TESTS) --with-coverage --cover-package=$(PACKAGE_NAME) --cover-erase \
			--cover-html --cover-html-dir=$(abspath $(COVER))
	@echo
	@echo Coverage report is $(COVER)/index.html

# Coverage environment rule
$(ENV)/cover:
	virtualenv $@
	. $@/bin/activate; pip install coverage nose

# Clean
.PHONY: clean
clean:
	-rm -rf .coverage $(COVER)
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -rf $(shell find $(PACKAGE_NAME) -name '*.pyc')

# Superclean
.PHONY: superclean
superclean: clean
	-rm -rf $(ENV)
