# -*- makefile-gmake -*-
#
# Copyright (C) 2012-2014 Craig Hobbs
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

# Python version support
PYTHON_VERSIONS = \
    2.7 \
    3.2 \
    3.3 \
    3.4

# Local directories
ENV = .env
COVER = .cover

# Help
.PHONY: help
help:
	@echo "usage: make [test|pyflakes|cover|check|clean]"

# Run unit tests
.PHONY: test
test: pyflakes test_$(firstword $(PYTHON_VERSIONS))

# Pre-checkin check
.PHONY: check
check: pyflakes $(foreach V, $(PYTHON_VERSIONS), test_$(V)) cover

# Clean
.PHONY: clean
clean:
	-rm -rf \
		$(ENV) \
		$(COVER) \
		.coverage \
		$$(find $(PACKAGE_NAME) -name '__pycache__') \
		$$(find $(PACKAGE_NAME) -name '*.pyc') \
		dist \
		*.egg-info \
		*.egg

# Setup
.PHONY: setup
setup:
	sudo add-apt-repository -y ppa:fkrull/deadsnakes
	sudo apt-get update
	sudo apt-get install -y \
		python-pip \
		python-virtualenv \
		$(foreach P, $(PYTHON_VERSIONS),$(if $(shell which python$P),,python$P))
	sudo pip install -U pip virtualenv

# Function to generate virtualenv rules - env_name, python_version, packages, commands
define ENV_RULE
BUILD_$(strip $(1)) := $(ENV)/$(strip $(1)).build

$$(BUILD_$(strip $(1))):
	virtualenv -p python$(strip $(2)) $(ENV)/$(strip $(1))
	$(if $(strip $(3)),$(call ENV_PYTHON, $(1)) -m pip install $(strip $(3)))
	touch $$@

.PHONY: $(strip $(1))
$(strip $(1)): $$(BUILD_$(strip $(1)))
$(call $(4), $(1))
endef

# Function to generate an environment rule's python interpreter
ENV_PYTHON = $(ENV)/$(strip $(1))/bin/python -E

# Generate test rules
define TEST_COMMANDS
	$(call ENV_PYTHON, $(1)) -m pip install -q -e . -e .[tests]
	$(call ENV_PYTHON, $(1)) setup.py test $(if $(TEST),-s $(TEST))
endef
$(foreach V, $(PYTHON_VERSIONS), $(eval $(call ENV_RULE, test_$(V), $(V), , TEST_COMMANDS)))

# Generate coverage rule
define COVER_COMMANDS
	$(call ENV_PYTHON, $(1)) -m pip install -e . -e .[tests]
	$(call ENV_PYTHON, $(1)) -m coverage run --branch --source $(PACKAGE_NAME) setup.py test
	$(call ENV_PYTHON, $(1)) -m coverage html -d $(COVER)
	$(call ENV_PYTHON, $(1)) -m coverage report
	@echo
	@echo Coverage report is $(COVER)/index.html
endef
$(eval $(call ENV_RULE, cover, $(firstword $(PYTHON_VERSIONS)), coverage, COVER_COMMANDS))

# Generate pyflakes rule
define PYFLAKES_COMMANDS
	$(call ENV_PYTHON, $(1)) -m pyflakes $(PACKAGE_NAME)
endef
$(eval $(call ENV_RULE, pyflakes, $(firstword $(PYTHON_VERSIONS)), pyflakes, PYFLAKES_COMMANDS))
