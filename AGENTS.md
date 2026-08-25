# AGENTS.md

Notes for coding agents working in this repository.

## What Chisel is

Chisel is a lightweight Python WSGI application framework for building well-documented,
schema-validated JSON web APIs. Its one runtime dependency is
[schema-markdown](https://github.com/craigahobbs/schema-markdown-py), which supplies the
Schema Markdown parser, type validator, and query-string codec that Chisel is built around.

## python-build

This is a [python-build](https://github.com/craigahobbs/python-build#readme) package. Read the python-build skill before running tests, lint, coverage, or changing the Makefile: [`../python-build/SKILL.md`](../python-build/SKILL.md) if that file exists, otherwise [https://raw.githubusercontent.com/craigahobbs/python-build/main/SKILL.md](https://raw.githubusercontent.com/craigahobbs/python-build/main/SKILL.md).

Local Makefile overrides:

- `SPHINX_DOC` — `doc` (Sphinx; `>>>` doctests in docstrings, e.g. `app.py` and `action.py`, must pass)
- `TESTS_REQUIRE` — `bare-script`
- `commit` also depends on `test-doc`

Package-specific targets:

- `make test-doc` — BareScript unit tests for `src/chisel/static/` via the `bare` CLI (`TEST=` is an exact BareScript test name)
- `make markdown-up` — re-download vendored `src/chisel/static/markdown-up.tar.gz`

When editing `.bare` files, invoke the `bare-script` skill.

## Front-end / BareScript tests

`src/chisel/static/` holds the client-side documentation app, written in **BareScript**
(`chiselDoc.bare`), plus its `index.html` bootstrap and a vendored `markdown-up.tar.gz` (the
MarkdownUp runtime, served as static resources). `make test-doc` runs `runTests.bare`, which
enforces 100% BareScript coverage. Most CHANGELOG entries are the tarball being bumped.

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
