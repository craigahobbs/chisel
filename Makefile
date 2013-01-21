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
ENV = .env
COVER = .cover

# Python version support
PYTHON_VERSIONS = \
    2.7 \
    2.6 \
    3.1 \
    3.2 \
    3.3

# Help
.PHONY: help
help:
	@echo "usage: make [test|cover|check|clean|superclean]"

# Run unit tests
.PHONY: test
test: test_$(firstword $(PYTHON_VERSIONS))

# Pre-checkin check
.PHONY: check
check: clean $(foreach V, $(PYTHON_VERSIONS), test_$(V)) cover

# Clean
.PHONY: clean
clean:
	-rm -rf $(shell find $(PACKAGE_NAME) -name '*.pyc')
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -rf .coverage $(COVER)

# Superclean
.PHONY: superclean
superclean: clean
	-rm -rf $(ENV)

# Macro to generate virtualenv rules - env_name, python_version, packages, commands
define ENV_RULE
$(ENV)/$(strip $(1)):
	virtualenv -p python$(strip $(2)) $$@
	$(if $(strip $(3)), . $$@/bin/activate; pip install $(3))

.PHONY: $(1)
$(1): $(ENV)/$(strip $(1))
	$(4)
endef
ENV_ACTIVATE = . $$</bin/activate

# Generate test rules
define TEST_COMMANDS
	$(ENV_ACTIVATE); python setup.py test
endef
$(foreach V, $(PYTHON_VERSIONS), $(eval $(call ENV_RULE, test_$(V), $(V), , $(TEST_COMMANDS))))

# Generate coverage rule
define COVER_COMMANDS
	$(ENV_ACTIVATE); nosetests -w $(PACKAGE_TESTS) --with-coverage --cover-package=$(PACKAGE_NAME) \
		--cover-erase --cover-html --cover-html-dir=$(abspath $(COVER))
	@echo
	@echo Coverage report is $(COVER)/index.html
endef
$(eval $(call ENV_RULE, cover, $(firstword $(PYTHON_VERSIONS)), nose coverage, $(COVER_COMMANDS)))
