#!/usr/bin/env python3


from typing import Any
from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from python_core_lib.domain.serialize import SerializationBase


class FakeConnfigResolver(ConfigResolver):

    # Static variable
    config: SerializationBase = None

    @staticmethod
    def load(config: SerializationBase) -> None:
        TyperRemoteOpts.load(config.remote)
        TyperAnchorOpts.load(config.anchor)
        
    def get_config() -> Any:
        return FakeConnfigResolver.config
