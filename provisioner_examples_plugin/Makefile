default: help

POETRY_DEV=../../external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=../../external/shell_scripts_lib/python/poetry_pip_releaser.sh

.PHONY: deps
deps: ## Update and install pyproject.toml dependencies on the virtual environment
	@${POETRY_DEV} deps

.PHONY: typecheck
typecheck: ## Check for Python static type errors
	@${POETRY_DEV} types

.PHONY: fmtcheck
fmtcheck: ## Validate Python code format and sort imports
	@${POETRY_DEV} fmt --check-only

.PHONY: fmt
fmt: ## Format Python code using Black style and sort imports
	@${POETRY_DEV} fmt

.PHONY: test
test: ## Run tests suite
	@${POETRY_DEV} test

.PHONY: test-coverage-html
test-coverage-html: ## Run tests suite with HTML coverage report
	@sed -i '' '/# provisioner = { path = "..\/..\/provisioner", develop = true }/s/^# //' pyproject.toml
	@${POETRY_DEV} test --coverage-type html

.PHONY: test-coverage-xml
test-coverage-xml: ## Run tests suite with XML coverage report (for app.codecov.io)
	@sed -i '' '/# provisioner = { path = "..\/..\/provisioner", develop = true }/s/^# //' pyproject.toml
	@${POETRY_DEV} test --coverage-type xml

# http://localhost:9001/anchor/
.PHONY: docs-site
docs-site: ## Run a local documentation site
	@${POETRY_DEV} docs

# http://192.168.x.xx:9001/
.PHONY: docs-site-lan
docs-site-lan: ## Run a local documentation site (LAN available)
	@${POETRY_DEV} docs --lan

.PHONY: pip-install
pip-install: ## Install a source distribution to local pip
	@${POETRY_PIP_RELEASER} install --build-type sdist --multi-project

.PHONY: pip-uninstall
pip-uninstall: ## Uninstall a source distribution from local pip
	@${POETRY_PIP_RELEASER} delete --origin pypi-local

.PHONY: pip-publish-github
pip-publish-github: ## Publish a pip package tarball as a GitHub release
	@${POETRY_PIP_RELEASER} publish \
		--build-type sdist \
		--plugin \
		--release-type github \
		--release-tag $(shell cat ../provisioner/resources/version.txt)

.PHONY: clear-virtual-env
clear-virtual-env: ## Clear Poetry virtual environments
	@rm -rf .venv
	@echo Cleared.

.PHONY: pDev
pDev: ## Interact with ../external/.../poetry_dev.sh            (Usage: make pDev 'fmt --check-only')
	@${POETRY_DEV} $(filter-out $@,$(MAKECMDGOALS))

.PHONY: pReleaser
pReleaser: ## Interact with ../external/.../poetry_pip_releaser.sh   (Usage: make pReleaser 'install --build-type sdist --multi-project')
	@${POETRY_PIP_RELEASER} $(filter-out $@,$(MAKECMDGOALS))

.PHONY: run
run: ## Compile and run Provisioner CLI                        (Usage: make run '<command> <sub-command>')
	@poetry run example_plugin $(filter-out $@,$(MAKECMDGOALS))

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
