#!/usr/bin/env python3

from provisioner_installers_plugin.installer.domain.config import InstallerConfig


class TestDataclassInstallerConfig:
    @staticmethod
    def create_fake_installer_config() -> InstallerConfig:
        return InstallerConfig()
