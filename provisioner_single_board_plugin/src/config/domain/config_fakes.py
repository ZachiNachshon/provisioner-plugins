#!/usr/bin/env python3

import yaml
from provisioner_single_board_plugin.src.config.domain.config import SingleBoardConfig

from provisioner_shared.components.remote.typer_remote_opts_fakes import TEST_REMOTE_CFG_YAML_TEXT

TEST_DATA_DOWNLOAD_PATH = "/test/path/to/download/os/image"
TEST_DATA_ACTIVE_SYSTEM = "64bit"
TEST_DATA_DOWNLOAD_URL_32BIT = "https://test-data-download-url-32bit.com"
TEST_DATA_DOWNLOAD_URL_64BIT = "https://test-data-download-url-64bit.com"
TEST_DATA_GW_IP_ADDRESS = "1.1.1.1"
TEST_DATA_DNS_IP_ADDRESS = "2.2.2.2"

TEST_DATA_YAML_TEXT = f"""
single_board:
  os:
    raspbian:
      download_path: {TEST_DATA_DOWNLOAD_PATH}
      active_system: {TEST_DATA_ACTIVE_SYSTEM}
      download_url:
        64bit: {TEST_DATA_DOWNLOAD_URL_64BIT}
        32bit: {TEST_DATA_DOWNLOAD_URL_32BIT}

  network:
    gw_ip_address: {TEST_DATA_GW_IP_ADDRESS}
    dns_ip_address: {TEST_DATA_DNS_IP_ADDRESS}
"""


class TestDataSingleBoardConfig:
    @staticmethod
    def create_fake_single_board_config() -> SingleBoardConfig:
        cfg_with_remote = TEST_DATA_YAML_TEXT + "\n" + TEST_REMOTE_CFG_YAML_TEXT
        cfg_dict = yaml.safe_load(cfg_with_remote)
        example_cfg = SingleBoardConfig(cfg_dict)
        return example_cfg
