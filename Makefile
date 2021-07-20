# Exclude incompatible Python versions
PYTHON_IMAGES_EXCLUDE := python:3.6

# Sphinx documentation directory
SPHINX_DOC := doc

# Download Python Build base makefile and pylintrc
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell $(call WGET_CMD, $(1)))
endif
endef
WGET_CMD = if which wget; then wget -q $(1); else curl -Os $(1); fi
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/python-build/main/Makefile.base))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/python-build/main/pylintrc))

# Include Python Build
include Makefile.base

clean:
	rm -rf Makefile.base pylintrc

# Dump documentation API responses
define DUMP_DOC_APIS
import chisel
import json

def dump_doc_request(name):
    app = chisel.Application()
    app.pretty_output = True
    app.add_requests(chisel.create_doc_requests())
    _, _, response = app.request('GET', '/doc/doc_request', query_string=f'name={name}')
    with open(f'build/doc/html/{name}/doc_request', 'wb') as request_file:
        request_file.write(response)
    with open(f'build/doc/html/{name}/doc_index', 'w') as index_file:
        json.dump({'title': 'Chisel Documentation Application', 'groups': {'Documentation': [name]}}, index_file, indent=2)

dump_doc_request('chisel_doc_index')
dump_doc_request('chisel_doc_request')
endef

export DUMP_DOC_APIS

doc:
	mkdir -p build/doc/html/chisel_doc_index build/doc/html/chisel_doc_request
	cd build/doc/html/chisel_doc_index && $(call WGET_CMD, https://craigahobbs.github.io/chisel-doc/index.html)
	cd build/doc/html/chisel_doc_request && $(call WGET_CMD, https://craigahobbs.github.io/chisel-doc/index.html)
	$(DOC_DEFAULT_VENV_CMD)/python3 -c "$$DUMP_DOC_APIS"
