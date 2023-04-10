default: help

POETRY_WRAPPER=./runners/poetry_runner.sh
POETRY_WRAPPER_DEV=./runners/poetry_runner_dev.sh
PROJECT_LOCATION=.

.PHONY: install-deps-all
install-deps-all: ## Create/Update a Python virtual env
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; poetry install --all-extras; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; poetry install; cd ..
	# @echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	# @cd python_core_lib; poetry install; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; poetry install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; poetry install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; poetry install; cd ..

.PHONY: fmt-all
fmt-all: ## Format Python code using Black style and sort imports
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make fmt; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make fmt; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make fmt; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make fmt; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make fmt; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make fmt; cd ..

.PHONY: fmtcheck-all
fmtcheck-all: ## Validate Python code format and sort imports
	@echo "Validate all Python modules formatting..."
	@${POETRY_WRAPPER_DEV} run black ${PROJECT_LOCATION} --check
	@echo "Checking import statements..."
	@${POETRY_WRAPPER_DEV} run isort ${PROJECT_LOCATION} --check-only

.PHONY: typecheck-all
typecheck-all: ## Check for Python static types errors (https://mypy.readthedocs.io/en/stable/index.html)
	@${POETRY_WRAPPER_DEV} run mypy */**/*.py

# .PHONY: diagrams
# diagrams: ## Format Python code using Black style (https://black.readthedocs.io)
# 	@${POETRY_WRAPPER_DEV} run diagrams ${PROJECT_LOCATION}/rpi/os/diagrams/install_diag.py

.PHONY: test-all
# test: fmtcheck-all ## Run Unit/E2E/IT tests
test-all: ## Run Unit/E2E/IT tests
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make test; cd ..
	# @echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	# @cd python_core_lib; make test; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make test; cd ..

.PHONY: test-ci-all
# test-ci-all: fmtcheck-all ## Run Unit/E2E/IT tests
test-ci-all: ## Run Unit/E2E/IT tests
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make test-ci; cd ..
	# @echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	# @cd python_core_lib; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make test-ci; cd ..

.PHONY: pip-install-all
pip-install-all: ## pip install all packages locally
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make pip-install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make pip-install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make pip-install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make pip-install; cd ..

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
