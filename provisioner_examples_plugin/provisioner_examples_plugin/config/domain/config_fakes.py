#!/usr/bin/env python3

from provisioner_examples_plugin.config.domain.config import ExamplesConfig


class TestDataExamplesConfig:
    TEST_DATA_HELLO_WORLD_USERNAME = "test-username"

    @staticmethod
    def create_fake_dummy_config() -> ExamplesConfig:
        return ExamplesConfig(
            hello_world=ExamplesConfig.HelloWorldConfig(
                username=TestDataExamplesConfig.TEST_DATA_HELLO_WORLD_USERNAME,
            )
        )
