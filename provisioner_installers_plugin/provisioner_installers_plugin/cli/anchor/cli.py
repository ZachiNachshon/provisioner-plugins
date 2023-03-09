#!/usr/bin/env python3

from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)


def anchor() -> None:
    """
    Create Dynamic CLI's as your GitOps Marketplace
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="anchor",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(utilities=["anchor"], remote_opts=CliRemoteOpts.maybe_get()),
        ),
    )
