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

# OS helpers
OS_MAC := $(findstring Darwin, $(shell uname))

.PHONY: help
help: _help

.PHONY: _help
_help:
	@echo "usage: make [test|cover|doc|pylint|check|clean|superclean]"

.PHONY: check
check: test doc cover pylint

.PHONY: clean
clean: _clean

.PHONY: _clean
_clean:
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
superclean: clean _superclean

.PHONY: _superclean
_superclean:
	rm -rf \
		$(BUILD)

.PHONY: setup
setup: _setup

.PHONY: _setup
_setup:
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

# Function to generate virtualenv rules - env_name, pip_args, commands, *python_url
define ENV_RULE
$(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_ENV := $$(ENV)/$(strip $(1))-$(basename $(notdir $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS)))))
$(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_BUILD := $$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_ENV).build
$(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS)))) := $$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_ENV)/bin/python -E

$$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_BUILD): $$($(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_BUILD)
	$$($(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))) -m virtualenv '$$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_ENV)'
	$(if $(PIP_ARGS)$(strip $(2)),$$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))) -m pip --disable-pip-version-check install --no-use-wheel $(PIP_ARGS) $(2))
	touch $$@

.PHONY: $(strip $(1))_$(call LOWER_FN, $(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS)))))
$(strip $(1))_$(call LOWER_FN, $(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))): $$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_BUILD)
$(call $(3), $$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))_ENV), $$($(call UPPER_FN, $(1))_$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS))))))

.PHONY: $(strip $(1))
$(strip $(1)): _$(strip $(1))

.PHONY: _$(strip $(1))
_$(strip $(1)): $(strip $(1))$(call LOWER_FN, _$(call PYTHON_NAME_FN, $(if $(strip $(4)),$(4),$(firstword $(PYTHON_URLS)))))
endef

# Generate test rules - virtualenv, python
define TEST_COMMANDS_FN
	$(2) setup.py test $(if $(TEST),-s $(TEST))
endef
$(foreach X, $(PYTHON_URLS), $(eval $(call ENV_RULE, test, -e . -e .[tests], TEST_COMMANDS_FN, $(X))))

# Generate coverage rules - virtualenv, python
define COVER_COMMANDS_FN
	$(2) -m coverage run --branch --source $(PACKAGE_NAME) setup.py test
	$(2) -m coverage html -d $(COVER)
	$(2) -m coverage report
	@echo
	@echo Coverage report is $(COVER)/index.html
endef
$(eval $(call ENV_RULE, cover, -e . -e .[tests] coverage==4.0, COVER_COMMANDS_FN))

# Generate doc rules - virtualenv, python
HAS_DOC = $(shell if [ -d doc ]; then echo 1; fi)
define DOC_COMMANDS_FN
ifneq "$(HAS_DOC)" ""
	$(1)/bin/sphinx-build -b html -d $(DOC)/doctrees doc $(DOC)/html
	@echo
	@echo Doc index is $(DOC)/html/index.html
endif
endef
$(eval $(call ENV_RULE, doc, $(if $(HAS_DOC), sphinx==1.3.1), DOC_COMMANDS_FN))

# Generate pyint rules - virtualenv, python
define PYLINT_COMMANDS_FN
	$(2) -m pylint $(PYLINT_ARGS) $(PACKAGE_NAME)
endef
$(eval $(call ENV_RULE, pylint, -e . pylint==1.4.4, PYLINT_COMMANDS_FN, $(word 3, $(PYTHON_URLS))))
