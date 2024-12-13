#!/usr/bin/env python3

import importlib
import os
import pathlib

from loguru import logger
from provisioner_shared.components.runtime.config.domain.config import ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

from provisioner_shared.components.runtime.cli.entrypoint import EntryPoint
from provisioner_installers_plugin import main as installers_plugin_main

PLUGIN_IMPORT_PATH = "provisioner_installers_plugin.main"

PROVISIONER_CONFIG_DEV_INTERNAL_PATH = (
    f"{pathlib.Path(__file__).parent.parent.parent.parent}/provisioner/provisioner/resources/config.yaml"
)
CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Typer is initialized.
I've added pre Typer run env var to control the visiblity of components debug logs
such as config-loader, package-loader etc..
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
ENV_VAR_LOCAL_DEV_MODE = "PROVISIONER_LOCAL_DEV"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)

if not debug_pre_init:
    logger.remove()

app = EntryPoint.create_typer(
    title="Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)",
    config_resolver_fn=lambda: ConfigManager.instance().load(
        PROVISIONER_CONFIG_DEV_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig
    ),
)

try:
    logger.debug(f"Importing module {PLUGIN_IMPORT_PATH}")
    plugin_main_module = importlib.import_module(PLUGIN_IMPORT_PATH)
    logger.debug(f"Running module callback on {PLUGIN_IMPORT_PATH}")
    installers_plugin_main.load_config()
    installers_plugin_main.append_to_cli(app)
except Exception as ex:
    err_msg = f"Failed to import module. import_path: {PLUGIN_IMPORT_PATH}, ex: {ex}"
    logger.error(err_msg)
    raise Exception(err_msg)


# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    app()
