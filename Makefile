# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/main/LICENSE


# Download python-build
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell $(call WGET_CMD, $(1)))
endif
endef
WGET_CMD = if which wget; then wget -q -c $(1); else curl -f -Os $(1); fi
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/python-build/main/Makefile.base))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/python-build/main/pylintrc))


# Sphinx documentation directory
SPHINX_DOC := doc

# Development dependencies
TESTS_REQUIRE := bare-script

# Include python-build
include Makefile.base


help:
	@echo "            [test-doc]"


clean:
	rm -rf Makefile.base pylintrc


doc:
    # Copy statics
	cp -R static/* build/doc/html/

    # Dump the documentation example
	mkdir -p build/doc/html/example
	$(DEFAULT_VENV_PYTHON) -c "$$DUMP_EXAMPLE_PY"


.PHONY: test-doc
commit: test-doc
test-doc: $(DEFAULT_VENV_BUILD)
	$(DEFAULT_VENV_BIN)/bare -s static/doc/*.mds static/doc/test/*.mds
	$(DEFAULT_VENV_BIN)/bare -c 'include <markdownUp.bare>' static/doc/test/runTests.mds$(if $(TEST), -v vTest "'$(TEST)'")


# Python to dump documentation API responses
define DUMP_EXAMPLE_PY
import chisel
from chisel.doc import CHISEL_DOC_HTML
import json

app = chisel.Application()
app.pretty_output = True
app.add_requests(chisel.create_doc_requests())
_, _, response = app.request('GET', '/doc/doc_request', query_string=f'name=chisel_doc_request')
with open(f'build/doc/html/example/index.html', 'wb') as request_file:
    request_file.write(CHISEL_DOC_HTML)
with open(f'build/doc/html/example/doc_request', 'wb') as request_file:
    request_file.write(response)
with open(f'build/doc/html/example/doc_index', 'w') as index_file:
    json.dump({'title': 'Chisel Documentation Example', 'groups': {'Documentation': ['chisel_doc_request']}}, index_file, indent=2)
endef
export DUMP_EXAMPLE_PY
