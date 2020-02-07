# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

PYTHON_VERSIONS := \
    3.8 \
    3.7

SPHINX_DOC := doc

include Makefile.base

help:
	@echo '            [cover_test]'

define COVER_TEST_COMMANDS
.PHONY: cover_test_$(1)
cover_test_$(1): $(COVER_PYTHON_3_8_VENV_BUILD)
	$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage run --branch --source src -m unittest src.tests.test_$(1)
	$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage html -d $(BUILD)/coverage
	$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage report | grep '/$(1).py.*100%'

.PHONY: cover_test
cover_test: cover_test_$(1)
endef
$(foreach TEST, $(sort $(subst src/tests/test_,,$(subst .py,,$(wildcard src/tests/test_*.py)))), $(eval $(call COVER_TEST_COMMANDS,$(TEST))))
