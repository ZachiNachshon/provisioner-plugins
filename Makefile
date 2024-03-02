# default: help
# PLUGINS=examples installers single_board

# POETRY_DEV=external/shell_scripts_lib/python/poetry_dev.sh
# POETRY_PIP_RELEASER=external/shell_scripts_lib/python/poetry_pip_releaser.sh

# .PHONY: update-externals
# update-externals: ## Update external source dependents
# 	@git-deps-syncer sync shell_scripts_lib -y

# .PHONY: deps-all
# deps-all: ## Update and install pyproject.toml dependencies on all virtual environments
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make deps; cd ..; \
# 	done

# .PHONY: typecheck-all
# typecheck-all: ## Check for Python static type errors
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make typecheck; cd ..; \
# 	done

# .PHONY: fmtcheck-all
# fmtcheck-all: ## Validate Python code format and sort imports
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make fmtcheck; cd ..; \
# 	done

# .PHONY: fmt-all
# fmt-all: ## Format Python code using Black style and sort imports
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make fmt; cd ..; \
# 	done

# .PHONY: test-all
# test-all: ## Run tests suite
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make test; cd ..; \
# 	done
# 	@echo "\n========= COMBINING COVERAGE DATABASES ==============\n"
# 	@coverage combine \
# 		provisioner_examples_plugin/.coverage \
# 		provisioner_installers_plugin/.coverage \
# 		provisioner_single_board_plugin/.coverage
# 	@echo "\n========= COVERAGE FULL REPORT ======================\n"		
# 	@coverage report
# 	@coverage html
# 	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

# .PHONY: test-coverage-xml-all
# test-coverage-xml-all: ## Run Unit/E2E/IT tests
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make test-coverage-xml; cd ..; \
# 	done

# .PHONY: pip-install-all
# pip-install-all: ## Install all source distributions to local pip
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make pip-install; cd ..; \
# 	done

# .PHONY: pip-uninstall-all
# pip-uninstall-all: ## Uninstall all source distributions from local pip
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make pip-uninstall; cd ..; \
# 	done

# .PHONY: pip-publish-github
# pip-publish-github: ## Publish all pip packages tarballs as GitHub releases
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make pip-publish-github; cd ..; \
# 	done

# .PHONY: clear-virtual-env-all
# clear-virtual-env-all: ## Clear all Poetry virtual environments
# 	@for plugin in $(PLUGINS); do \
# 		echo "\n========= PLUGIN: $$plugin ==============\n"; \
# 		cd provisioner_$${plugin}_plugin; make clear-virtual-env; cd ..; \
# 	done

# .PHONY: pDev
# pDev: ## Interact with ./external/.../poetry_dev.sh            (Usage: make pDev 'fmt --check-only')
# 	@${POETRY_DEV} $(filter-out $@,$(MAKECMDGOALS))

# .PHONY: pReleaser
# pReleaser: ## Interact with ./external/.../poetry_pip_releaser.sh   (Usage: make pReleaser 'install --build-type sdist --multi-project')
# 	@${POETRY_PIP_RELEASER} $(filter-out $@,$(MAKECMDGOALS))

# # .PHONY: diagrams
# # diagrams: ## Format Python code using Black style (https://black.readthedocs.io)
# # 	@${POETRY_WRAPPER_DEV} run diagrams ${PROJECT_LOCATION}/rpi/os/diagrams/install_diag.py

# .PHONY: help
# help:
# 	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
