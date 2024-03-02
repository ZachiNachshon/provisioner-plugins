#!/usr/bin/env python3

import os
import pathlib

from provisioner.config.manager.config_manager import ConfigManager
from provisioner.cli.entrypoint import EntryPoint
from provisioner.utils.package_loader import PackageLoader

from provisioner.config.domain.config import ProvisionerConfig

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/config/config.yaml"

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Typer is initialized.
I've added pre Typer run env var to control the visiblity of components debug logs
such as config-loader, package-loader etc..
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
ENV_VAR_LOCAL_DEV_MODE = "PROVISIONER_LOCAL_DEV"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)
is_local_dev = os.getenv(key=ENV_VAR_LOCAL_DEV_MODE, default=False)

app = EntryPoint.create_typer(
    title="Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)",
    config_resolver_fn=lambda: ConfigManager.instance().load(
        CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig, debug=debug_pre_init
    ),
)

PackageLoader.create().load_modules_fn(
    filter_keyword="provisioner",
    import_path="main",
    exclusions=["provisioner", "provisioner-features-lib"],
    callback=lambda module: module.append_to_cli(app),
    debug=debug_pre_init,
    is_local_dev=is_local_dev,
)

# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    app()
