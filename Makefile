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

COVERAGE_FAIL_UNDER := 96

include Makefile.base
