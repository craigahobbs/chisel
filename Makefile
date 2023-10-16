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


# Include python-build
include Makefile.base


clean:
	rm -rf Makefile.base pylintrc package.json package-lock.json node_modules/


doc:
	cp -R static/* build/doc/html/
	mkdir -p build/doc/html/example
	$(DEFAULT_VENV_CMD)/python3 -c "$$DUMP_EXAMPLE"


# Python to dump documentation API responses
define DUMP_EXAMPLE
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
export DUMP_EXAMPLE


# Node
NODE_IMAGE ?= node:current-slim
NODE_DOCKER := $(if $(NO_DOCKER),,docker run -i --rm -u `id -u`:`id -g` -v `pwd`:`pwd` -w `pwd` -e HOME=`pwd`/build $(NODE_IMAGE))


.PHONY: test-doc
commit: test-doc
test-doc: build/npm.build
	$(NODE_DOCKER) npx bare -s static/doc/*.mds static/doc/test/*.mds
	$(NODE_DOCKER) npx bare -c 'include <markdownUp.bare>' static/doc/test/runTests.mds


build/npm.build:
ifeq '$(NO_DOCKER)' ''
	if [ "$$(docker images -q $(NODE_IMAGE))" = "" ]; then docker pull -q $(NODE_IMAGE); fi
endif
	echo '{"type":"module","devDependencies":{"bare-script":"*"}}' > package.json
	$(NODE_DOCKER) npm install
	mkdir -p $(dir $@)
	touch $@
