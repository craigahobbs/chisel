PYTHON_VERSIONS := \
    3.9 \
    3.10-rc \
    3.8 \
    3.7

# Sphinx documentation directory
SPHINX_DOC := doc

# Download Python Build base makefile and pylintrc
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
    $$(info Downloading $(notdir $(1)))
    $$(shell if which wget > /dev/null; then wget -q '$(strip $(1))'; else curl -Os '$(strip $(1))'; fi)
endif
endef
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/python-build/master/Makefile.base))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/python-build/master/pylintrc))

# Include Python Build
include Makefile.base

clean:
	rm -rf Makefile.base pylintrc
	$(MAKE) -C static clean

superclean:
	$(MAKE) -C static superclean

.PHONY: commit-static
commit-static:
	$(MAKE) -C static commit

commit: commit-static

define DUMP_DOC_APIS
import sys
import chisel
application = chisel.Application()
application.pretty_output = True
application.add_requests(chisel.create_doc_requests())
_, _, index_bytes = application.request('GET', '/doc/doc_index')
_, _, request_bytes = application.request('GET', '/doc/doc_request', query_string='name=chisel_doc_request')
with open(sys.argv[1], 'wb') as file:
    file.write(index_bytes)
with open(sys.argv[2], 'wb') as file:
    file.write(request_bytes)
endef
export DUMP_DOC_APIS

doc:
	rsync -rv --delete static/src/ build/doc/html/doc/
	mv build/doc/html/doc/doc.html build/doc/html/doc/index.html
	$(DOC_PYTHON_3_9_VENV_CMD)/python3 -c "$$DUMP_DOC_APIS" build/doc/html/doc/doc_index build/doc/html/doc/doc_request
