#!/usr/bin/env python3

import yaml
from provisioner_installers_plugin.src.config.domain.config import InstallersConfig

from provisioner_shared.components.remote.remote_opts_fakes import TEST_REMOTE_CFG_YAML_TEXT


class TestDataInstallersConfig:
    @staticmethod
    def create_fake_installers_config() -> InstallersConfig:
        cfg_with_remote = TEST_REMOTE_CFG_YAML_TEXT
        cfg_dict = yaml.safe_load(cfg_with_remote)
        installers_cfg = InstallersConfig(cfg_dict)
        return installers_cfg
