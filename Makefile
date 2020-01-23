# -*- makefile-gmake -*-
# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

PYTHON_VERSIONS := \
    3.8 \
    3.7 \
    3.6 \
    3.5

SPHINX_DOC := doc

include Makefile.base

define COVER_TEST_COMMANDS
.PHONY: cover_test_$(1)
cover_test_$(1): $(COVER_PYTHON_3_8_VENV_BUILD)
	$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage run --branch --source src -m unittest discover -v -t src -s src/tests -p test_$(1).py
	$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage html -d $(BUILD)/coverage
	$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage report | grep '/$(1).py.*100%'

commit: cover_test_$(1)
endef
$(foreach TEST, $(sort $(subst src/tests/test_,,$(subst .py,,$(wildcard src/tests/test_*.py)))), $(eval $(call COVER_TEST_COMMANDS,$(TEST))))
