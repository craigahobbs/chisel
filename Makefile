# -*- makefile-gmake -*-
#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
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
