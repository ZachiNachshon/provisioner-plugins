#!/usr/bin/env python3

from typing import List, Optional
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts

import typer
from loguru import logger
from python_core_lib.cli.typer_callbacks import exclusivity_callback
from python_core_lib.runner.ansible.ansible import HostIpPair

from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment


class FakeTyperRemoteOpts:

    # Static variable
    remote_config: RemoteConfig

    @staticmethod
    def create(remote_config: RemoteConfig) -> TyperRemoteOpts:
        opts = TyperRemoteOpts()
        opts.remote_config = remote_config
        return opts
