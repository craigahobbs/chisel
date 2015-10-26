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

# Helper functions
LOWER_FN = $(eval $(call LOWER_FN_CACHE, $(1)))$(__LOWER_FN__$(strip $(1))__)
UPPER_FN = $(eval $(call UPPER_FN_CACHE, $(1)))$(__UPPER_FN__$(strip $(1))__)
define LOWER_FN_CACHE
ifndef __LOWER_FN__$(strip $(1))__
__LOWER_FN__$(strip $(1))__ := $$(shell echo '$(strip $(1))' | tr '[:upper:]' '[:lower:]')
endif
endef
define UPPER_FN_CACHE
ifndef __UPPER_FN__$(strip $(1))__
__UPPER_FN__$(strip $(1))__ := $$(shell echo '$(strip $(1))' | tr '[:lower:]' '[:upper:]')
endif
endef

# Python version support
PYTHON_URLS := \
    https://www.python.org/ftp/python/3.5.0/Python-3.5.0.tgz \
    https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz \
    https://www.python.org/ftp/python/3.4.3/Python-3.4.3.tgz \
    https://www.python.org/ftp/python/3.3.6/Python-3.3.6.tgz \
    https://www.python.org/ftp/python/3.2.6/Python-3.2.6.tgz
PYTHON_NAME_FN = $(call UPPER_FN, $(subst -,_,$(subst .,_,$(basename $(notdir $(1))))))
PYTHON_NAMES := $(foreach X, $(PYTHON_URLS), $(call LOWER_FN, $(call PYTHON_NAME_FN, $(X))))
PYTHON_DEFAULT := $(firstword $(PYTHON_NAMES))

# OS helpers
OS_MAC := $(findstring Darwin, $(shell uname))

.PHONY: help
help:
	@echo "usage: make [test|cover|doc|pylint|check|clean|superclean]"

.PHONY: test
test: test_$(PYTHON_DEFAULT)

.PHONY: cover
cover: cover_$(PYTHON_DEFAULT)

.PHONY: doc
doc: doc_$(PYTHON_DEFAULT)

.PHONY: pylint
pylint: pylint_python_3_4_3

.PHONY: check
check: $(foreach X, $(PYTHON_NAMES), test_$(X)) cover doc pylint

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
	brew install \
		openssl \
		homebrew/dupes/zlib
else
	sudo apt-get install -y \
		build-essential \
		libbz2-dev \
		libexpat1-dev \
		libssl-dev \
		zlib1g-dev
endif

# Function to generate python source build rules - python_url
define PYTHON_RULE_FN
$(call PYTHON_NAME_FN, $(1))_SRC := $$(BUILD)/$(basename $(notdir $(1)))
$(call PYTHON_NAME_FN, $(1))_INSTALL := $$($(call PYTHON_NAME_FN, $(1))_SRC).install
$(call PYTHON_NAME_FN, $(1))_BUILD := $$($(call PYTHON_NAME_FN, $(1))_SRC).build
$(call PYTHON_NAME_FN, $(1)) := $$($(call PYTHON_NAME_FN, $(1))_INSTALL)/bin/python$(if $(findstring Python-3.,$(1)),3) -E

$$($(call PYTHON_NAME_FN, $(1))_BUILD):
	mkdir -p '$$(dir $$@)'
	$(if $(shell which curl),curl -s,wget -q -O -) "$(strip $(1))" | tar xzC '$$(dir $$@)'
	cd '$$($(call PYTHON_NAME_FN, $(1))_SRC)' && \
		$(if $(OS_MAC), CPPFLAGS="-I/usr/local/opt/zlib/include -I/usr/local/opt/openssl/include") \
		$(if $(OS_MAC), LDFLAGS="-L/usr/local/opt/zlib/lib -L/usr/local/opt/openssl/lib") \
			./configure --prefix='$$(abspath $$($(call PYTHON_NAME_FN, $(1))_INSTALL))' && \
		make && \
		make install
	if ! $$($(call PYTHON_NAME_FN, $(1))) -m ensurepip --default-pip; then \
		$(if $(shell which curl),curl -s,wget -q -O -) "https://bootstrap.pypa.io/get-pip.py" | $$($(call PYTHON_NAME_FN, $(1))); \
	fi
	$$($(call PYTHON_NAME_FN, $(1))) -m pip --disable-pip-version-check install --no-use-wheel virtualenv
	touch $$@
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call PYTHON_RULE_FN, $(X))))

# Function to generate virtualenv rules - python_url, env_name, pip_args, commands
define ENV_RULE
$(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_ENV := $$(ENV)/$(strip $(2))-$(basename $(notdir $(1)))
$(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_BUILD := $$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_ENV).build
$(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1)) := $$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_ENV)/bin/python -E

$$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_BUILD): $$($(call PYTHON_NAME_FN, $(1))_BUILD)
	$$($(call PYTHON_NAME_FN, $(1))) -m virtualenv '$$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_ENV)'
	$(if $(PIP_ARGS)$(strip $(3)),$$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))) -m pip --disable-pip-version-check install --no-use-wheel $(PIP_ARGS) $(3))
	touch $$@

.PHONY: $(call LOWER_FN, $(2)_$(call PYTHON_NAME_FN, $(1)))
$(call LOWER_FN, $(2)_$(call PYTHON_NAME_FN, $(1))): $$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_BUILD)
$(call $(4), $$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))_ENV), $$($(call UPPER_FN, $(2))_$(call PYTHON_NAME_FN, $(1))))
endef

# Generate test rules - virtualenv, python
define TEST_COMMANDS_FN
	$(2) setup.py test $(if $(TEST),-s $(TEST))
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), test, -e . -e .[tests], TEST_COMMANDS_FN)))

# Generate coverage rules - virtualenv, python
define COVER_COMMANDS_FN
	$(2) -m coverage run --branch --source $(PACKAGE_NAME) setup.py test
	$(2) -m coverage html -d $(COVER)
	$(2) -m coverage report
	@echo
	@echo Coverage report is $(COVER)/index.html
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), cover, -e . -e .[tests] coverage==4.0, COVER_COMMANDS_FN)))

# Generate doc rules - virtualenv, python
HAS_DOC = $(shell if [ -d doc ]; then echo 1; fi)
define DOC_COMMANDS_FN
ifneq "$(HAS_DOC)" ""
	$(1)/bin/sphinx-build -b html -d $(DOC)/doctrees doc $(DOC)/html
	@echo
	@echo Doc index is $(DOC)/html/index.html
endif
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), doc, $(if $(HAS_DOC), sphinx==1.3.1), DOC_COMMANDS_FN)))

# Generate pyint rules - virtualenv, python
define PYLINT_COMMANDS_FN
	$(2) -m pylint -f parseable $(PYLINT_ARGS) $(PACKAGE_NAME)
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, $(X), pylint, -e . pylint==1.4.4, PYLINT_COMMANDS_FN)))
