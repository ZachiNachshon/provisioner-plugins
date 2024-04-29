#!/usr/bin/env python3

from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.vcs.domain.config import VersionControlConfig

PLUGIN_NAME = "example_plugin"


class ExamplesConfig(SerializationBase):
    """
    Configuration structure -

    hello_world:
        username: Config User

    remote: {}
    vcs: {}
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "remote" in dict_obj:
            self.remote = RemoteConfig(dict_obj)
        if "vcs" in dict_obj:
            self.vcs = VersionControlConfig(dict_obj)
        if "hello_world" in dict_obj:
            self._parse_hello_world_block(dict_obj["hello_world"])

    def merge(self, other: "ExamplesConfig") -> SerializationBase:
        if hasattr(other, "remote"):
            self.remote.merge(other.remote)
        if hasattr(other, "vcs"):
            self.vcs.merge(other.vcs)
        if hasattr(other, "hello_world"):
            self.hello_world = self.HelloWorldConfig()
            self.hello_world.merge(other.hello_world)

        return self

    def _parse_hello_world_block(self, hello_world_block: dict):
        self.hello_world = self.HelloWorldConfig()
        if "username" in hello_world_block:
            self.hello_world.username = hello_world_block["username"]

    class HelloWorldConfig:

        username: str = None

        def __init__(self, username: str = None) -> None:
            self.username = username

        def merge(self, other: "ExamplesConfig.HelloWorldConfig") -> SerializationBase:
            if hasattr(other, "username"):
                self.username = other.username

            return self

    hello_world: HelloWorldConfig = {}
    remote: RemoteConfig = {}
    vcs: VersionControlConfig = {}
