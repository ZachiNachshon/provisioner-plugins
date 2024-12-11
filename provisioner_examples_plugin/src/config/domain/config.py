#!/usr/bin/env python3

from provisioner_shared.components.runtime.domain.serialize import SerializationBase

from provisioner_shared.components.remote.domain.config import RemoteConfig
from provisioner_shared.components.vcs.domain.config import VersionControlConfig

PLUGIN_NAME = "example_plugin"

"""
    Configuration structure -

    hello_world:
        username: Config User

    remote: {}
    vcs: {}
    """


class HelloWorldConfig(SerializationBase):
    username: str = ""

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "HelloWorldConfig") -> SerializationBase:
        if hasattr(other, "username") and len(other.username) > 0:
            self.username = other.username
        return self

    def _try_parse_config(self, dict_obj: dict) -> None:
        if "username" in dict_obj:
            self.username = dict_obj["username"]


class ExamplesConfig(SerializationBase):
    hello_world: HelloWorldConfig = HelloWorldConfig({})
    remote: RemoteConfig = RemoteConfig({})
    vcs: VersionControlConfig = VersionControlConfig({})

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "ExamplesConfig") -> SerializationBase:
        if hasattr(other, "remote"):
            self.remote = self.remote if self.remote is not None else RemoteConfig()
            self.remote.merge(other.remote)
        if hasattr(other, "vcs"):
            self.vcs = self.vcs if self.vcs is not None else VersionControlConfig()
            self.vcs.merge(other.vcs)
        if hasattr(other, "hello_world"):
            self.hello_world = self.hello_world if self.hello_world is not None else HelloWorldConfig()
            self.hello_world.merge(other.hello_world)
        return self

    def _try_parse_config(self, dict_obj: dict):
        if "remote" in dict_obj:
            self.remote = RemoteConfig(dict_obj["remote"])
        if "vcs" in dict_obj:
            self.vcs = VersionControlConfig(dict_obj["vcs"])
        if "hello_world" in dict_obj:
            self.hello_world = HelloWorldConfig(dict_obj["hello_world"])
