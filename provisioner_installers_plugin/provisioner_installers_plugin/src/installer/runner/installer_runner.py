#!/usr/bin/env python3

import os
import pathlib
from typing import List, NamedTuple, Optional

from loguru import logger
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import ActiveInstallSource

from provisioner_shared.components.remote.domain.config import RunEnvironment
from provisioner_shared.components.remote.remote_connector import RemoteMachineConnector, SSHConnectionInfo
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.version import NameVersionTuple
from provisioner_shared.components.runtime.errors.cli_errors import (
    InstallerSourceError,
    InstallerUtilityNotSupported,
    OsArchNotSupported,
    VersionResolverError,
)
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import (
    AnsibleHost,
    AnsiblePlaybook,
    AnsibleRunnerLocal,
)
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.framework.functional.pyfn import Environment, PyFn, PyFnEnvBase, PyFnEvaluator

ProvisionerInstallableBinariesPath = os.path.expanduser("~/.config/provisioner/binaries")
ProvisionerInstallableSymlinksPath = os.path.expanduser("~/.local/bin")

ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER = """
---
- name: Provisioner run command
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/provisioner
      tags: ['provisioner_wrapper']
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

    def __init__(
        self,
        utilities: List[NameVersionTuple],
        remote_opts: RemoteOpts,
        sub_command_name: InstallerSubCommandName,
        git_access_token: str = None,
        dynamic_args: Optional[DynamicArgs] = None,
    ) -> None:
        self.utilities = utilities
        self.remote_opts = remote_opts
        self.sub_command_name = sub_command_name
        self.dynamic_args = dynamic_args
        self.git_access_token = git_access_token


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
        for name_ver_tuple in env.args.utilities:
            if name_ver_tuple.name not in env.supported_utilities:
                return PyFn.fail(
                    error=InstallerUtilityNotSupported(
                        f"{name_ver_tuple.name} is not supported as an installable utility"
                    )
                )
        return PyFn.empty()

    def _maybe_set_custom_versions(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerUtilityNotSupported, None]:
        for name_ver_tuple in env.args.utilities:
            if name_ver_tuple.name in env.supported_utilities and name_ver_tuple.version:
                env.supported_utilities[name_ver_tuple.name].version = name_ver_tuple.version
        return PyFn.empty()

    def _map_to_utilities_list(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        return PyFn.effect(
            lambda: [
                env.supported_utilities[name_ver_tuple.name]
                for name_ver_tuple in env.args.utilities
                if name_ver_tuple.name in env.supported_utilities
            ]
        )

    def _create_utils_summary(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        return PyFn.effect(
            lambda: [
                env.collaborators.summary().append(
                    utility.display_name, utility.as_summary_object(env.ctx.is_verbose())
                )
                for utility in utilities
            ]
        ).map(lambda _: utilities)

    def _print_installer_welcome(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", None, List[Installable.Utility]]:
        return PyFn.effect(
            lambda: env.collaborators.printer().print_with_rich_table_fn(
                generate_installer_welcome(utilities, env.args.remote_opts.get_environment())
            ),
        ).map(lambda _: utilities)

    def _resolve_run_environment(
        self,
        env: InstallerEnv,
        utilities: List[Installable.Utility],
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, RunEnv_Utilities_Tuple]:
        return (
            PyFn.success(RunEnv_Utilities_Tuple(env.args.remote_opts.get_environment(), utilities))
            if env.args.remote_opts.get_environment() is not None
            else PyFn.effect(
                lambda: RunEnv_Utilities_Tuple(
                    run_env=RunEnvironment.from_str(
                        env.collaborators.summary().append_result(
                            attribute_name="run_env",
                            call=lambda: env.collaborators.prompter().prompt_user_single_selection_fn(
                                message="Please choose an environment", options=[v.value for v in RunEnvironment]
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

    def _print_pre_install_summary(
        self, env: InstallerEnv, maybe_utility: Optional[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        if maybe_utility:
            return PyFn.effect(
                lambda: env.collaborators.summary().show_summary_and_prompt_for_enter(
                    f"Installing Utility: {maybe_utility.display_name}"
                )
            ).map(lambda _: maybe_utility)
        else:
            return PyFn.empty()

    def _print_post_install_summary(
        self, env: InstallerEnv, maybe_utility: Optional[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        if maybe_utility:
            return PyFn.effect(
                lambda: env.collaborators.printer().print_with_rich_table_fn(
                    f"""Successfully installed utility:
  name:    {maybe_utility.display_name}
  version: {maybe_utility.version}
  binary:  {self._genreate_binary_symlink_path(maybe_utility.binary_name)}"""
                )
            ).map(lambda _: maybe_utility)
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
            .flat_map(lambda maybe_utility: self._print_pre_install_summary(env, maybe_utility))
            .if_then_else(
                predicate=lambda maybe_utility: maybe_utility is not None,
                if_true=lambda maybe_utility: self._install_utility_locally(env, maybe_utility).flat_map(
                    lambda maybe_utility: self._print_post_install_summary(env, maybe_utility)
                ),
                if_false=lambda _: PyFn.empty(),
            )
        )

    def _check_if_utility_already_installed(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Utility_InstallStatus_Tuple]:
        return PyFn.effect(
            lambda: Utility_InstallStatus_Tuple(
                utility=utility, installed=env.collaborators.checks().is_tool_exist_fn(utility.binary_name)
            )
        )
        # return PyFn.effect(
        #     lambda: Utility_InstallStatus_Tuple(
        #         utility=utility, installed=False
        #     )
        # )

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

    def _get_ssh_conn_info_localhost(self) -> SSHConnectionInfo:
        return SSHConnectionInfo(
            ansible_hosts=[
                AnsibleHost(
                    host="localhost",
                    ip_address="ansible_connection=local",
                    username="localhost",
                )
            ]
        )

    def _install_utility_locally(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        match utility.active_source:
            case ActiveInstallSource.Callback:
                return PyFn.of(utility).flat_map(lambda _: self._install_from_callback(env, utility))
            case ActiveInstallSource.Script:
                return PyFn.of(utility).flat_map(lambda _: self._install_from_script(env, utility))
            case ActiveInstallSource.Ansible:
                return (
                    PyFn.of(utility)
                    .flat_map(lambda _: self._install_locally_from_ansible_playbook(env, utility))
                    .flat_map(lambda output: self._print_ansible_response(env, output))
                    .map(lambda _: utility)
                )
            case ActiveInstallSource.GitHub:
                return PyFn.of(utility).flat_map(lambda _: self._install_from_github(env, utility))
            case _:
                return PyFn.fail(
                    error=InstallerSourceError(f"Invalid installation active source. value: {utility.active_source}")
                )

    def _print_ansible_response(self, env: InstallerEnv, output: str):
        return PyFn.effect(lambda: env.collaborators.printer().print_fn(output))

    def _install_locally_from_ansible_playbook(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, str]:
        if not utility.has_ansible_active_source():
            return PyFn.fail(error=InstallerSourceError("Missing installation source. name: Ansible"))
        else:
            return PyFn.effect(
                lambda: env.collaborators.progress_indicator()
                .get_status()
                .long_running_process_fn(
                    call=lambda: env.collaborators.ansible_runner().run_fn(
                        selected_hosts=self._get_ssh_conn_info_localhost().ansible_hosts,
                        playbook=AnsiblePlaybook.copy_and_add_context(
                            copy_from=utility.source.ansible.playbook,
                            remote_context=env.args.remote_opts.get_remote_context(),
                        ),
                        ansible_vars=env.args.dynamic_args.as_ansible_vars()
                        + utility.source.ansible.ansible_vars
                        + [f"git_access_token={env.args.git_access_token}"],
                        ansible_tags=utility.source.ansible.ansible_tags,
                    ),
                    desc_run=f"Running Ansible playbook locally ({utility.source.ansible.playbook.get_name()})).",
                    desc_end=f"Ansible playbook finished locally ({utility.source.ansible.playbook.get_name()})).",
                )
            )

    def _install_from_script(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        # TODO: for custom command lines args we need to support additional install args
        if not utility.has_script_active_source():
            return PyFn.fail(error=InstallerSourceError("Missing installation source. name: Script"))
        else:
            return PyFn.effect(
                lambda: env.collaborators.process().run_fn(
                    args=[utility.source.script.install_script], allow_single_shell_command_str=True
                ),
            ).map(lambda _: utility)

    def _install_from_callback(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        if not utility.has_callback_active_source():
            return PyFn.fail(error=InstallerSourceError("Missing installation source. name: Callback"))
        else:
            return PyFn.effect(
                lambda: utility.source.callback.install_fn(utility.version, env.collaborators),
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
                owner=utility.source.github.owner, repo=utility.source.github.repo
            )
        ).if_then_else(
            predicate=lambda version: version is not None and len(version) > 0,
            if_true=lambda version: PyFn.success(Utility_Version_Tuple(utility, version)),
            if_false=lambda _: PyFn.fail(
                VersionResolverError(
                    f"Failed to resolve latest version from GitHub. owner: {utility.source.github.owner}, repo: {utility.source.github.repo}"
                )
            ),
        )

    def _try_get_github_release_name_by_os_arch(
        self, env: InstallerEnv, util_ver_tuple: Utility_Version_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", OsArchNotSupported, Utility_Version_ReleaseFileName_Tuple]:
        release_filename = util_ver_tuple.utility.source.github.resolve_binary_release_name(
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
            f"Downloading from GitHub. owner: {util_ver_name_tuple.utility.source.github.owner}, repo: {util_ver_name_tuple.utility.source.github.repo}, name: {util_ver_name_tuple.release_filename}, version: {util_ver_name_tuple.version}"
        )

    def _download_binary_by_version(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple]:
        return PyFn.effect(
            lambda: env.collaborators.github().download_release_binary_fn(
                owner=util_ver_name_tuple.utility.source.github.owner,
                repo=util_ver_name_tuple.utility.source.github.repo,
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
                ).flat_map(
                    lambda unpacked_release_folderpath: PyFn.of(
                        env.collaborators.printer().print_fn(
                            f"Unpacked Utility: {releasename_filepath_util_tuple.utility.display_name}, archive: {releasename_filepath_util_tuple.release_filename}, path: {unpacked_release_folderpath}"
                        )
                    ).map(lambda _: unpacked_release_folderpath)
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
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
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
        if not utility.source.github:
            return PyFn.fail(error=InstallerSourceError("Missing installation source. name: GitHub"))
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
                .map(lambda _: utility)
            )

    @staticmethod
    def run(env: InstallerEnv) -> bool:
        logger.debug("Inside UtilityInstallerCmdRunner run()")
        eval: PyFnEvaluator = PyFnEvaluator[UtilityInstallerCmdRunner, Exception].new(
            UtilityInstallerCmdRunner(ctx=env.ctx)
        )
        chain: UtilityInstallerCmdRunner = eval << Environment[UtilityInstallerCmdRunner]()
        run_env_utils_tuple = eval << (
            chain._verify_selected_utilities(env)
            .flat_map(lambda _: chain._maybe_set_custom_versions(env))
            .flat_map(lambda _: chain._map_to_utilities_list(env))
            .flat_map(lambda utilities: chain._create_utils_summary(env, utilities))
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
            lambda: env.collaborators.progress_indicator()
            .get_status()
            .long_running_process_fn(
                call=lambda: self._run_ansible(
                    env=env,
                    runner=env.collaborators.ansible_runner(),
                    remote_ctx=env.args.remote_opts.get_remote_context(),
                    ssh_conn_info=sshconninfo_utility_info.ssh_conn_info,
                    sub_command_name=env.args.sub_command_name,
                    utility=sshconninfo_utility_info.utility,
                    git_access_token=env.args.git_access_token,
                ),
                desc_run="Running Ansible playbook remotely (Provisioner Wrapper)",
                desc_end="Ansible playbook finished remotely (Provisioner Wrapper).",
            ),
        )

    def _run_ansible(
        self,
        env: InstallerEnv,
        runner: AnsibleRunnerLocal,
        remote_ctx: RemoteContext,
        ssh_conn_info: SSHConnectionInfo,
        sub_command_name: InstallerSubCommandName,
        utility: Installable.Utility,
        git_access_token: str,
    ) -> str:

        install_method = "install_method='pip'"
        ansible_tags = ["provisioner_wrapper"]
        maybe_test_args = []
        if self._test_only_is_testing_mode_enabled(env):
            print("\n=== Running Ansible Provisioner Wrapper in testing mode ===\n")
            # We must have the tests reference in here since we are controlling the provisioner_wrapper execution by:
            #   - Running it as non-test code as a direct provisioner CLI install command
            #   - Running it as test code remotely via provisioner_wrapper Ansible script
            # This test indicator allows the provisioner runtime / shared / installer-plugin to be bundled and run from sources within the docker container.
            # Otherwise, the container will download from pip those components and we won't be able to run the tests on local changes before publishing.
            # Copying the entire project / mount as a volume to the container was tested, added complexity and don't work as expected due to the time it takes to copy
            # and the fact that we'll have to re-create the virtual environmnet within the containers.
            temp_folder_path = self._test_only_prepare_test_artifacts(env)
            install_method = "install_method='testing'"
            ansible_tags.append("provisioner_testing")
            maybe_test_args.append(f"provisioner_e2e_tests_archives_host_path='{temp_folder_path}'")
            maybe_test_args.append("ansible_python_interpreter='/usr/local/bin/python3'")

        utility_maybe_ver = f"{utility.display_name}@{utility.version}" if utility.version else utility.display_name
        prov_run_cmd = f"install --environment Local {sub_command_name} {utility_maybe_ver} -y {'-v' if remote_ctx.is_verbose() else ''}"
        return runner.run_fn(
            selected_hosts=ssh_conn_info.ansible_hosts,
            playbook=AnsiblePlaybook(
                name="provisioner_wrapper",
                content=ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER,
                remote_context=remote_ctx,
            ),
            ansible_vars=[
                f"provisioner_command='{prov_run_cmd}'",
                # "required_plugins=['provisioner_installers_plugin:0.1.0']",
                "required_plugins=['provisioner_installers_plugin']",
                install_method,
                f"git_access_token={git_access_token}",
            ]
            + maybe_test_args,
            ansible_tags=ansible_tags,
        )

    def is_hosts_found(self, ssh_conn_info: SSHConnectionInfo) -> bool:
        return ssh_conn_info.ansible_hosts is not None and len(ssh_conn_info.ansible_hosts) > 0

    def _run_remote_installation(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        return (
            PyFn.of(RemoteMachineConnector(collaborators=env.collaborators))
            .flat_map(lambda connector: self._collect_ssh_connection_info(env, connector))
            .if_then_else(
                predicate=lambda ssh_conn_info: self.is_hosts_found(ssh_conn_info),
                if_false=lambda _: PyFn.empty(),
                if_true=lambda ssh_conn_info: PyFn.of(utilities).for_each(
                    lambda utility: PyFn.of(SSHConnInfo_Utility_Tuple(ssh_conn_info, utility))
                    .flat_map(
                        lambda sshconninfo_utility_tuple: self._print_pre_install_summary(
                            env, sshconninfo_utility_tuple.utility
                        ).map(lambda _: sshconninfo_utility_tuple)
                    )
                    .flat_map(
                        lambda sshconninfo_utility_tuple: self._install_on_remote_machine(
                            env, sshconninfo_utility_tuple
                        )
                    )
                    .map(lambda output: env.collaborators.printer().new_line_fn().print_fn(output)),
                ),
            )
        )

    def _test_only_is_testing_mode_enabled(self, env: InstallerEnv) -> bool:
        return env.collaborators.checks().is_env_var_equals_fn("PROVISIONER_TESTING_MODE_ENABLED", "true")

    def _test_only_prepare_test_artifacts(self, env: InstallerEnv) -> str:
        project_git_root = env.collaborators.io_utils().find_git_repo_root_abs_path_fn(clazz=UtilityInstallerCmdRunner)
        sdist_output_path = f"{project_git_root}/tests-outputs/installers-plugin/dist"
        env.collaborators.package_loader().build_sdists_fn(
            [
                f"{project_git_root}/provisioner",
                f"{project_git_root}/provisioner_shared",
                f"{project_git_root}/plugins/provisioner_installers_plugin",
            ],
            sdist_output_path,
        )
        return sdist_output_path


@staticmethod
def generate_installer_welcome(
    utilities_to_install: List[Installable.Utility], environment: Optional[RunEnvironment]
) -> str:
    selected_utils_names = ""
    if utilities_to_install:
        for utility in utilities_to_install:
            selected_utils_names += f"  - {utility.display_name} ({utility.version})\n"

    env_indicator = ""
    if not environment:
        env_indicator = """[yellow]Environment was not set, you will be prompted to select a local/remote environment.[/yellow]

When opting-in for the remote option you will be prompted for additional arguments."""
    else:
        env_indicator = f"Running on [yellow]{environment}[/yellow] environment."

    return f"""About to install the following CLI utilities:
{selected_utils_names}
{env_indicator}"""
