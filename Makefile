default: help

POETRY_WRAPPER=./runners/poetry_runner.sh
POETRY_WRAPPER_DEV=./runners/poetry_runner_dev.sh
PROJECT_LOCATION=.

.PHONY: install-sdist
install-sdist: ## Install a source distribution locally
	@./runners/install_sdist.sh

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

# To test a single test file run - poetry run coverage run -m pytest python_scripts_lib/utils/network_test.py
.PHONY: test-all
# test: fmtcheck ## Run Unit/E2E/IT tests
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

# @cd python_core_lib; make test; cd ..

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
