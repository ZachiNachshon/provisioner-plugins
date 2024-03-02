#!/usr/bin/env python3

from provisioner.config.domain.config import ProvisionerConfig
from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.remote.domain.config import RemoteConfig

PLUGIN_NAME = "example-plugin"
PLUGIN_EXAMPLES_CONFIG_MODULE_NAME = "provisioner_examples_plugin.domain.config"

class ExamplesConfig(SerializationBase):
    """
    Configuration structure -

    dummy:
      hello_world:
        username: Config User    

    remote: {}
    anchor: {}
    """
    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        examples_data = dict_obj["examples"]
        # if "remote" in examples_data:
        #     self._parse_remote_block(examples_data["remote"])
        # if "anchor" in examples_data:
        #     self._parse_anchor_block(examples_data["anchor"])
        if "hello_world" in examples_data:
            self._parse_dummy_block(examples_data["dummy"])

    def merge(self, other: ProvisionerConfig) -> SerializationBase:
        if other.dummmy.hello_world.username:
            self.dummmy.hello_world.username = other.dummmy.hello_world.username

        return self
        
    def _parse_dummy_block(self, dummy_block: dict):
        if "hello_world" in dummy_block:
            hello_world_block = dummy_block["hello_world"]
            if "username" in hello_world_block:
                self.dummmy.hello_world.username = hello_world_block["username"]

    class HelloWorldConfig:

        username: str = None

        def __init__(self, username: str = None) -> None:
            self.username = username

    hello_world: HelloWorldConfig = None
    remote: RemoteConfig = None
    anchor: AnchorConfig = None