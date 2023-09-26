default: help
PLUGINS=examples installers single_board

POETRY_DEV=external/shell_scripts_lib/python/poetry_dev.sh
POETRY_PIP_RELEASER=external/shell_scripts_lib/python/poetry_pip_releaser.sh

# Generate SSH key for GitHub action:
#  1. On local machine: ssh-keygen -t ed25519 -C "GitHub Actions"
#  2. Add the public key as a deploy key to the repository you want to access:
#     - Go to the repository’s settings page on GitHub.
#     - Click on “Deploy keys” in the left sidebar.
#     - Click on “Add deploy key”.
#     - Enter a title for the key and paste the contents of the public key file into the “Key” field.
#     - Click on “Add key”.
#  3. Add the private key as a secret in the repository running the workflow:
#     - Go to the repository’s settings page on GitHub.
#     - Click on “Secrets” in the left sidebar and then "Actions".
#     - Click on “New repository secret”.
#     - Enter a name for the secret, such as SSH_PRIVATE_KEY, and paste the contents of the private key file into the “Value” field.
#     - Click on “Add secret”.
#  4. Copy the code snippet from .github/workflows/ci.yaml SSH loading step

.PHONY: update-externals
update-externals: ## Update external source dependents
	@git-deps-syncer sync shell_scripts_lib -y

.PHONY: deps-all
deps-all: ## Update and install pyproject.toml dependencies on all virtual environments
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make deps; cd ..; \
	done

.PHONY: typecheck-all
typecheck-all: ## Check for Python static type errors
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make typecheck; cd ..; \
	done

.PHONY: fmtcheck-all
fmtcheck-all: ## Validate Python code format and sort imports
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make fmtcheck; cd ..; \
	done

.PHONY: fmt-all
fmt-all: ## Format Python code using Black style and sort imports
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make fmt; cd ..; \
	done

.PHONY: test-all
test-all: ## Run tests suite
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make test; cd ..; \
	done
	@echo "\n========= COMBINING COVERAGE DATABASES ==============\n"
	@coverage combine \
		provisioner_examples_plugin/.coverage \
		provisioner_installers_plugin/.coverage \
		provisioner_single_board_plugin/.coverage
	@echo "\n========= COVERAGE FULL REPORT ======================\n"		
	@coverage report
	@coverage html
	-@echo "\n====\n\nFull coverage report available on the following link:\n\n  • $(PWD)/htmlcov/index.html\n"

.PHONY: test-coverage-xml-all
test-coverage-xml-all: ## Run Unit/E2E/IT tests
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make test-coverage-xml; cd ..; \
	done

.PHONY: pip-install-all
pip-install-all: ## Install all source distributions to local pip
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make pip-install; cd ..; \
	done

.PHONY: pip-uninstall-all
pip-uninstall-all: ## Uninstall all source distributions from local pip
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make pip-uninstall; cd ..; \
	done

.PHONY: pip-publish-github
pip-publish-github: ## Publish all pip packages tarballs as GitHub releases
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make pip-publish-github; cd ..; \
	done

.PHONY: clear-virtual-env-all
clear-virtual-env-all: ## Clear all Poetry virtual environments
	@for plugin in $(PLUGINS); do \
		echo "\n========= PLUGIN: $$plugin ==============\n"; \
		cd provisioner_$${plugin}_plugin; make clear-virtual-env; cd ..; \
	done

.PHONY: pDev
pDev: ## Interact with ./external/.../poetry_dev.sh            (Usage: make pDev 'fmt --check-only')
	@${POETRY_DEV} $(filter-out $@,$(MAKECMDGOALS))

.PHONY: pReleaser
pReleaser: ## Interact with ./external/.../poetry_pip_releaser.sh   (Usage: make pReleaser 'install --build-type sdist --multi-project')
	@${POETRY_PIP_RELEASER} $(filter-out $@,$(MAKECMDGOALS))

# .PHONY: diagrams
# diagrams: ## Format Python code using Black style (https://black.readthedocs.io)
# 	@${POETRY_WRAPPER_DEV} run diagrams ${PROJECT_LOCATION}/rpi/os/diagrams/install_diag.py

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
