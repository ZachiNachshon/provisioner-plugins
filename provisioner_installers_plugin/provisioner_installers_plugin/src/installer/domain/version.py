#!/usr/bin/env python3

import typing

from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs


class NameVersionArgsTuple(typing.NamedTuple):
    name: str = None
    version: str = None
    maybe_args: DynamicArgs = None


def try_extract_name_version_tuple(command_arg: str) -> NameVersionArgsTuple:
    """Extract name and version from the target argument"""
    version = "latest"
    if "@" in command_arg:
        name, version = command_arg.split("@", 1)
    else:
        name = command_arg
        version = "latest"

    return NameVersionArgsTuple(name=name, version=version, maybe_args=DynamicArgs({}))
