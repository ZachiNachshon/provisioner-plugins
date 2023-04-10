default: help

POETRY_WRAPPER=./runners/poetry_runner.sh
POETRY_WRAPPER_DEV=./runners/poetry_runner_dev.sh
PROJECT_LOCATION=.

.PHONY: fmt-all
fmt-all: ## Format Python code using Black style and sort imports
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make fmt; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make fmt; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make fmt; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make fmt; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make fmt; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make fmt; cd ..

.PHONY: typecheck-all
typecheck-all: ## Check for Python static types errors (https://mypy.readthedocs.io/en/stable/index.html)
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make typecheck; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make typecheck; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make typecheck; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make typecheck; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make typecheck; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make typecheck; cd ..

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
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make test; cd ..

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

.PHONY: update-externals-all
update-externals-all: ## Update external source dependents
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make update-externals; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make update-externals; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make update-externals; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make update-externals; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make update-externals; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make update-externals; cd ..

.PHONY: ci-test-all
# ci-test-all: fmtcheck-all ## Run Unit/E2E/IT tests
ci-test-all: ## Run Unit/E2E/IT tests
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make test-ci; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make test-ci; cd ..
	@coverage combine \
		provisioner/.coverage \
		provisioner_examples_plugin/.coverage \
		provisioner_features_lib/.coverage \
		provisioner_installers_plugin/.coverage \
		provisioner_single_board_plugin/.coverage
	@coverage xml -o coverage-combined.xml

.PHONY: ci-install-deps-all
ci-install-deps-all: ## Install all modules dependencies
	@pip install coverage
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; poetry install --all-extras; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; poetry install; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; poetry install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; poetry install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; poetry install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; poetry install; cd ..
	@echo "\n\n========= COMBINING COVERAGE.XML FILES ==========\n\n"

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
