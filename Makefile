# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE


# Download python-build
PYTHON_BUILD_DIR ?= ../python-build
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell [ -f $(PYTHON_BUILD_DIR)/$(notdir $(1)) ] && cp $(PYTHON_BUILD_DIR)/$(notdir $(1)) . || $(call WGET_CMD, $(1)))
endif
endef
WGET_CMD = if which wget; then wget -q -c $(1); else curl -f -Os $(1); fi
$(eval $(call WGET, https://craigahobbs.github.io/python-build/Makefile.base))
$(eval $(call WGET, https://craigahobbs.github.io/python-build/pylintrc))


# Sphinx documentation directory
SPHINX_DOC := doc


# Include python-build
include Makefile.base


# Development dependencies
TESTS_REQUIRE := bare-script


help:
	@echo "            [test-doc]"


clean:
	rm -rf Makefile.base pylintrc


doc:
    # Copy statics
	cp -R static/* build/doc/html/

    # Dump the documentation example
	mkdir -p build/doc/html/example
	cp src/chisel/static/index.html build/doc/html/example/
	cp src/chisel/static/chiselDoc.bare build/doc/html/example/
	$(DEFAULT_VENV_PYTHON) -c "$$DUMP_EXAMPLE_PY"


.PHONY: test-doc
commit: test-doc
test-doc: $(DEFAULT_VENV_BUILD)
	$(DEFAULT_VENV_BIN)/bare -s src/chisel/static/*.bare src/chisel/static/test/*.bare
	$(DEFAULT_VENV_BIN)/bare -m src/chisel/static/test/runTests.bare$(if $(DEBUG), -d)$(if $(TEST), -v vTest "'$(TEST)'")


# Python to dump documentation API responses
define DUMP_EXAMPLE_PY
import chisel
import json

app = chisel.Application()
app.pretty_output = True
app.add_requests(chisel.create_doc_requests())
_, _, response = app.request('GET', '/doc/doc_request', query_string='name=chisel_doc_request')
with open('build/doc/html/example/doc_request', 'wb') as request_file:
    request_file.write(response)
with open('build/doc/html/example/doc_index', 'w') as index_file:
    json.dump({'title': 'Chisel Documentation Example', 'groups': {'Documentation': ['chisel_doc_request']}}, index_file, indent=2)
endef
export DUMP_EXAMPLE_PY
