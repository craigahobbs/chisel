# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# Download Javascript Build base makefile, etc.
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell if which wget; then wget -q $(1); else curl -Os $(1); fi)
endif
endef
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/Makefile.base))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/package.json))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/.eslintrc.js))

# Include Javascript Build
include Makefile.base

# Exclude external code from coverage
NYC_ARGS := --exclude src/schema-markdown

clean:
	rm -rf Makefile.base package.json .eslintrc.js

.PHONY: update-dependencies
update-dependencies:
	cp ../../schema-markdown/static/src/doc.css src/doc.css
	cp ../../schema-markdown/static/src/doc.svg src/doc.svg
	rsync --delete -r ../../schema-markdown/static/src/schema-markdown/ src/schema-markdown/
