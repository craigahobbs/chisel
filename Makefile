# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

PYTHON_VERSIONS := \
    3.8 \
    3.9-rc \
    3.7

SPHINX_DOC := doc

include Makefile.base

help:
	@echo '            [cover-test]'


# Delegate commit, clean, and superclean to the static sub-project
.PHONY: commit-static
commit-static:
	$(MAKE) -C static commit

commit: commit-static

clean:
	$(MAKE) -C static clean

superclean:
	$(MAKE) -C static superclean


# Test each sub-module's test coverage with its own test sub-module
define COVER_TEST_COMMANDS
.PHONY: cover-test-$(1)
cover-test-$(1): $$(COVER_PYTHON_3_8_VENV_BUILD)
	$$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage run --branch --source src -m unittest -v src.tests.test_$(1)
	$$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage html -d $(BUILD)/coverage
	$$(COVER_PYTHON_3_8_VENV_CMD)/python3 -m coverage report | grep '/$(1).py.*100%'

.PHONY: cover-test
cover-test: cover-test-$(1)
endef
$(foreach TEST, $(sort $(subst src/tests/test_,,$(subst .py,,$(wildcard src/tests/test_*.py)))), $(eval $(call COVER_TEST_COMMANDS,$(TEST))))

define DOC_PAGE_RUN_REPLACE
s/DocPage.run()/import {getTypeModel} from '.\/chisel.js';\n        DocPage.run(getTypeModel(), 'The Chisel Type Model')/
endef
export DOC_PAGE_RUN_REPLACE

doc:
	rsync -rv --delete static/src/ build/doc/html/doc/
	sed "$$DOC_PAGE_RUN_REPLACE" build/doc/html/doc/doc.html > build/doc/html/doc/index.html
	rm build/doc/html/doc/doc.html
