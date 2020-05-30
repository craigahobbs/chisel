.DEFAULT_GOAL := help

NODE_IMAGE ?= node:13-buster-slim
NODE_DOCKER := docker run --rm -u `id -u`:`id -g` -v `pwd`:`pwd` -w `pwd` -e HOME=`pwd`/build $(NODE_IMAGE)

build/npm.install:
	docker pull -q $(NODE_IMAGE)
	$(NODE_DOCKER) npm install
	mkdir -p $(dir $@)
	touch $@

.PHONY: help
help: _help

.PHONY: _help
_help:
	@echo 'usage: make [clean|commit|doc|lint|test]'

.PHONY: commit
commit: test lint doc

.PHONY: test
test: _test

.PHONY: _test
_test: build/npm.install
	$(NODE_DOCKER) npx nyc $(NYC_ARGS) --check-coverage --reporter html --reporter text \
		--report-dir build/coverage --temp-dir build/tmp ava $(AVA_ARGS) tests/test*.js

.PHONY: _lint
lint: _lint

.PHONY: _lint
_lint: build/npm.install
	$(NODE_DOCKER) npx eslint $(ESLINT_ARGS) -c .eslintrc.js -f unix .eslintrc.js src tests

.PHONY: doc
doc: _doc

.PHONY: _doc
_doc: build/npm.install
	$(NODE_DOCKER) npx jsdoc $(JSDOC_ARGS) --pedantic -d build/doc src

.PHONY: clean
clean: _clean

.PHONY: _clean
_clean:
	rm -rf build node_modules package-lock.json

.PHONY: superclean
superclean: clean
	docker rmi -f $(NODE_IMAGE)
