#!/usr/bin/env python3

import yaml
from provisioner_features_lib.remote.typer_remote_opts_fakes import TEST_REMOTE_CFG_YAML_TEXT

from provisioner_installers_plugin.config.domain.config import InstallersConfig


class TestDataInstallersConfig:
    @staticmethod
    def create_fake_example_config() -> InstallersConfig:
        cfg_with_remote = TEST_REMOTE_CFG_YAML_TEXT
        cfg_dict = yaml.safe_load(cfg_with_remote)
        installers_cfg = InstallersConfig(cfg_dict)
        return installers_cfg
