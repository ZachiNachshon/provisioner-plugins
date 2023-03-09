#!/usr/bin/env python3

from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)


def helm() -> None:
    """
    Package Manager for Kubernetes
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="helm",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(utilities=["helm"], remote_opts=CliRemoteOpts.maybe_get()),
        ),
    )
