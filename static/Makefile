# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# Download JavaScript Build
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell if which wget; then wget -q $(1); else curl -Os $(1); fi)
endif
endef
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/Makefile.base))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/jsdoc.json))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/package.json))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/javascript-build/main/.eslintrc.cjs))

# Disable gh-pages
GHPAGES_SRC :=

# Include JavaScript Build
include Makefile.base

# Exclude external code from coverage
COVER_ARGS := --exclude src/doc/schema-markdown

clean:
	rm -rf Makefile.base jsdoc.json package.json .eslintrc.cjs

.PHONY: update-dependencies
update-dependencies:
	cp ../../schema-markdown/static/src/doc.css src/doc.css
	cp ../../schema-markdown/static/src/doc.svg src/doc.svg
	rsync --delete -r ../../schema-markdown/static/src/schema-markdown/ src/doc/schema-markdown/
