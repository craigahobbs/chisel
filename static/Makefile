.DEFAULT_GOAL := help

NODE_IMAGE := node:13-buster-slim
NODE_DOCKER := docker run --rm -u `id -u`:`id -g` -v $(CURDIR):$(CURDIR) -w $(CURDIR) -e HOME=$(CURDIR)/build $(NODE_IMAGE)

build/npm.install:
	$(NODE_DOCKER) npm install
	mkdir -p $(dir $@)
	touch $@

.PHONY: help
help:
	@echo 'usage: make [clean|commit|eslint]'

.PHONY: commit
commit: eslint

.PHONY: eslint
eslint: build/npm.install
	$(NODE_DOCKER) npx eslint -c .eslintrc.js -f unix .eslintrc.js src

.PHONY: clean
clean:
	rm -rf build node_modules package-lock.json

.PHONY: superclean
superclean: clean
	docker rmi -f $(NODE_IMAGE)
