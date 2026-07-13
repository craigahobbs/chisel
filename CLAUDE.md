# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Chisel is

Chisel is a lightweight Python WSGI application framework for building well-documented,
schema-validated JSON web APIs. Its one runtime dependency is
[schema-markdown](https://github.com/craigahobbs/schema-markdown-py), which supplies the
Schema Markdown parser, type validator, and query-string codec that Chisel is built around.

## Build system

This package uses [python-build](https://github.com/craigahobbs/python-build). The bulk of the
build logic lives in `Makefile.base` and `pylintrc`, which are **downloaded** from
`craigahobbs.github.io/python-build` on first `make` run and are git-ignored — do not edit them
(edit the top-level `Makefile` for project-specific targets). Every target runs inside an
auto-created virtualenv under `build/venv/`; you don't manage the venv yourself.

Common commands:

- `make test` — run the Python unit tests (`unittest discover` over `src/tests/`, with `-W error`)
- `make test TEST=tests.test_app.TestApplication.test_add_request` — run a single test / module / class
- `make lint` — pylint over `src`
- `make cover` — tests with branch coverage; **enforced at 100%** (`--fail-under 100`), so new code needs full coverage
- `make doc` — Sphinx build **including doctests**; the `>>>` examples in docstrings (e.g. in `app.py`, `action.py`) are executed and must pass
- `make commit` — runs `test lint doc cover` plus `test-doc` (the full pre-commit gate)
- `make clean` / `make superclean`
- `make changelog`, `make publish` — release tasks; version is set in `setup.cfg` and `CHANGELOG.md` is generated from git history

Supported Python versions are 3.10–3.14. To test across versions in containers, use
`make test USE_DOCKER=1` (or `USE_PODMAN=1`).

## Front-end / BareScript tests

`src/chisel/static/` holds the client-side documentation app, written in **BareScript**
(`chiselDoc.bare`), plus its `index.html` bootstrap and a vendored `markdown-up.tar.gz` (the
MarkdownUp runtime, served as static resources). These have their own test path:

- `make test-doc` — runs the BareScript unit tests via the `bare` CLI (from the `bare-script` dev
  dependency). It executes `runTests.bare`, which enforces 100% BareScript coverage.
- `make test-doc TEST='<name>'` — run a single BareScript test.
- `make markdown-up` — re-download / update the vendored `markdown-up.tar.gz`. Most CHANGELOG
  entries are just this tarball being bumped.

When editing `.bare` files, invoke the `bare-script` skill.

## Architecture

The Python package is `src/chisel/` with four small modules. The public API is re-exported from
`__init__.py`.

**`app.py` — WSGI core and routing.**
- `Application` is the WSGI callable. Requests are registered with `add_request(s)` and routed in
  `match_request` with this precedence: exact `(method, path)` → `(method, regex)` for paths with
  `{arg}` placeholders → `(None, path)` (any method) → `(None, regex)`. A path that matches some
  request but not the method yields `405`, otherwise `404`.
- `Context` encapsulates per-request state (WSGI `environ`, URL args, logger, response headers) and
  is stashed in `environ['chisel.ctx']` so requests can reach it. It provides the response helpers
  (`response`, `response_text`, `response_json`, `add_header`, `add_cache_headers`,
  `reconstruct_url`) and `create_environ` for building test environs.
- `Application.request(method, path, ...)` drives a full request in-process (used everywhere in
  tests and docstrings) and returns `(status, headers, content_bytes)`.

**`request.py` — request objects.** `Request` is the base class: it wraps a WSGI callback together
with hosting metadata (`name`, `urls`, `doc`, `doc_group`). `urls` normalizes to a tuple of
`(method-or-None, path)` pairs, defaulting to `/<name>`. Subclasses `RedirectRequest` and
`StaticRequest` (content-type by extension + MD5 ETag / 304 handling) override `__call__`. The
`request` decorator wraps a plain WSGI function as a `Request`.

**`action.py` — the schema-validated JSON API (the heart of the framework).** `Action` subclasses
`Request`. It parses a Schema Markdown `spec` (an `action <name>` definition with `urls`, `query`,
`input`, `path`, `output`, `errors` sections) via `schema-markdown`. On each request it:
1. deserializes JSON body (non-GET), decodes the query string, collects URL path args;
2. validates each source against its section schema, then **merges** them into one `req` dict
   (path and query keys copied to the top level);
3. calls `action_callback(ctx, req)` and, when `app.validate_output` is set, validates the returned
   dict against the `output` schema.
Validation failures become structured JSON errors (`InvalidInput` / `InvalidOutput` with the
offending `member`). Callbacks signal domain errors by raising `ActionError(error_code)`. Set
`wsgi_response=True` to return a raw WSGI response instead of a validated dict.

**`doc.py` — the documentation application.** `create_doc_requests()` is a generator of `Request`
objects (add them with `add_requests`). It yields two doc APIs — `chisel_doc_index` and
`chisel_doc_request` (both `Action`s that introspect the app's registered requests and their type
models) — plus the static HTML page, the `chiselDoc.bare` app, and the unpacked MarkdownUp tarball
statics. This is how any Chisel app gets a browsable `/doc/` site for free.

## Conventions

- Every source file starts with the MIT license header (two comment lines).
- Classes use `__slots__` throughout.
- Docstrings contain runnable doctests — keep them accurate, since `make doc` executes them.
- Coverage is 100% for both Python (`make cover`) and BareScript (`make test-doc`); a change that
  drops either below 100% fails `make commit`.
