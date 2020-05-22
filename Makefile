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


# Dump API docs into doc build "doc" folder
define DUMP_DOC_APIS
import os
import sys
import chisel

# Create the chisel application with documentation application
application = chisel.Application()
application.pretty_output = True
application.add_requests(chisel.create_doc_requests())

# Dump chisel_doc_index API response
doc_dir = sys.argv[1]
_, _, index_bytes = application.request('GET', '/doc/doc_index')
with open(os.path.join(doc_dir, 'doc_index'), 'wb') as file:
	file.write(index_bytes)

# Dump chisel_doc_request API response for each request
request_dir = os.path.join(doc_dir, 'doc_request')
os.mkdir(request_dir)
for name in application.requests.keys():
	_, _, content_bytes = application.request('GET', f'/doc/doc_request/{name}')
	with open(os.path.join(request_dir, name), 'wb') as file:
		file.write(content_bytes)
endef
export DUMP_DOC_APIS

doc:
	rsync -rv --delete static/src/ build/doc/html/doc/
	$(DOC_PYTHON_3_8_VENV_CMD)/python3 -c "$$DUMP_DOC_APIS" build/doc/html/doc
