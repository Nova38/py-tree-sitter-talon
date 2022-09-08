# Docs

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = docs/_build

html: Makefile
	@$(SPHINXBUILD) -M "html" "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: html


# Tests

test:
	@python setup.py pytest
	@PYTHONPATH=. stubtest --mypy-config-file pyproject.toml tree_sitter_talon

.PHONY: test


# Bump versions

VERSION = $(shell poetry run tree-sitter-talon-version)

minor:
	@bumpver update
	@$(MAKE) release

major:
	@bumpver update
	@$(MAKE) release

release:
	@git tag "v$(VERSION)"
	@git push origin "v$(VERSION)"

.PHONY: minor major release
