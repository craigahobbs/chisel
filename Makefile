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

# Build directories
BUILD := .build
DOC := doc/_build
ENV := .env
COVER := .cover

# Python version support
PYTHON_URLS := \
    https://www.python.org/ftp/python/3.5.0/Python-3.5.0.tgz \
    https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz \
    https://www.python.org/ftp/python/3.4.3/Python-3.4.3.tgz \
    https://www.python.org/ftp/python/3.3.6/Python-3.3.6.tgz \
    https://www.python.org/ftp/python/3.2.6/Python-3.2.6.tgz

# Function to get a python URL's name - python_url
PYTHON_NAME = $(subst -,_,$(subst .,_,$(basename $(notdir $(1)))))

# OS helpers
OS_MAC := $(findstring Darwin, $(shell uname))

.PHONY: help
help:
	@echo "usage: make [test|cover|doc|pylint|check|clean|superclean]"

.PHONY: test
test: $(call PYTHON_NAME, $(firstword $(PYTHON_URLS)))_test

.PHONY: cover
cover: $(call PYTHON_NAME, $(firstword $(PYTHON_URLS)))_cover

.PHONY: doc
doc: $(call PYTHON_NAME, Python_3_5_0)_doc

.PHONY: pylint
pylint: $(call PYTHON_NAME, Python_3_4_3)_pylint

.PHONY: check
check: $(foreach X, $(PYTHON_URLS), $(call PYTHON_NAME, $(X))_test) cover doc pylint

.PHONY: clean
clean:
	rm -rf \
		$(DOC) \
		$(ENV) \
		$(COVER) \
		.coverage \
		.makefile \
		$$(find $(PACKAGE_NAME) -name '__pycache__') \
		$$(find $(PACKAGE_NAME) -name '*.pyc') \
		$$(find $(PACKAGE_NAME) -name '*.so') \
		build \
		dist \
		*.egg-info \
		*.egg

.PHONY: superclean
superclean: clean
	rm -rf \
		$(BUILD)

.PHONY: setup
setup:
ifneq "$(OS_MAC)" ""
	brew install homebrew/dupes/zlib openssl
else
	sudo apt-get install -y \
		build-essential \
		libbz2-dev \
		libexpat1-dev \
		libssl-dev \
		zlib1g-dev
endif

# Function to generate a wget to stdout command - url
WGET_STDOUT = $(if $(OS_MAC), curl -s, wget -O -) '$(strip $(1))'

# Function to generate python source build rules - python_url
define PYTHON_RULE
SRC_$(call PYTHON_NAME, $(1)) := $$(BUILD)/$(basename $(notdir $(1)))
INSTALL_$(call PYTHON_NAME, $(1)) := $$(BUILD)/$(call PYTHON_NAME, $(1)).install
BUILD_$(call PYTHON_NAME, $(1)) := $$(BUILD)/$(call PYTHON_NAME, $(1)).build
PYTHON_$(call PYTHON_NAME, $(1)) := $$(INSTALL_$(call PYTHON_NAME, $(1)))/bin/python$(if $(findstring Python-3.,$(1)),3) -E

$$(BUILD_$(call PYTHON_NAME, $(1))):
	mkdir -p '$$(dir $$@)'
	$(call WGET_STDOUT, $(1)) | tar xzC '$$(dir $$@)'
	cd '$$(SRC_$(call PYTHON_NAME, $(1)))' && \
		$(if $(OS_MAC), CPPFLAGS="-I/usr/local/opt/zlib/include -I/usr/local/opt/openssl/include") \
		$(if $(OS_MAC), LDFLAGS="-L/usr/local/opt/zlib/lib -L/usr/local/opt/openssl/lib") \
			./configure --prefix='$$(abspath $$(INSTALL_$(call PYTHON_NAME, $(1))))' && \
		make && \
		make install
	if ! $$(PYTHON_$(call PYTHON_NAME, $(1))) -m ensurepip --default-pip; then \
		$(call WGET_STDOUT, https://bootstrap.pypa.io/get-pip.py) | $$(PYTHON_$(call PYTHON_NAME, $(1))); \
	fi
	$$(PYTHON_$(call PYTHON_NAME, $(1))) -m pip --disable-pip-version-check install --no-binary ':all:' virtualenv
	touch $$@
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call PYTHON_RULE, $(X))))

# Function to generate virtualenv rules - python_url, env_name, pip_args, commands
define ENV_RULE
ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)) := $$(ENV)/$(call PYTHON_NAME, $(1))_$(strip $(2))
BUILD_$(call PYTHON_NAME, $(1))_$(strip $(2)) := $$(ENV)/$(call PYTHON_NAME, $(1))_$(strip $(2)).build

$$(BUILD_$(call PYTHON_NAME, $(1))_$(strip $(2))): $$(BUILD_$(call PYTHON_NAME, $(1)))
	$$(PYTHON_$(call PYTHON_NAME, $(1))) -m virtualenv '$$(ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)))'
	$(if $(PIP_ARGS)$(strip $(3)), $(call ENV_PYTHON, $(1), $(2)) -m pip --disable-pip-version-check install --no-binary ':all:' $(PIP_ARGS) $(3))
	touch $$@

.PHONY: $(call PYTHON_NAME, $(1))_$(strip $(2))
$(call PYTHON_NAME, $(1))_$(strip $(2)): $$(BUILD_$(call PYTHON_NAME, $(1))_$(strip $(2)))
$(call $(4), $(1), $(2))
endef

# Function to generate an environment's python interpreter - python_url, env_name
ENV_PYTHON = $$(ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)))/bin/python$(if $(findstring Python-3.,$(1)),3) -E

# Generate test rules
define TEST_COMMANDS
	$(call ENV_PYTHON, $(1), $(2)) setup.py test $(if $(TEST),-s $(TEST))
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), test, -e . -e .[tests], TEST_COMMANDS)))

# Generate coverage rule
define COVER_COMMANDS
	$(call ENV_PYTHON, $(1), $(2)) -m coverage run --branch --source $(PACKAGE_NAME) setup.py test
	$(call ENV_PYTHON, $(1), $(2)) -m coverage html -d $(COVER)
	$(call ENV_PYTHON, $(1), $(2)) -m coverage report
	@echo
	@echo Coverage report is $(COVER)/index.html
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), cover, -e . -e .[tests] coverage==4.0, COVER_COMMANDS)))

# Generate doc rule
HAS_DOC = $(shell if [ -d doc ]; then echo 1; fi)
define DOC_COMMANDS
ifneq "$(HAS_DOC)" ""
	$$(ENV_$(call PYTHON_NAME, $(1))_$(strip $(2)))/bin/sphinx-build -b html -d $(DOC)/doctrees doc $(DOC)/html
	@echo
	@echo Doc index is $(DOC)/html/index.html
endif
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), doc, $(if $(HAS_DOC), sphinx==1.3.1), DOC_COMMANDS)))

# Generate pyint rule
define PYLINT_COMMANDS
	$(call ENV_PYTHON, $(1), $(2)) -m pylint -f parseable $(PYLINT_ARGS) $(PACKAGE_NAME)
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), pylint, -e . pylint==1.4.4, PYLINT_COMMANDS)))
