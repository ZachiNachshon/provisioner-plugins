default: help

SOURCE_DEV_DEPS_PATH=../../provisioner/pyproject.toml
DEV_DEPS=../../dev_deps.py
POETRY_DEV=../../external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=../../external/shell_scripts_lib/python/poetry_pip_releaser.sh

# This section allows us to make commands self aware with the OS we are running
# and adjust the sed command accordingly
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
    SED_INPLACE := -i
endif
ifeq ($(UNAME_S),Darwin)
    SED_INPLACE := -i ''
endif

.PHONY: set-dev-deps
set-dev-deps: ## Update dev dependencies and their config based on provisioner pyproject.toml
	@${DEV_DEPS} ${SOURCE_DEV_DEPS_PATH} pyproject.toml

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
	@${POETRY_DEV} test --coverage-type html

.PHONY: test-coverage-xml
test-coverage-xml: ## Run tests suite with XML coverage report (for app.codecov.io)
	@${POETRY_DEV} test --coverage-type xml

.PHONY: pip-install
pip-install: ## Install a source distribution to local pip
	@${POETRY_PIP_RELEASER} install --build-type sdist --multi-project

.PHONY: pip-uninstall
pip-uninstall: ## Uninstall a source distribution from local pip
	@${POETRY_PIP_RELEASER} delete --origin pypi-local

.PHONY: pip-publish-github
pip-publish-github: ## Publish a pip package tarball as a GitHub release
	@${POETRY_PIP_RELEASER} publish -y \
		--multi-project \
		--build-type wheel \
		--release-type github \
		--release-tag-prefix installers_plugin

.PHONY: pip-publish-pypi
pip-publish-pypi: ## Publish a pip package tarball as a PyPi release
	@${POETRY_PIP_RELEASER} publish --multi-project --build-type wheel --release-type pypi -y

.PHONY: clear-virtual-env
clear-virtual-env: ## Clear Poetry virtual environments
	@rm -rf .venv
	@echo Cleared.

.PHONY: use-provisioner-from-sources
use-provisioner-from-sources: ## Use provisioner from local sources
	@sed $(SED_INPLACE) '/# provisioner_runtime = { path = "..\/..\/provisioner", develop = true }/s/^# //' pyproject.toml
	@poetry lock
	@make deps

.PHONY: use-provisioner-from-pypi
use-provisioner-from-pypi: ## Use provisioner from remote PyPi
	@sed $(SED_INPLACE) '/# provisioner-runtime =/s/^# //' pyproject.toml
	@poetry lock
	@make deps

.PHONY: pDev
pDev: ## Interact with ../external/.../poetry_dev.sh            (Usage: make pDev 'fmt --check-only')
	@${POETRY_DEV} $(filter-out $@,$(MAKECMDGOALS))

.PHONY: pReleaser
pReleaser: ## Interact with ../external/.../poetry_pip_releaser.sh   (Usage: make pReleaser 'install --build-type sdist --multi-project')
	@${POETRY_PIP_RELEASER} $(filter-out $@,$(MAKECMDGOALS))

.PHONY: run
run: ## Compile and run Provisioner CLI                        (Usage: make run '<command> <sub-command>')
	@poetry run installers_plugin $(filter-out $@,$(MAKECMDGOALS))

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
