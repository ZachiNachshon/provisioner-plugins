default: help

POETRY_WRAPPER=./runners/poetry_runner.sh
POETRY_WRAPPER_DEV=./runners/poetry_runner_dev.sh
PROJECT_LOCATION=.
POETRY_PIP_RELEASER=./external/shell_scripts_lib/python/poetry_pip_releaser.sh

.PHONY: update-externals
update-externals: ## Update external source dependents
	@git-deps-syncer sync-all -y

.PHONY: clear-virtual-env
clear-virtual-env: ## Clear Poetry virtual environments
	@rm -rf .venv

# Add -vv for debug logs
.PHONY: create-update-venv
create-update-venv: ## Create/Update a Python virtual env
	@${POETRY_WRAPPER_DEV} update   # Update latest changes in pyproject.toml lock file
	@${POETRY_WRAPPER_DEV} install  # Download and install dependencies
	@${POETRY_WRAPPER_DEV} build    # Build a tarball package with local Python wheel

.PHONY: fmt
fmt: ## Format Python code using Black style and sort imports
	@echo "Formatting Python code using Black style..."
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION}
	@echo "Sorting/cleaning import statements..."
	@${POETRY_WRAPPER_DEV} run isort ${PROJECT_LOCATION}

.PHONY: fmtcheck
fmtcheck: ## Validate Python code format and sort imports
	@echo "Validate Python code formatting..."
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION} --check
	@echo "Checking import statements..."
	@${POETRY_WRAPPER_DEV} run isort ${PROJECT_LOCATION} --check-only

.PHONY: typecheck
typecheck: ## Check for Python static types errors (https://mypy.readthedocs.io/en/stable/index.html)
	@${POETRY_WRAPPER_DEV} run mypy python_core_lib/**/*.py

# To test a single test file run - poetry run coverage run -m pytest python_core_lib/utils/network_test.py
.PHONY: test
# test: fmtcheck ## Run Unit/E2E/IT tests
test: ## Run Unit/E2E/IT tests
	@echo "Cleaning up previous runs..."
	-@rm -rf "$(PWD)/htmlcov"
	@echo "Done."
	@echo "\nRunning tests/coverage..."
	-@${POETRY_WRAPPER_DEV} run coverage run -m pytest 
	-@${POETRY_WRAPPER} run coverage report
	-@${POETRY_WRAPPER} run coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

.PHONY: test-ci
# test-ci: fmtcheck ## Run Unit/E2E/IT tests with XML report for app.codecov.io
test-ci: ## Run Unit/E2E/IT tests with XML report for app.codecov.io
	@echo "Cleaning up previous runs..."
	-@rm -rf "$(PWD)/coverage.xml"
	@echo "Done."
	@echo "\nRunning tests/coverage..."
	@${POETRY_WRAPPER_DEV} run coverage run -m pytest
	@${POETRY_WRAPPER} run coverage report
	@${POETRY_WRAPPER} run coverage xml
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/coverage.xml\n"

.PHONY: pip-install
pip-install: ## Install a source distribution to local pip
	@${POETRY_PIP_RELEASER} install --build-type sdist --plugin

.PHONY: pip-uninstall
pip-uninstall: ## Uninstall a source distribution from local pip
	@${POETRY_PIP_RELEASER} delete --origin pypi-local

.PHONY: pip-github-publish
pip-github-publish: ## Publish a pip package tarball as a GitHub release
	@GITHUB_TOKEN=${GITHUB_TOKEN} ${POETRY_PIP_RELEASER} publish \
		--build-type sdist \
		--plugin \
		--release-type github \
		--release-tag $(shell cat ./resources/version.txt)

.PHONY: pip-github-delete-tag
pip-github-delete-tag: ## Publish a pip package tarball as a GitHub release
	@GITHUB_TOKEN=${GITHUB_TOKEN} ${POETRY_PIP_RELEASER} delete \
		--origin github \
		--delete-tag $(shell cat ./resources/version.txt)

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
