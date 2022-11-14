#!/usr/bin/env python3

import os
import pathlib

from loguru import logger
from python_core_lib.config.config_reader import ConfigReader
from python_core_lib.infra.context import Context
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.yaml_util import YamlUtil

from provisioner.config.domain.config import ProvisionerConfig
from provisioner.config.typer_remote_opts import TyperRemoteOpts

ENV_VAR_ENABLE_CONFIG_DEBUG = "PROVISIONER_PRE_RUN_DEBUG"
CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/config.yaml"


class ConfigResolver:

    config_reader: ConfigReader
    _internal_path: str
    _user_path: str

    # Static variable
    config: ProvisionerConfig = None

    def __init__(self, ctx: Context, internal_path: str, user_path: str) -> None:
        self._internal_path = internal_path
        self._user_path = user_path
        io = IOUtils.create(ctx)
        yaml_util = YamlUtil.create(ctx, io)
        self.config_reader = ConfigReader.create(yaml_util)

    @staticmethod
    def _create(ctx: Context, internal_path: str, user_path: str) -> "ConfigResolver":
        logger.debug("Creating typer cli config resolver...")
        resolver = ConfigResolver(ctx, internal_path, user_path)
        return resolver

    @staticmethod
    def resolve(internal_path: str, user_path: str) -> None:
        """
        Logger is being set-up after Typer is initialized and we have the --dry-run, --verbose
        flags are avaialble.
        I've added pre Typer run env var to contorl if configuraiton load debug logs
        should be visible.
        """
        debug_config = os.getenv(key=ENV_VAR_ENABLE_CONFIG_DEBUG, default=False)
        if debug_config != "True":
            logger.remove()
        logger.debug("Loading configuration...")
        empty_ctx = Context.create()
        resolver = ConfigResolver._create(empty_ctx, internal_path, user_path)
        ConfigResolver.config = resolver.config_reader.read_config_fn(
            internal_path=internal_path, class_name=ProvisionerConfig, user_path=user_path
        )

    def get_config() -> ProvisionerConfig:
        if not ConfigResolver.config:
            ConfigResolver.resolve(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH)
            TyperRemoteOpts.load(ConfigResolver.config)
        return ConfigResolver.config
