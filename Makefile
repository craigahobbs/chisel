# -*- makefile-gmake -*-
# Copyright (C) 2012-2017 Craig Hobbs
#
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

PACKAGE_NAME := chisel

PYTHON_VERSIONS := \
    3.7.0 \
    3.6.6 \
    3.5.5

COVERAGE_REPORT_ARGS := --fail-under 96

SPHINX_DOC := doc

include Makefile.base

# Add additional help
help:
	@echo "       make [run]"

# Run a local server
PORT ?= 8080
define RUN_COMMANDS_FN
	$(1)/python3 -u -m chisel $(ARGS) -p $(PORT)
endef
$(eval $(call VENV_RULE_FN, run, -e ., RUN_COMMANDS_FN,, -p $(PORT):$(PORT)))
