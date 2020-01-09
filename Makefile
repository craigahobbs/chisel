# -*- makefile-gmake -*-
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

PYTHON_VERSIONS := \
    3.8 \
    3.7 \
    3.6 \
    3.5

COVERAGE_REPORT_ARGS := --fail-under 97

SPHINX_DOC := doc

include Makefile.base
