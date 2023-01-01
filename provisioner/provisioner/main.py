#!/usr/bin/env python3

import os
import pathlib
from python_core_lib.cli.entrypoint import EntryPoint
from python_features_lib.config.config_resolver import ConfigResolver

from provisioner.config.domain.config import ProvisionerConfig

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/config/config.yaml"

ConfigResolver.load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, class_name=ProvisionerConfig)

app = EntryPoint.create_typer(title="Provision Everything Anywhere")    

# ======================
#  LIBRARY: INSTALLERS
# ======================
try:
    from python_installers_lib.main import append_installers
    append_installers(app)
except Exception as ex:
    print(f"Failed to load python installers commands. ex: {ex}")

# ========================
#  LIBRARY: SINGLE BOARD
# ========================
try:
    from python_single_board_lib.main import append_single_boards
    append_single_boards(app)
except Exception as ex:
    print(f"Failed to load single board commands. ex: {ex}")

# ====================
#  LIBRARY: EXAMPLES
# ====================
try:
    from python_examples_lib.main import append_examples
    append_examples(app)
except Exception as ex:
    print(f"Failed to load python example commands. ex: {ex}")

# ==============
#  ENTRY POINT
# ==============
def main():
    app()
