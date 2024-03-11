#!/usr/bin/env python3

import yaml
from provisioner_examples_plugin.config.domain.config import ExamplesConfig
from provisioner_features_lib.remote.typer_remote_opts_fakes import TEST_REMOTE_CFG_YAML_TEXT

TEST_DATA_HELLO_WORLD_USERNAME = "test-username"

TEST_DATA_YAML_TEXT = f"""
hello_world:
  username: {TEST_DATA_HELLO_WORLD_USERNAME}
"""

class TestDataExamplesConfig:
    
    @staticmethod
    def create_fake_example_config() -> ExamplesConfig:
        cfg_with_remote = TEST_DATA_YAML_TEXT + "\n" + TEST_REMOTE_CFG_YAML_TEXT
        cfg_dict = yaml.safe_load(cfg_with_remote)
        example_cfg = ExamplesConfig(cfg_dict)
        return example_cfg
