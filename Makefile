# -*- makefile-gmake -*-
#
# Copyright (C) 2012 Craig Hobbs
#
# See README.md for license.
#

PACKAGE_NAME = chisel

# Python version support
PYTHON_VERSIONS = \
	2.6 \
	2.7

# Local directories
ENV = env
COVER = cover

# Run unit tests
.PHONY: test
test:
	$(if $(PYTHON_ENV), . $(PYTHON_ENV)/bin/activate;,) \
	if python -m unittest discover --help > /dev/null 2>&1; then \
		python -m unittest discover -t . -s $(PACKAGE_NAME)/test -p 'test_*.py' $(if $(VERBOSE),-v,); \
	else \
		echo No unittest discover - using $$(which nosetests)...; \
		nosetests -w $(PACKAGE_NAME)/test $(if $(VERBOSE),-v,); \
	fi

# Pre-checkin check
.PHONY: check
check: $(foreach V, $(PYTHON_VERSIONS), $(ENV)/$(V))
	$(foreach V, $(PYTHON_VERSIONS), $(MAKE) test PYTHON_ENV=$(ENV)/$(V);)

# Python environment rules
define PYTHON_ENV_RULE
env/$(1):
	virtualenv -p python$$(notdir $$@) $$@
	if [ "$$$$(expr $(1) \< 2.7)" = "1" ]; then \
		. $$@/bin/activate; pip install nose; \
	fi
endef
$(foreach V, $(PYTHON_VERSIONS), $(eval $(call PYTHON_ENV_RULE,$(V))))

# Run code coverage
.PHONY: cover
cover: $(ENV)/$(COVER)
	-rm -rf $(COVER)
	. $(ENV)/$(COVER)/bin/activate; \
		nosetests -w $(PACKAGE_NAME)/test --with-coverage --cover-package=$(PACKAGE_NAME) --cover-erase \
			--cover-html --cover-html-dir=$(abspath $(COVER))
	@echo
	@echo Coverage report is $(COVER)/index.html

# Coverage environment rule
$(ENV)/$(COVER):
	virtualenv $@
	. $@/bin/activate; pip install nose coverage

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
