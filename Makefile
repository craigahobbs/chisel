# -*- makefile-gmake -*-
#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

# Run unit tests
.PHONY: test
test:
	python -m unittest discover -t . -s chisel/test -p 'test_*.py' $(if $(VERBOSE),-v,)

# Run code coverage
.PHONY: cover
cover:
	-rm -rf cover
	nosetests -w chisel/test --with-coverage --cover-package=chisel --cover-erase --cover-html --cover-html-dir=$(abspath .)/cover

# Build the source distribution
.PHONY: sdist
sdist: test
	python setup.py sdist

# Install
.PHONY: install
install: test
	python setup.py install

# Clean
.PHONY: clean
clean:
	python setup.py clean
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -rf $(shell find . -name '*.pyc')
	-rm -rf .coverage cover
