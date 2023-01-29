#!/usr/bin/env python3

from provisioner_examples_plugin.domain.config import DummyConfig

class TestDataExamplesConfig:
    TEST_DATA_HELLO_WORLD_USERNAME= "test-username"

    @staticmethod
    def create_fake_dummy_config() -> DummyConfig:
        return DummyConfig(
            hello_world=DummyConfig.HelloWorldConfig(
                username=TestDataExamplesConfig.TEST_DATA_HELLO_WORLD_USERNAME,
            )
        )
