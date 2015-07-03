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

# Local directories
ENV := .env
COVER := .cover

# Python version support
PYTHON_URLS := \
    https://www.python.org/ftp/python/3.4.3/Python-3.4.3.tgz \
    https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz \
    https://www.python.org/ftp/python/3.3.6/Python-3.3.6.tgz \
    https://www.python.org/ftp/python/3.2.6/Python-3.2.6.tgz

# Function to get a python URL's name - python_url
PYTHON_NAME = $(subst -,_,$(subst .,_,$(basename $(notdir $(1)))))

.PHONY: help
help:
	@echo "usage: make [test|cover|pyflakes|check|clean]"

.PHONY: test
test: $(call PYTHON_NAME, $(firstword $(PYTHON_URLS)))_test

.PHONY: cover
cover: $(call PYTHON_NAME, $(firstword $(PYTHON_URLS)))_cover

.PHONY: pyflakes
pyflakes: $(call PYTHON_NAME, Python_2_7_10)_pyflakes

.PHONY: check
check: pyflakes $(foreach X, $(PYTHON_URLS), $(call PYTHON_NAME, $(X))_test) cover

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

.PHONY: setup
setup:
	sudo apt-get install -y \
		build-essential \
		zlib1g-dev \
		libssl-dev

# Function to generate python source build rules - python_url
define PYTHON_RULE
SRC_$(call PYTHON_NAME, $(1)) := $(abspath $$(ENV)/$(basename $(notdir $(1))))
INSTALL_$(call PYTHON_NAME, $(1)) := $(abspath $$(ENV)/$(call PYTHON_NAME, $(1)).install)
BUILD_$(call PYTHON_NAME, $(1)) := $(abspath $$(ENV)/$(call PYTHON_NAME, $(1)).build)

PYTHON_$(call PYTHON_NAME, $(1)) := \
    LD_LIBRARY_PATH='$$(INSTALL_$(call PYTHON_NAME, $(1)))/lib' \
    LDFLAGS=-L'$$(INSTALL_$(call PYTHON_NAME, $(1)))/lib' \
    CFLAGS=-I'$$(INSTALL_$(call PYTHON_NAME, $(1)))/include' \
    CXXFLAGS=-I'$$(INSTALL_$(call PYTHON_NAME, $(1)))/include' \
        $$(INSTALL_$(call PYTHON_NAME, $(1)))/bin/python$(if $(findstring Python-3.,$(1)),3) -E

$$(BUILD_$(call PYTHON_NAME, $(1))):
	mkdir -p '$$(ENV)'
	wget -O - '$(strip $(1))' | tar xzC '$$(ENV)'
	cd '$$(SRC_$(call PYTHON_NAME, $(1)))' && ./configure --prefix='$$(INSTALL_$(call PYTHON_NAME, $(1)))' && make && make install
	if ! $$(PYTHON_$(call PYTHON_NAME, $(1))) -m ensurepip; then \
		wget -O - 'https://bootstrap.pypa.io/get-pip.py' | $$(PYTHON_$(call PYTHON_NAME, $(1))); \
	fi
	$$(PYTHON_$(call PYTHON_NAME, $(1))) -m pip --disable-pip-version-check install virtualenv
	touch $$@
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call PYTHON_RULE, $(X))))

# Function to generate virtualenv rules - python_url, env_name, packages, commands
define ENV_RULE
ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)) := $$(ENV)/$(call PYTHON_NAME, $(1))_$(strip $(2))
BUILD_$(call PYTHON_NAME, $(1))_$(strip $(2)) := $$(ENV)/$(call PYTHON_NAME, $(1))_$(strip $(2)).build

$$(BUILD_$(call PYTHON_NAME, $(1))_$(strip $(2))): $$(BUILD_$(call PYTHON_NAME, $(1)))
	$$(PYTHON_$(call PYTHON_NAME, $(1))) -m virtualenv '$$(ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)))'
	$(if $(strip $(3)),$(call ENV_PIP, $(1), $(2)) install $(strip $(3)))
	touch $$@

.PHONY: $(call PYTHON_NAME, $(1))_$(strip $(2))
$(call PYTHON_NAME, $(1))_$(strip $(2)): $$(BUILD_$(call PYTHON_NAME, $(1))_$(strip $(2)))
$(call $(4), $(1), $(2))
endef

# Function to generate an environment's python interpreter - python_url, env_name
ENV_PYTHON = \
    LD_LIBRARY_PATH='$$(INSTALL_$(call PYTHON_NAME, $(1)))/lib' \
    LDFLAGS=-L'$$(INSTALL_$(call PYTHON_NAME, $(1)))/lib' \
    CFLAGS=-I'$$(INSTALL_$(call PYTHON_NAME, $(1)))/include' \
    CXXFLAGS=-I'$$(INSTALL_$(call PYTHON_NAME, $(1)))/include' \
        $$(ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)))/bin/python$(if $(findstring Python-3.,$(1)),3) -E

# Function to generate an environment's pip - python_url, env_name
ENV_PIP = $(call ENV_PYTHON, $(1), $(2)) -m pip --disable-pip-version-check

# Generate test rules
define TEST_COMMANDS
	$(call ENV_PIP, $(1), $(2)) install -q -e . -e .[tests]
	$(call ENV_PYTHON, $(1), $(2)) setup.py test $(if $(TEST),-s $(TEST))
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), test,, TEST_COMMANDS)))

# Generate coverage rule
define COVER_COMMANDS
	$(call ENV_PIP, $(1), $(2)) install -e . -e .[tests]
	$(call ENV_PYTHON, $(1), $(2)) -m coverage run --branch --source $(PACKAGE_NAME) setup.py test
	$(call ENV_PYTHON, $(1), $(2)) -m coverage html -d $(COVER)
	$(call ENV_PYTHON, $(1), $(2)) -m coverage report
	@echo
	@echo Coverage report is $(COVER)/index.html
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), cover, coverage, COVER_COMMANDS)))

# Generate pyflakes rule
define PYFLAKES_COMMANDS
	$(call ENV_PYTHON, $(1), $(2)) -m pyflakes $(PACKAGE_NAME)
	$(call ENV_PYTHON, $(1), $(2)) -m pep8 --show-pep8 --max-line-length=140 $(PACKAGE_NAME)
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), pyflakes, pyflakes pep8, PYFLAKES_COMMANDS)))
