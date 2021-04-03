# Licensed under the MIT License
# https://github.com/craigahobbs/chisel/blob/master/LICENSE

# Download Javascript Build base makefile, etc.
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell if which wget; then wget -q $(1); else curl -Os $(1); fi)
endif
endef
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/schema-markdown/master/static/Makefile.base))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/schema-markdown/master/static/package.json))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/schema-markdown/master/static/.eslintrc.js))
$(eval $(call WGET, https://raw.githubusercontent.com/craigahobbs/schema-markdown/master/static/.npmrc))

include Makefile.base

NYC_ARGS := $(NYC_ARGS) --exclude src/schema-markdown

JSDOC_ARGS := -c jsdoc.json

clean:
	rm -rf Makefile.base package.json .eslintrc.js .npmrc

.PHONY: update-dependencies
update-dependencies:
	cp ../../schema-markdown/static/src/doc.css src/doc.css
	rsync --delete -r ../../schema-markdown/static/src/schema-markdown/ src/schema-markdown/
