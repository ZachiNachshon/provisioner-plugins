default: help

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

.PHONY: deps-all
deps-all: ## Update and install pyproject.toml dependencies on all virtual environments
	@pip install coverage
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make deps; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make deps; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make deps; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make deps; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make deps; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make deps; cd ..

.PHONY: typecheck-all
typecheck-all: ## Check for Python static type errors
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

.PHONY: fmtcheck-all
fmtcheck-all: ## Validate Python code format and sort imports
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make fmtcheck; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make fmtcheck; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make fmtcheck; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make fmtcheck; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make fmtcheck; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make fmtcheck; cd ..

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

.PHONY: test-all
test-all: ## Run tests suite
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make test; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make test; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make test; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make test; cd ..
	@echo "\n\n========= COMBINING COVERAGE DATABASES ==============\n\n"
	@coverage combine \
		provisioner/.coverage \
		python_core_lib/.coverage \
		provisioner_features_lib/.coverage \
		provisioner_examples_plugin/.coverage \
		provisioner_installers_plugin/.coverage \
		provisioner_single_board_plugin/.coverage
	@echo "\n\n========= COVERAGE FULL REPORT ======================\n\n"		
	@coverage report
	@coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

.PHONY: test-coverage-xml-all
test-coverage-xml-all: ## Run Unit/E2E/IT tests
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make test-coverage-xml; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: CORE ==================\n\n"
	@cd python_core_lib; make test-coverage-xml; cd ..
	@echo "\n\n========= PROVISIONER LIBRARY: FEATURES =============\n\n"
	@cd provisioner_features_lib; make test-coverage-xml; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make test-coverage-xml; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make test-coverage-xml; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make test-coverage-xml; cd ..

.PHONY: pip-install-all
pip-install-all: ## Install all source distributions to local pip
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make pip-install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make pip-install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make pip-install; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make pip-install; cd ..

.PHONY: pip-uninstall-all
pip-uninstall-all: ## Uninstall all source distributions from local pip
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make pip-uninstall; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make pip-uninstall; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make pip-uninstall; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make pip-uninstall; cd ..

.PHONY: pip-publish-github
pip-publish-github: ## Publish all pip packages tarballs as GitHub releases
	@echo "\n\n========= PROVISIONER ===============================\n\n"
	@cd provisioner; make pip-publish-github; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: EXAMPLES ==============\n\n"
	@cd provisioner_examples_plugin; make pip-publish-github; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: INSTALLERS ============\n\n"
	@cd provisioner_installers_plugin; make pip-publish-github; cd ..
	@echo "\n\n========= PROVISIONER PLUGIN: SINGLE BOARD ==========\n\n"
	@cd provisioner_single_board_plugin; make pip-publish-github; cd ..

# .PHONY: diagrams
# diagrams: ## Format Python code using Black style (https://black.readthedocs.io)
# 	@${POETRY_WRAPPER_DEV} run diagrams ${PROJECT_LOCATION}/rpi/os/diagrams/install_diag.py

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
