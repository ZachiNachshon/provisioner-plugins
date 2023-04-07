#!/usr/bin/env python3

import os
import pathlib
from typing import List, NamedTuple, Optional

from loguru import logger
from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.errors.cli_errors import (
    InstallerSourceError,
    InstallerUtilityNotSupported,
    OsArchNotSupported,
    VersionResolverError,
)
from python_core_lib.func.pyfn import Environment, PyFn, PyFnEnvBase, PyFnEvaluator
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible_runner import AnsiblePlaybook
from python_core_lib.shared.collaborators import CoreCollaborators

from provisioner_installers_plugin.installer.domain.installable import Installable
from provisioner_installers_plugin.installer.domain.source import ActiveInstallSource

ProvisionerInstallableBinariesPath = os.path.expanduser("~/.config/provisioner/binaries")
ProvisionerInstallableSymlinksPath = os.path.expanduser("~/.local/bin")

ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_RUN = """
---
- name: Provisioner run command
  hosts: selected_hosts
  gather_facts: no
  environment:
    DRY_RUN: True
    VERBOSE: True
    # SILENT: True

  roles:
    - role: {ansible_playbooks_path}/roles/provisioner
      tags: ['provisioner_run']
"""

# Named Tuples
class Utility_InstallStatus_Tuple(NamedTuple):
    utility: Installable.Utility
    installed: bool


class RunEnv_Utilities_Tuple(NamedTuple):
    run_env: RunEnvironment
    utilities: List[Installable.Utility]


class Utility_Version_Tuple(NamedTuple):
    utility: Installable.Utility
    version: str


class Utility_Version_ReleaseFileName_Tuple(NamedTuple):
    utility: Installable.Utility
    version: str
    release_filename: str


class ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(NamedTuple):
    release_filename: str
    release_download_filepath: str
    utility: Installable.Utility


class UnpackedReleaseFolderPath_Utility_Tuple(NamedTuple):
    unpacked_release_folderpath: str
    utility: Installable.Utility


class RemoteConnector_Utility_Tuple(NamedTuple):
    connector: RemoteMachineConnector
    utility: Installable.Utility


class SSHConnInfo_Utility_Tuple(NamedTuple):
    ssh_conn_info: SSHConnectionInfo
    utility: Installable.Utility


class UtilityInstallerRunnerCmdArgs:
    utilities: List[str]
    remote_opts: CliRemoteOpts
    github_access_token: str

    def __init__(
        self,
        utilities: List[str],
        remote_opts: CliRemoteOpts,
        github_access_token: str = None,
    ) -> None:
        self.utilities = utilities
        self.remote_opts = remote_opts
        self.github_access_token = github_access_token


class InstallerEnv:

    ctx: Context
    collaborators: CoreCollaborators
    args: UtilityInstallerRunnerCmdArgs
    supported_utilities: dict[str, Installable.Utility]

    def __init__(
        self,
        ctx: Context,
        collaborators: CoreCollaborators,
        args: UtilityInstallerRunnerCmdArgs,
        supported_utilities: dict[str, Installable.Utility],
    ) -> None:
        self.ctx = ctx
        self.collaborators = collaborators
        self.args = args
        self.supported_utilities = supported_utilities


class UtilityInstallerCmdRunner(PyFnEnvBase):
    def __init__(self, ctx: Context):
        super().__init__(ctx=ctx)

    def _verify_selected_utilities(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerUtilityNotSupported, None]:
        for name in env.args.utilities:
            if name not in env.supported_utilities:
                return PyFn.fail(
                    error=InstallerUtilityNotSupported(f"{name} is not supported as an installable utility")
                )
        return PyFn.empty()

    def _map_to_utilities_list(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        return PyFn.effect(
            lambda: env.collaborators.summary().append_result(
                attribute_name="utilities",
                call=lambda: [
                    env.supported_utilities[name] for name in env.args.utilities if name in env.supported_utilities
                ],
            )
        )

    def _print_installer_welcome(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", None, List[Installable.Utility]]:
        return PyFn.effect(
            lambda: env.collaborators.printer().print_with_rich_table_fn(
                generate_installer_welcome(utilities, env.args.remote_opts.environment)
            ),
        ).map(lambda _: utilities)

    def _resolve_run_environment(
        self,
        env: InstallerEnv,
        utilities: List[Installable.Utility],
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, RunEnv_Utilities_Tuple]:
        return (
            PyFn.success(RunEnv_Utilities_Tuple(env.args.remote_opts.environment, utilities))
            if env.args.remote_opts.environment
            else PyFn.effect(
                lambda: RunEnv_Utilities_Tuple(
                    run_env=RunEnvironment.from_str(
                        env.collaborators.summary().append_result(
                            attribute_name="run_env",
                            call=lambda: env.collaborators.prompter().prompt_user_single_selection_fn(
                                message="Please choose an environment", options=["Local", "Remote"]
                            ),
                        ),
                    ),
                    utilities=utilities,
                ),
            )
        )

    def _run_installation(
        self, env: InstallerEnv, run_env_utils_tuple: RunEnv_Utilities_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        match run_env_utils_tuple.run_env:
            case RunEnvironment.Local:
                return PyFn.of(run_env_utils_tuple.utilities).flat_map(
                    lambda utilities: self._run_local_utilities_installation(env=env, utilities=utilities)
                )
            case RunEnvironment.Remote:
                # We are guranteed by previous step that the RunEnvironment argument is valid
                return PyFn.of(run_env_utils_tuple.utilities).flat_map(
                    lambda utilities: self._run_remote_installation(env=env, utilities=utilities)
                )

    def _install_utility(
        self, env: InstallerEnv, maybe_utility: Optional[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        if maybe_utility:
            return PyFn.effect(
                lambda: env.collaborators.summary().show_summary_and_prompt_for_enter(
                    f"Installing Utility: {maybe_utility.display_name}"
                )
            ).flat_map(lambda _: self._install_utility_locally(env=env, utility=maybe_utility))
        else:
            return PyFn.empty()

    def _run_local_utilities_installation(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        return PyFn.of(utilities).for_each(
            lambda utility: self._check_if_utility_already_installed(env, utility)
            .flat_map(
                lambda utility_install_tuple: self._notify_if_utility_already_installed(
                    env, utility_install_tuple.utility, utility_install_tuple.installed
                )
            )
            .flat_map(lambda maybe_utility: self._install_utility(env, maybe_utility))
        )

    def _check_if_utility_already_installed(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Utility_InstallStatus_Tuple]:
        return PyFn.effect(
            lambda: Utility_InstallStatus_Tuple(
                utility=utility, installed=env.collaborators.checks().is_tool_exist_fn(utility.binary_name)
            )
        )

    def _notify_if_utility_already_installed(
        self, env: InstallerEnv, utility: Installable.Utility, exists: bool
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Optional[Installable.Utility]]:
        if exists:
            return PyFn.effect(
                lambda: env.collaborators.printer().print_fn(
                    f"Utility already installed locally. name: {utility.binary_name}"
                )
            ).map(lambda _: None)
        else:
            return PyFn.of(utility)

    def _install_utility_locally(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        match utility.active_source:
            case ActiveInstallSource.Script:
                return PyFn.of(utility).flat_map(lambda _: self._install_from_script(env, utility))
            case ActiveInstallSource.GitHub:
                return PyFn.of(utility).flat_map(lambda _: self._install_from_github(env, utility))
            case _:
                return PyFn.fail(
                    error=InstallerSourceError(f"Invalid installation active source. value: {utility.active_source}")
                )

    def _install_from_script(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        # TODO: for custom command lines args we need to support additional install args
        if not utility.sources.script:
            return PyFn.fail(error=InstallerSourceError(f"Missing installation source. name: Script"))
        else:
            return PyFn.effect(
                lambda: env.collaborators.process().run_fn(
                    args=[utility.sources.script.install_cmd], allow_single_shell_command_str=True
                ),
            ).map(lambda _: utility)

    def _try_resolve_utility_version(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", VersionResolverError, Utility_Version_Tuple]:
        if not utility.version:
            if not utility.has_github_active_source():
                return PyFn.fail(
                    error=InstallerSourceError(
                        f"GitHub install source is not active or is missing, cannot resolve utility version. name: {utility.display_name}"
                    )
                )
            else:
                return self._try_resolve_version_from_github(env=env, utility=utility)
        else:
            return PyFn.success(Utility_Version_Tuple(utility, utility.version))

    def _try_resolve_version_from_github(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", VersionResolverError, Utility_Version_Tuple]:
        return PyFn.effect(
            lambda: env.collaborators.github().get_latest_version_fn(
                owner=utility.sources.github.owner, repo=utility.sources.github.repo
            )
        ).if_then_else(
            predicate=lambda version: version is not None and len(version) > 0,
            if_true=lambda version: PyFn.success(Utility_Version_Tuple(utility, version)),
            if_false=lambda _: PyFn.fail(
                VersionResolverError(
                    f"Failed to resolve latest version from GitHub. owner: {utility.sources.github.owner}, repo: {utility.sources.github.repo}"
                )
            ),
        )

    def _try_get_github_release_name_by_os_arch(
        self, env: InstallerEnv, util_ver_tuple: Utility_Version_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", OsArchNotSupported, Utility_Version_ReleaseFileName_Tuple]:
        release_filename = util_ver_tuple.utility.sources.github.resolve_binary_release_name(
            env.ctx.os_arch, util_ver_tuple.version
        )
        if not release_filename:
            return PyFn.fail(
                OsArchNotSupported(
                    f"OS/Arch is not supported. name: {util_ver_tuple[0].display_name}, os_arch: {env.ctx.os_arch.as_pair()}"
                )
            )
        return PyFn.success(
            Utility_Version_ReleaseFileName_Tuple(util_ver_tuple.utility, util_ver_tuple.version, release_filename)
        )

    def _print_before_downloading(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", None, Utility_Version_ReleaseFileName_Tuple]:
        return PyFn.effect(
            lambda: self._print_github_binary_info(env=env, util_ver_name_tuple=util_ver_name_tuple)
        ).map(lambda _: util_ver_name_tuple)

    def _print_github_binary_info(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_Tuple
    ) -> None:
        env.collaborators.printer().new_line_fn().print_fn(
            f"Downloading from GitHub. owner: {util_ver_name_tuple.utility.sources.github.owner}, repo: {util_ver_name_tuple.utility.sources.github.repo}, name: {util_ver_name_tuple.release_filename}, version: {util_ver_name_tuple.version}"
        )

    def _download_binary_by_version(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple]:
        return PyFn.effect(
            lambda: env.collaborators.github().download_release_binary_fn(
                owner=util_ver_name_tuple.utility.sources.github.owner,
                repo=util_ver_name_tuple.utility.sources.github.repo,
                version=util_ver_name_tuple.version,
                binary_name=util_ver_name_tuple.release_filename,
                binary_folder_path=self._genreate_binary_folder_path(
                    util_ver_name_tuple.utility.binary_name, util_ver_name_tuple.version
                ),
            )
        ).flat_map(
            lambda download_filepath: PyFn.of(
                ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(
                    util_ver_name_tuple.release_filename, download_filepath, util_ver_name_tuple.utility
                )
            )
        )

    def _maybe_extract_downloaded_binary(
        self, env: InstallerEnv, releasename_filepath_util_tuple: ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, UnpackedReleaseFolderPath_Utility_Tuple]:
        # Download path is: ~/.config/provisioner/binaries/<binary-cli-name>/<version>/<archive-file>
        return (
            PyFn.of(releasename_filepath_util_tuple.release_download_filepath)
            .if_then_else(
                predicate=lambda release_filepath: env.collaborators.io_utils().is_archive_fn(release_filepath),
                if_true=lambda release_filepath: PyFn.effect(
                    lambda: env.collaborators.io_utils().unpack_archive_fn(release_filepath)
                ),
                if_false=lambda release_filepath: PyFn.of(str(pathlib.Path(release_filepath).parent)),
            )
            .map(
                lambda unpacked_release_folderpath: UnpackedReleaseFolderPath_Utility_Tuple(
                    unpacked_release_folderpath,
                    releasename_filepath_util_tuple.utility,
                )
            )
        )

    def _elevate_permission_and_symlink(
        self, env: InstallerEnv, unpackedreleasefolderpath_utility_tuple: UnpackedReleaseFolderPath_Utility_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, str]:
        return (
            PyFn.of(unpackedreleasefolderpath_utility_tuple)
            .map(
                lambda releasename_folderpath_tuple: env.collaborators.io_utils().set_file_permissions_fn(
                    file_path=f"{releasename_folderpath_tuple.unpacked_release_folderpath}/{releasename_folderpath_tuple.utility.binary_name}"
                )
            )
            .map(
                lambda _: env.collaborators.io_utils().write_symlink_fn(
                    f"{unpackedreleasefolderpath_utility_tuple.unpacked_release_folderpath}/{unpackedreleasefolderpath_utility_tuple.utility.binary_name}",
                    self._genreate_binary_symlink_path(unpackedreleasefolderpath_utility_tuple.utility.binary_name),
                )
            )
        )

    def _install_from_github(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        if not utility.sources.github:
            return PyFn.fail(error=InstallerSourceError(f"Missing installation source. name: GitHub"))
        else:
            # TODO: for command lines we need to support additional install args
            return (
                PyFn.of(utility)
                .flat_map(lambda utility: self._try_resolve_utility_version(env, utility))
                .flat_map(lambda util_ver_tuple: self._try_get_github_release_name_by_os_arch(env, util_ver_tuple))
                .flat_map(lambda util_ver_name_tuple: self._print_before_downloading(env, util_ver_name_tuple))
                .flat_map(lambda util_ver_name_tuple: self._download_binary_by_version(env, util_ver_name_tuple))
                .flat_map(
                    lambda releasename_filepath_util_tuple: self._maybe_extract_downloaded_binary(
                        env, releasename_filepath_util_tuple
                    )
                )
                .flat_map(
                    lambda releasename_folderpath_util_tuple: self._elevate_permission_and_symlink(
                        env, releasename_folderpath_util_tuple
                    )
                )
            )

    @staticmethod
    def run(env: InstallerEnv) -> bool:
        logger.debug("Inside UtilityInstallerCmdRunner run()")
        eval = PyFnEvaluator[UtilityInstallerCmdRunner, Exception].new(UtilityInstallerCmdRunner(ctx=env.ctx))
        chain = eval << Environment[UtilityInstallerCmdRunner]()
        run_env_utils_tuple = eval << (
            chain._verify_selected_utilities(env)
            .flat_map(lambda _: chain._map_to_utilities_list(env))
            .flat_map(lambda utilities: chain._print_installer_welcome(env, utilities))
            .flat_map(lambda utilities: chain._resolve_run_environment(env, utilities))
        )
        result = eval << chain._run_installation(env, run_env_utils_tuple)
        return result is not None

    def _genreate_binary_folder_path(self, binary_name: str, version: str) -> str:
        return f"{ProvisionerInstallableBinariesPath}/{binary_name}/{version}"

    def _genreate_binary_symlink_path(self, binary_name: str) -> str:
        return f"{ProvisionerInstallableSymlinksPath}/{binary_name}"

    def _collect_ssh_connection_info(
        self, env: InstallerEnv, connector: RemoteMachineConnector
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, SSHConnectionInfo]:
        return PyFn.effect(
            lambda: env.collaborators.summary().append_result(
                attribute_name="ssh_conn_info",
                call=lambda: connector.collect_ssh_connection_info(
                    env.ctx, env.args.remote_opts, force_single_conn_info=True
                ),
            )
        )

    def _install_on_remote_machine(
        self, env: InstallerEnv, sshconninfo_utility_info: SSHConnInfo_Utility_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, str]:
        return PyFn.effect(
            lambda: env.collaborators.printer().progress_indicator.status.long_running_process_fn(
                call=lambda: env.collaborators.ansible_runner().run_fn(
                    selected_hosts=sshconninfo_utility_info.ssh_conn_info.ansible_hosts,
                    playbook=AnsiblePlaybook(name="provisioner_run", content=ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_RUN),
                    ansible_vars=[
                        f"provisioner_command='provisioner -y install cli --environment=Local {sshconninfo_utility_info.utility.binary_name}'"
                    ],
                    ansible_tags=["provisioner_run"],
                ),
                desc_run="Running Ansible playbook (Provisioner Run)",
                desc_end="Ansible playbook finished (Provisioner Run).",
            )
        )

    def _run_remote_installation(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        ssh_conn_info_chain = PyFn.of(RemoteMachineConnector(collaborators=env.collaborators)).flat_map(
            lambda connector: self._collect_ssh_connection_info(env, connector)
        )
        return PyFn.of(utilities).for_each(
            lambda utility: ssh_conn_info_chain.flat_map(
                lambda ssh_conn_info: PyFn.of(SSHConnInfo_Utility_Tuple(ssh_conn_info, utility))
            )
            .flat_map(lambda sshconninfo_utility_tuple: self._install_on_remote_machine(env, sshconninfo_utility_tuple))
            .map(lambda output: env.collaborators.printer().new_line_fn().print_fn(output))
        )


@staticmethod
def generate_installer_welcome(
    utilities_to_install: List[Installable.Utility], environment: Optional[RunEnvironment]
) -> str:
    selected_utils_names = ""
    if utilities_to_install:
        for utility in utilities_to_install:
            selected_utils_names += f"  - {utility.display_name}\n"

    env_indicator = ""
    if not environment:
        env_indicator = """[yellow]Environment was not set, you will be prompted to select a local/remote environment.[/yellow]

When opting-in for the remote option you will be prompted for additional arguments."""
    else:
        env_indicator = f"Running on [yellow]{environment}[/yellow] environment."

    return f"""About to install the following CLI utilities:
{selected_utils_names}
{env_indicator}"""
