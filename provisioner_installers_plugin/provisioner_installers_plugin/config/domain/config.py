#!/usr/bin/env python3

from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.remote.domain.config import RemoteConfig

PLUGIN_NAME = "installers-plugin"


class InstallersConfig(SerializationBase):
    """
    Configuration structure -
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "remote" in dict_obj:
            self.remote = RemoteConfig(dict_obj)

    def merge(self, other: "InstallersConfig") -> SerializationBase:
        return self

    remote: RemoteConfig = None
