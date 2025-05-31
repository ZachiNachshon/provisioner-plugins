#!/usr/bin/env python3

import os
import pathlib
from typing import List, NamedTuple, Optional

from loguru import logger
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import ActiveInstallSource
from provisioner_installers_plugin.src.installer.domain.version import NameVersionArgsTuple

from provisioner_shared.components.remote.ansible.remote_provisioner_runner import (
    RemoteProvisionerRunner,
    RemoteProvisionerRunnerArgs,
)
from provisioner_shared.components.remote.domain.config import RunEnvironment
from provisioner_shared.components.remote.remote_connector import RemoteMachineConnector, SSHConnectionInfo
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.errors.cli_errors import (
    InstallerSourceError,
    InstallerUtilityNotSupported,
    OsArchNotSupported,
    StepEvaluationFailure,
    VersionResolverError,
)
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import (
    AnsibleHost,
    AnsiblePlaybook,
)
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.os import OsArch
from provisioner_shared.framework.functional.pyfn import Environment, PyFn, PyFnEnvBase, PyFnEvaluator

ProvisionerInstallableBinariesPath = os.path.expanduser("~/.config/provisioner/binaries")
ProvisionerInstallableSymlinksPath = os.path.expanduser("~/.local/bin")


class Utility_InstallStatus_Tuple(NamedTuple):
    utility: Installable.Utility
    installed: bool


class RunEnv_Utilities_Tuple(NamedTuple):
    run_env: RunEnvironment
    utilities: List[Installable.Utility]


class Utility_Version_Tuple(NamedTuple):
    utility: Installable.Utility
    version: str


class Utility_Version_ReleaseFileName_OsArch_Tuple(NamedTuple):
    utility: Installable.Utility
    version: str
    release_filename: str
    os_arch_adjusted: OsArch


class ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple(NamedTuple):
    release_filename: str
    release_download_filepath: str
    utility: Installable.Utility
    os_arch_adjusted: OsArch


class UnpackedReleaseFolderPath_Utility_OsArch_Tuple(NamedTuple):
    unpacked_release_folderpath: str
    utility: Installable.Utility
    os_arch_adjusted: OsArch


class RemoteConnector_Utility_Tuple(NamedTuple):
    connector: RemoteMachineConnector
    utility: Installable.Utility


class SSHConnInfo_Utility_Tuple(NamedTuple):
    ssh_conn_info: SSHConnectionInfo
    utility: Installable.Utility


class UtilityInstallerRunnerCmdArgs:

    def __init__(
        self,
        utilities: List[NameVersionArgsTuple],
        remote_opts: RemoteOpts,
        sub_command_name: InstallerSubCommandName,
        git_access_token: str = None,
        force: bool = False,
        uninstall: bool = False,
    ) -> None:
        self.utilities = utilities
        self.remote_opts = remote_opts
        self.sub_command_name = sub_command_name
        self.git_access_token = git_access_token
        self.force = force
        self.uninstall = uninstall


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
            .flat_map(lambda _: chain._map_to_utilities_list_with_dynamic_args(env))
            .flat_map(lambda utilities: chain._create_utils_summary(env, utilities))
            .flat_map(lambda utilities: chain._print_installer_welcome(env, utilities))
            .flat_map(lambda utilities: chain._resolve_run_environment(env, utilities))
        )
        result = eval << chain._run_installation(env, run_env_utils_tuple)
        return result is not None

    def _verify_selected_utilities(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerUtilityNotSupported, None]:
        if env.args.utilities is None:
            return PyFn.fail(error=Exception("Utilities list is None, cannot proceed"))

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

    def _map_to_utilities_list_with_dynamic_args(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        logger.debug(f"Mapping utilities with dynamic args, utils to install: {env.args.utilities}")
        result: List[Installable.Utility] = []
        for name_ver_tuple in env.args.utilities:
            if name_ver_tuple.name in env.supported_utilities:
                # Create a copy of the utility
                utility = Installable.Utility(**env.supported_utilities[name_ver_tuple.name].__dict__)

                # Add dynamic args from the name_ver_tuple
                utility.maybe_args = name_ver_tuple.maybe_args

                # Ensure uninstall flag is propagated to each utility's dynamic args
                if env.args.uninstall:
                    if utility.maybe_args is None:
                        utility.maybe_args = DynamicArgs({"uninstall": True})
                    else:
                        args_dict = utility.maybe_args.as_dict()
                        args_dict["uninstall"] = True
                        utility.maybe_args = DynamicArgs(args_dict)

                result.append(utility)

        logger.debug(f"Mapped utilities with dynamic args: {[u.display_name for u in result]}")
        return PyFn.effect(lambda: result)

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
        # Determine if this is an uninstall operation
        is_uninstall = self._determine_uninstall_mode(env, utilities)

        return PyFn.effect(
            lambda: env.collaborators.printer().print_with_rich_table_fn(
                generate_installer_welcome(utilities, env.args.remote_opts.get_environment(), is_uninstall)
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
                logger.debug(f"Running local installation for {len(run_env_utils_tuple.utilities)} utilities")
                return self._run_local_utilities_installation(env, run_env_utils_tuple.utilities)
            case RunEnvironment.Remote:
                logger.debug(f"Running remote installation for {len(run_env_utils_tuple.utilities)} utilities")
                return self._run_remote_installation(env, run_env_utils_tuple.utilities)
            case _:
                logger.error(f"Unsupported run environment: {run_env_utils_tuple.run_env}")
                return PyFn.fail(
                    error=StepEvaluationFailure(f"Unsupported run environment: {run_env_utils_tuple.run_env}")
                )

    def _print_pre_install_summary(
        self, env: InstallerEnv, maybe_utility: Optional[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        if maybe_utility is None:
            return PyFn.empty()

        return PyFn.effect(
            lambda: env.collaborators.summary().show_summary_and_prompt_for_enter(
                f"Installing Utility: {maybe_utility.display_name}"
            )
        ).map(lambda _: maybe_utility)

    def _print_post_install_summary(
        self, env: InstallerEnv, maybe_utility: Optional[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        if maybe_utility is None:
            return PyFn.empty()

        return PyFn.effect(
            lambda: env.collaborators.printer().print_with_rich_table_fn(
                f"""Successfully installed utility:
  name:    {maybe_utility.display_name}
  version: {maybe_utility.version}
  binary:  {self._genreate_binary_symlink_path(maybe_utility.binary_name)}"""
            )
        ).map(lambda _: maybe_utility)

    def _run_local_utilities_installation(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        """Handle local installation or uninstallation of utilities based on arguments."""
        # Early return if no utilities
        if not utilities:
            logger.warning("No utilities to process locally")
            return PyFn.success([])

        # Determine if we're in uninstall mode
        is_uninstall = self._determine_uninstall_mode(env, utilities)

        # Execute appropriate flow
        if is_uninstall:
            logger.debug("Starting uninstall flow")
            return self._execute_uninstall_flow(env, utilities)
        else:
            logger.debug("Starting install flow")
            return self._execute_install_flow(env, utilities)

    def _determine_uninstall_mode(self, env: InstallerEnv, utilities: List[Installable.Utility]) -> bool:
        """Determine if we're in uninstall mode based on args and utility settings."""
        # Check main uninstall flag first
        if env.args.uninstall:
            return True

        # If not set globally, check if any utility has it in its args
        if utilities:
            return any(
                utility.maybe_args and utility.maybe_args.as_dict().get("uninstall", False) for utility in utilities
            )

        return False

    def _execute_install_flow(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        """Execute the installation flow for a list of utilities."""
        if not utilities:
            logger.warning("No utilities to install")
            return PyFn.success([])

        # Process each utility and collect results
        return self._process_utility_list(env=env, utilities=utilities, processing_fn=self._install_single_utility)

    def _execute_uninstall_flow(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        """Execute the uninstallation flow for a list of utilities."""
        if not utilities:
            logger.warning("No utilities to uninstall")
            return PyFn.success([])

        # Get utility names for the confirmation message
        utility_names = ", ".join([utility.display_name for utility in utilities])

        # Prompt for confirmation if not already confirmed with -y flag
        if not env.ctx.is_auto_prompt():
            return PyFn.effect(
                lambda: env.collaborators.prompter().prompt_yes_no_fn(
                    message=f"Are you sure you want to uninstall {utility_names}",
                    post_yes_message=f"Uninstalling {utility_names}",
                    post_no_message=f"Aborting uninstallation of {utility_names}",
                )
            ).flat_map(
                lambda confirmed: (
                    self._process_utility_list(
                        env=env, utilities=utilities, processing_fn=self._uninstall_single_utility
                    )
                    if confirmed
                    else PyFn.success([])
                )
            )

        # Process each utility and collect results
        return self._process_utility_list(env=env, utilities=utilities, processing_fn=self._uninstall_single_utility)

    def _process_utility_list(
        self, env: InstallerEnv, utilities: List[Installable.Utility], processing_fn: callable
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        """Process a list of utilities using the provided processing function."""
        # Use for_each to process utilities in sequence
        installed_utilities = []

        def collect_result(result):
            if result is not None:
                installed_utilities.append(result)
            return result

        return (
            PyFn.of(utilities)
            .for_each(lambda utility: processing_fn(env, utility).map(lambda result: collect_result(result)))
            .map(lambda _: installed_utilities)
        )

    def _install_single_utility(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        """Install a single utility with proper checks and validation."""
        return (
            # Step 1: Check if utility is already installed
            self._check_if_utility_already_installed(env, utility)
            # Step 2: Handle already installed utilities (may return None to skip installation)
            .flat_map(
                lambda util_install_tuple: self._notify_if_utility_already_installed(
                    env, util_install_tuple.utility, util_install_tuple.installed
                )
            )
            # Step 3: Print pre-install summary if not skipped
            .flat_map(
                lambda maybe_utility: (
                    PyFn.empty() if maybe_utility is None else self._print_pre_install_summary(env, maybe_utility)
                )
            )
            # Step 4: Install the utility based on its source type
            .flat_map(
                lambda maybe_utility: (
                    PyFn.empty() if maybe_utility is None else self._install_by_source_type(env, maybe_utility)
                )
            )
            # Step 5: Trigger version command to verify installation
            .flat_map(
                lambda maybe_utility: (
                    PyFn.empty() if maybe_utility is None else self._trigger_utility_version_command(env, maybe_utility)
                )
            )
            # Step 6: Print post-install summary
            .flat_map(
                lambda maybe_utility: (
                    PyFn.empty() if maybe_utility is None else self._print_post_install_summary(env, maybe_utility)
                )
            )
        )

    def _uninstall_single_utility(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        """Uninstall a single utility."""
        return PyFn.effect(lambda: env.collaborators.printer().print_fn(f"Uninstalling utility: {utility.display_name}")).flat_map(
            lambda _: self._uninstall_utility_locally(env, utility)
        )

    def _uninstall_github_utility(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Uninstall a GitHub-based utility by removing the symlink and binaries directory."""
        symlink_path = self._genreate_binary_symlink_path(utility.binary_name)
        binaries_path = f"{ProvisionerInstallableBinariesPath}/{utility.binary_name}"

        env.collaborators.printer().print_fn(f"Removing symlink at {symlink_path}")
        env.collaborators.printer().print_fn(f"Removing binary directory at {binaries_path}")

        # First remove symlink, then try to remove the binaries directory
        return (
            # Remove symlink first
            PyFn.effect(lambda: self._safely_remove_symlink(env, symlink_path))
            # Then remove binaries directory
            .flat_map(lambda _: PyFn.effect(lambda: self._safely_remove_directory(env, binaries_path)))
            # Always return the utility
            .map(lambda _: utility)
        )

    def _safely_remove_symlink(self, env: InstallerEnv, symlink_path: str) -> None:
        """Safely remove a symlink with error handling."""
        try:
            env.collaborators.io_utils().remove_symlink_fn(symlink_path)
        except Exception as e:
            logger.warning(f"Could not remove symlink at {symlink_path}: {str(e)}")

    def _safely_remove_directory(self, env: InstallerEnv, directory_path: str) -> None:
        """Safely remove a directory with error handling."""
        try:
            env.collaborators.io_utils().delete_directory_fn(directory_path)
        except Exception as e:
            logger.warning(f"Could not remove directory at {directory_path}: {str(e)}")

    def _trigger_utility_version_command(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        return (
            PyFn.effect(
                lambda: (
                    env.collaborators.process().run_fn(args=[utility.binary_name, utility.version_command])
                    if utility.version_command
                    else env.collaborators.printer().print_fn(
                        f"Warning: No version command defined for {utility.display_name}"
                    )
                )
            )
            .flat_map(
                lambda output: PyFn.effect(
                    lambda: env.collaborators.printer().print_fn("Version installed: \n" + output)
                )
            )
            .map(lambda _: utility)
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
        if exists and not env.args.force:
            return PyFn.effect(
                lambda: env.collaborators.printer().print_fn(
                    f"Utility already installed locally. name: {utility.binary_name}"
                )
            ).map(lambda _: None)
        elif exists and env.args.force:
            return PyFn.effect(
                lambda: env.collaborators.printer().print_fn(f"Force reinstalling utility. name: {utility.binary_name}")
            ).map(lambda _: utility)
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
        """Install a utility based on its source type."""
        return self._install_by_source_type(env, utility)

    def _install_by_source_type(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Route installation to the appropriate method based on source type."""
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

    def _uninstall_utility_locally(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Handle uninstallation of utilities based on their source type."""
        # First check if utility is actually installed (but still continue even if not installed)
        return PyFn.effect(lambda: env.collaborators.checks().is_tool_exist_fn(utility.binary_name)).flat_map(
            lambda binary_exists: (
                PyFn.effect(
                    lambda: env.collaborators.printer().print_fn(f"Note: Utility {utility.display_name} is not currently installed")
                ).flat_map(lambda _: self._uninstall_by_source_type(env, utility))
                if not binary_exists
                else self._uninstall_by_source_type(env, utility)
            )
        )

    def _uninstall_by_source_type(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Route uninstallation to the appropriate method based on source type."""
        match utility.active_source:
            case ActiveInstallSource.Callback:
                return self._uninstall_callback_utility(env, utility)
            case ActiveInstallSource.GitHub:
                return self._uninstall_github_utility(env, utility)
            case ActiveInstallSource.Script:
                return self._uninstall_script_utility(env, utility)
            case ActiveInstallSource.Ansible:
                return self._uninstall_ansible_utility(env, utility)
            case _:
                return PyFn.fail(
                    error=InstallerSourceError(
                        f"Invalid installation active source for uninstall. value: {utility.active_source}"
                    )
                )

    def _uninstall_callback_utility(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Uninstall a callback-based utility."""
        if (
            utility.has_callback_active_source()
            and hasattr(utility.source.callback, "uninstall_fn")
            and utility.source.callback.uninstall_fn
        ):
            logger.info(f"Uninstalling callback-based utility: {utility.display_name}")
            maybe_args = utility.maybe_args if utility.maybe_args is not None else None
            return PyFn.effect(
                lambda: utility.source.callback.uninstall_fn(utility.version, env.collaborators, maybe_args)
            ).map(lambda _: utility)
        else:
            return self._uninstall_symlink(env, utility)

    def _uninstall_script_utility(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Uninstall a script-based utility."""
        if utility.has_script_active_source() and hasattr(utility.source.script, "uninstall_script"):
            return PyFn.effect(
                lambda: env.collaborators.process().run_fn(
                    args=[utility.source.script.uninstall_script], allow_single_shell_command_str=True
                )
            ).map(lambda _: utility)
        else:
            return self._uninstall_symlink(env, utility)

    def _uninstall_ansible_utility(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Uninstall an Ansible-based utility."""
        if (
            utility.has_ansible_active_source()
            and hasattr(utility.source.ansible, "uninstall_tags")
            and utility.source.ansible.uninstall_tags
        ):
            ansible_vars = []
            if utility.maybe_args is not None:
                ansible_vars.extend(utility.maybe_args.as_ansible_vars())
            ansible_vars.extend(utility.source.ansible.ansible_vars)
            ansible_vars.append(f"git_access_token={env.args.git_access_token}")
            ansible_vars.append("uninstall=true")

            return PyFn.effect(
                lambda: env.collaborators.progress_indicator()
                .get_status()
                .long_running_process_fn(
                    call=lambda: env.collaborators.ansible_runner().run_fn(
                        selected_hosts=self._get_ssh_conn_info_localhost().ansible_hosts,
                        playbook=utility.source.ansible.playbook,
                        ansible_vars=ansible_vars,
                        ansible_tags=utility.source.ansible.uninstall_tags,
                    ),
                    desc_run=f"Running Ansible playbook to uninstall ({utility.source.ansible.playbook.get_name()})).",
                    desc_end=f"Ansible playbook uninstall finished ({utility.source.ansible.playbook.get_name()})).",
                )
            ).map(lambda _: utility)
        else:
            return self._uninstall_symlink(env, utility)

    def _uninstall_symlink(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Installable.Utility]:
        """Remove the symlink for a utility as a basic uninstall method."""
        symlink_path = self._genreate_binary_symlink_path(utility.binary_name)

        return (
            PyFn.of(env)
            .flat_map(lambda e: e.collaborators.io_utils().remove_symlink_fn(symlink_path))
            .flat_map(lambda _: PyFn.effect(lambda: env.collaborators.printer().print_fn(f"Removed symlink at {symlink_path}")))
            .flat_map(
                lambda _: PyFn.effect(lambda: env.collaborators.printer().print_fn(f"Basic uninstall of {utility.display_name} completed"))
            )
            .map(lambda _: utility)
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
            maybe_args = utility.maybe_args if utility.maybe_args is not None else None
            return PyFn.effect(
                lambda: utility.source.callback.install_fn(utility.version, env.collaborators, maybe_args)
            ).map(lambda _: utility)

    def _try_resolve_utility_version(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", VersionResolverError, Utility_Version_Tuple]:
        if not utility.version or utility.version == "latest":
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
    ) -> PyFn["UtilityInstallerCmdRunner", OsArchNotSupported, Utility_Version_ReleaseFileName_OsArch_Tuple]:
        release_filename = util_ver_tuple.utility.source.github.resolve_binary_release_name(
            env.ctx.os_arch, util_ver_tuple.version
        )
        if not release_filename:
            return PyFn.fail(
                OsArchNotSupported(
                    f"OS/Arch is not supported. name: {util_ver_tuple[0].display_name}, os_arch: {env.ctx.os_arch.as_pair()}"
                )
            )
        os_arch_adjusted = util_ver_tuple.utility.source.github.get_adjusted_os_arch(env.ctx.os_arch)
        if not os_arch_adjusted:
            return PyFn.fail(
                OsArchNotSupported(
                    f"OS/Arch is not supported. name: {util_ver_tuple[0].display_name}, os_arch: {env.ctx.os_arch.as_pair()}"
                )
            )
        return PyFn.success(
            Utility_Version_ReleaseFileName_OsArch_Tuple(
                util_ver_tuple.utility, util_ver_tuple.version, release_filename, os_arch_adjusted
            )
        )

    def _print_before_downloading(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", None, Utility_Version_ReleaseFileName_OsArch_Tuple]:
        return PyFn.effect(
            lambda: self._print_github_binary_info(env=env, util_ver_name_tuple=util_ver_name_tuple)
        ).map(lambda _: util_ver_name_tuple)

    def _print_github_binary_info(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> None:
        env.collaborators.printer().new_line_fn().print_fn(
            f"Downloading from GitHub. owner: {util_ver_name_tuple.utility.source.github.owner}, repo: {util_ver_name_tuple.utility.source.github.repo}, name: {util_ver_name_tuple.release_filename}, version: {util_ver_name_tuple.version}"
        )

    def _download_binary_by_version(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple]:
        if util_ver_name_tuple.utility.source.github.alternative_base_url:
            return self._download_from_http_client(env, util_ver_name_tuple)
        else:
            return self._download_from_github(env, util_ver_name_tuple)

    def _download_from_http_client(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple]:
        return PyFn.effect(
            lambda: env.collaborators.http_client().download_file_fn(
                url=f"{util_ver_name_tuple.utility.source.github.alternative_base_url}/{util_ver_name_tuple.release_filename}",
                progress_bar=True,
                download_folder=self._genreate_binary_folder_path(
                    util_ver_name_tuple.utility.binary_name, util_ver_name_tuple.version
                ),
                verify_already_downloaded=True,
            )
        ).flat_map(lambda filepath: self._create_release_tuple(filepath, util_ver_name_tuple))

    def _download_from_github(
        self, env: InstallerEnv, util_ver_name_tuple: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple]:
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
        ).flat_map(lambda filepath: self._create_release_tuple(filepath, util_ver_name_tuple))

    def _create_release_tuple(
        self, download_filepath: str, util_ver_name_tuple: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple]:
        return PyFn.of(
            ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple(
                util_ver_name_tuple.release_filename,
                download_filepath,
                util_ver_name_tuple.utility,
                util_ver_name_tuple.os_arch_adjusted,
            )
        )

    def _maybe_extract_downloaded_binary(
        self,
        env: InstallerEnv,
        release_info: ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple,
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, UnpackedReleaseFolderPath_Utility_OsArch_Tuple]:
        """Extract the downloaded binary if it's an archive, otherwise return the parent directory."""
        release_filepath = release_info.release_download_filepath

        return (
            # Check if the file is an archive
            PyFn.effect(lambda: env.collaborators.io_utils().is_archive_fn(release_filepath)).flat_map(
                lambda is_archive: (
                    # If it's an archive, extract it and log the extraction
                    self._extract_and_log_archive(env, release_filepath, release_info.utility)
                    if is_archive
                    # Otherwise, just use the parent directory as the extraction path
                    else PyFn.of(str(pathlib.Path(release_filepath).parent))
                )
            )
            # Create the tuple with the extraction path and utility info
            .map(
                lambda extraction_path: UnpackedReleaseFolderPath_Utility_OsArch_Tuple(
                    extraction_path,
                    release_info.utility,
                    release_info.os_arch_adjusted,
                )
            )
        )

    def _extract_and_log_archive(
        self, env: InstallerEnv, archive_path: str, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, str]:
        """Extract an archive and log the extraction."""
        return (
            # Extract the archive
            PyFn.effect(lambda: env.collaborators.io_utils().unpack_archive_fn(archive_path))
            # Log the extraction
            .flat_map(
                lambda extraction_path: PyFn.effect(
                    lambda: env.collaborators.printer().print_fn(
                        f"Unpacked Utility: {utility.display_name}, "
                        f"archive: {os.path.basename(archive_path)}, "
                        f"path: {extraction_path}"
                    )
                ).map(lambda _: extraction_path)
            )
        )

    def _elevate_permission_and_symlink(
        self, env: InstallerEnv, unpackedreleasefolderpath_utility_tuple: UnpackedReleaseFolderPath_Utility_OsArch_Tuple
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
        """Install a utility from GitHub releases."""
        if not utility.source.github:
            return PyFn.fail(error=InstallerSourceError("Missing installation source. name: GitHub"))

        return (
            # Resolve version & validate source
            self._resolve_github_release_info(env, utility)
            # Download the binary
            .flat_map(lambda release_info: self._download_github_binary(env, release_info))
            # Extract and prepare the binary
            .flat_map(lambda download_info: self._prepare_github_binary(env, download_info))
            # Return the original utility
            .map(lambda _: utility)
        )

    def _resolve_github_release_info(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, Utility_Version_ReleaseFileName_OsArch_Tuple]:
        """Resolve version and file information for a GitHub release."""
        return (
            # Resolve version (latest or specified)
            self._try_resolve_utility_version(env, utility)
            # Get release filename based on OS/Arch
            .flat_map(lambda util_ver_tuple: self._try_get_github_release_name_by_os_arch(env, util_ver_tuple))
            # Log download information
            .flat_map(lambda util_ver_name_tuple: self._print_before_downloading(env, util_ver_name_tuple))
        )

    def _download_github_binary(
        self, env: InstallerEnv, release_info: Utility_Version_ReleaseFileName_OsArch_Tuple
    ) -> PyFn[
        "UtilityInstallerCmdRunner", InstallerSourceError, ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple
    ]:
        """Download the binary from GitHub or alternative URL."""
        return self._download_binary_by_version(env, release_info)

    def _prepare_github_binary(
        self, env: InstallerEnv, download_info: ReleaseFilename_ReleaseDownloadFilePath_Utility_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, None]:
        """Extract, prepare, and install the GitHub binary."""
        return (
            # Extract archive if needed
            self._maybe_extract_downloaded_binary(env, download_info)
            # Move binary to root if needed
            .flat_map(lambda extraction_info: self._force_binary_at_download_path_root(env, extraction_info))
            # Set permissions and create symlink
            .flat_map(lambda extraction_info: self._setup_binary_permissions_and_symlink(env, extraction_info))
        )

    def _setup_binary_permissions_and_symlink(
        self, env: InstallerEnv, extraction_info: UnpackedReleaseFolderPath_Utility_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, None]:
        """Set binary permissions and create symlink."""
        binary_path = f"{extraction_info.unpacked_release_folderpath}/{extraction_info.utility.binary_name}"
        symlink_path = self._genreate_binary_symlink_path(extraction_info.utility.binary_name)

        return (
            # Set executable permissions
            PyFn.effect(lambda: env.collaborators.io_utils().set_file_permissions_fn(file_path=binary_path))
            # Create symlink
            .flat_map(
                lambda _: PyFn.effect(lambda: env.collaborators.io_utils().write_symlink_fn(binary_path, symlink_path))
            )
        )

    def _force_binary_at_download_path_root(
        self, env: InstallerEnv, unpacked_release_folderpath_util_tuple: UnpackedReleaseFolderPath_Utility_OsArch_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, UnpackedReleaseFolderPath_Utility_OsArch_Tuple]:
        if unpacked_release_folderpath_util_tuple.utility.source.github.archive_nested_binary_path:
            return PyFn.effect(
                lambda: env.collaborators.io_utils().copy_file_fn(
                    unpacked_release_folderpath_util_tuple.unpacked_release_folderpath
                    / unpacked_release_folderpath_util_tuple.utility.source.github.archive_nested_binary_path(
                        unpacked_release_folderpath_util_tuple.utility.version,
                        unpacked_release_folderpath_util_tuple.os_arch_adjusted.os,
                        unpacked_release_folderpath_util_tuple.os_arch_adjusted.arch,
                    ),
                    unpacked_release_folderpath_util_tuple.unpacked_release_folderpath,
                )
            ).map(lambda _: unpacked_release_folderpath_util_tuple)
        else:
            return PyFn.success(unpacked_release_folderpath_util_tuple)

    def _genreate_binary_folder_path(self, binary_name: str, version: str) -> str:
        return f"{ProvisionerInstallableBinariesPath}/{binary_name}/{version}"

    def _genreate_binary_symlink_path(self, binary_name: str) -> str:
        return f"{ProvisionerInstallableSymlinksPath}/{binary_name}"

    def _install_on_remote_machine(
        self, env: InstallerEnv, sshconninfo_utility_info: SSHConnInfo_Utility_Tuple
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, str]:
        """Run the installation on a remote machine using Ansible."""
        return PyFn.effect(
            lambda: env.collaborators.progress_indicator()
            .get_status()
            .long_running_process_fn(
                call=lambda: self._execute_remote_ansible_playbook(
                    env=env,
                    ssh_conn_info=sshconninfo_utility_info.ssh_conn_info,
                    utility=sshconninfo_utility_info.utility,
                ),
                desc_run="Running Ansible playbook remotely (Provisioner Wrapper)",
                desc_end="Ansible playbook finished remotely (Provisioner Wrapper).",
            ),
        )

    def _execute_remote_ansible_playbook(
        self, env: InstallerEnv, ssh_conn_info: SSHConnectionInfo, utility: Installable.Utility
    ) -> str:
        """Execute the Ansible playbook that installs utilities on remote machines."""
        command = self._build_provisioner_command(env, utility)
        logger.debug(f"Remote provisioner command: {command}")

        ansible_vars = self._prepare_ansible_vars(env)

        args = RemoteProvisionerRunnerArgs(
            provisioner_command=command,
            remote_context=env.args.remote_opts.get_remote_context(),
            ssh_connection_info=ssh_conn_info,
            required_plugins=["provisioner_installers_plugin"],
            ansible_vars=ansible_vars,
        )
        return RemoteProvisionerRunner().run(env.ctx, args, env.collaborators)

    def _prepare_ansible_vars(self, env: InstallerEnv) -> List[str]:
        """Prepare Ansible variables for the remote installation."""
        ansible_vars = [
            f"git_access_token={env.args.git_access_token}",
        ]
        return ansible_vars

    def _build_provisioner_command(self, env: InstallerEnv, utility: Installable.Utility) -> str:
        """Build the provisioner command to run on the remote machine."""
        # Determine if this is an uninstall operation
        is_uninstall = env.args.uninstall or (
            utility.maybe_args and utility.maybe_args.as_dict().get("uninstall", False)
        )

        # Always use "install" as the base command
        operation = "install"

        # Format utility name with version if applicable
        if env.args.sub_command_name == InstallerSubCommandName.CLI:
            utility_maybe_ver = f"{utility.display_name}@{utility.version}" if utility.version else utility.display_name
        else:
            utility_maybe_ver = utility.display_name

        # Get utility args if any
        utility_maybe_args = ""
        if utility.maybe_args is not None:
            # For uninstall operations, remove the uninstall flag since we'll add it separately
            if is_uninstall and utility.maybe_args:
                args_dict = utility.maybe_args.as_dict().copy()
                if "uninstall" in args_dict:
                    del args_dict["uninstall"]
                utility_maybe_args = DynamicArgs(args_dict).as_cli_args()
            else:
                utility_maybe_args = utility.maybe_args.as_cli_args()

        # Format force flag
        is_force_flag = "--force" if env.args.force else ""

        # Format uninstall flag
        uninstall_flag = "--uninstall" if is_uninstall else ""

        # Build the full command
        verbose_flag = "-v" if env.args.remote_opts.get_remote_context().is_verbose() else ""

        # Clean utility args (remove any double quotes that might cause issues)
        # This is especially important for uninstall operations where we don't want shell interpretation issues
        utility_maybe_args = utility_maybe_args.replace('"', '\\"')

        # Return the simple command without bash -c wrapping
        return f"{operation} --environment Local {env.args.sub_command_name} {utility_maybe_ver} {utility_maybe_args} {uninstall_flag} {is_force_flag} -y {verbose_flag}"

    def _filter_ansible_warnings(self, output: str) -> str:
        # Ansible warnings should be handled through ansible.cfg settings, not filtered here
        return output

    def _install_locally_from_ansible_playbook(
        self, env: InstallerEnv, utility: Installable.Utility
    ) -> PyFn["UtilityInstallerCmdRunner", InstallerSourceError, str]:
        if not utility.has_ansible_active_source():
            return PyFn.fail(error=InstallerSourceError("Missing installation source. name: Ansible"))
        else:
            ansible_vars = []
            if utility.maybe_args is not None:
                ansible_vars.extend(utility.maybe_args.as_ansible_vars())
            ansible_vars.extend(utility.source.ansible.ansible_vars)
            ansible_vars.append(f"git_access_token={env.args.git_access_token}")

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
                        ansible_vars=ansible_vars,
                        ansible_tags=utility.source.ansible.ansible_tags,
                    ),
                    desc_run=f"Running Ansible playbook locally ({utility.source.ansible.playbook.get_name()})).",
                    desc_end=f"Ansible playbook finished locally ({utility.source.ansible.playbook.get_name()})).",
                )
            )

    def _print_ansible_response(self, env: InstallerEnv, output: str):
        # Simply print the output, letting ansible.cfg handle warning suppression
        return PyFn.effect(lambda: env.collaborators.printer().print_fn(output))

    def _collect_ssh_connection_info(
        self, env: InstallerEnv, connector: RemoteMachineConnector
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, SSHConnectionInfo]:
        """Collect SSH connection information for remote hosts."""
        return PyFn.effect(
            lambda: env.collaborators.summary().append_result(
                attribute_name="ssh_conn_info",
                call=lambda: connector.collect_ssh_connection_info(
                    env.ctx, env.args.remote_opts, force_single_conn_info=True
                ),
            )
        )

    def _run_remote_installation(
        self, env: InstallerEnv, utilities: List[Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        """Handle the remote installation flow for utilities."""
        logger.debug(
            f"Running remote installation for utilities: {[u.display_name for u in utilities] if utilities else 'None'}"
        )

        # Early return if no utilities
        if not utilities:
            logger.warning("No utilities to install remotely")
            return PyFn.success([])

        return (
            # Get remote connector and SSH connection info
            self._get_remote_connector_and_connection_info(env)
            # Process utilities on remote hosts
            .flat_map(lambda ssh_conn_info: self._process_remote_utilities(env, utilities, ssh_conn_info))
        )

    def _get_remote_connector_and_connection_info(
        self, env: InstallerEnv
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, SSHConnectionInfo]:
        """Get remote connector and collect SSH connection info."""
        return PyFn.of(RemoteMachineConnector(collaborators=env.collaborators)).flat_map(
            lambda connector: self._collect_ssh_connection_info(env, connector)
        )

    def _process_remote_utilities(
        self, env: InstallerEnv, utilities: List[Installable.Utility], ssh_conn_info: SSHConnectionInfo
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, List[Installable.Utility]]:
        """Process utilities on remote hosts."""
        # Check if we have hosts to install to
        if not self._has_remote_hosts(ssh_conn_info):
            logger.warning("No remote hosts found to install utilities on. Returning without installation.")
            return PyFn.success(utilities)

        logger.debug(f"Found SSH connection info with {len(ssh_conn_info.ansible_hosts)} hosts")

        # Use for_each to process each utility
        installed_utilities = []

        def collect_result(result):
            if result is not None:
                installed_utilities.append(result)
            return result

        return (
            PyFn.of(utilities)
            .for_each(
                lambda utility: self._install_single_utility_remotely(env, utility, ssh_conn_info).map(
                    lambda result: collect_result(result)
                )
            )
            .map(lambda _: installed_utilities)
        )

    def _has_remote_hosts(self, ssh_conn_info: SSHConnectionInfo) -> bool:
        """Check if there are remote hosts available."""
        return ssh_conn_info.ansible_hosts is not None and len(ssh_conn_info.ansible_hosts) > 0

    def _install_single_utility_remotely(
        self, env: InstallerEnv, utility: Installable.Utility, ssh_conn_info: SSHConnectionInfo
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        """Install a single utility on remote hosts."""
        return (
            # Create tuple with SSH connection info and utility
            PyFn.of(SSHConnInfo_Utility_Tuple(ssh_conn_info, utility))
            # Print pre-install summary
            .flat_map(
                lambda tuple_info: self._print_pre_install_summary(env, tuple_info.utility).map(lambda _: tuple_info)
            )
            # Execute remote installation
            .flat_map(
                lambda tuple_info: self._install_on_remote_machine(env, tuple_info).map(
                    lambda output: (output, tuple_info.utility)
                )
            )
            # Print output and return utility
            .flat_map(lambda output_utility: self._print_remote_output_and_return_utility(env, output_utility))
        )

    def _print_remote_output_and_return_utility(
        self, env: InstallerEnv, output_utility_tuple: tuple[str, Installable.Utility]
    ) -> PyFn["UtilityInstallerCmdRunner", Exception, Installable.Utility]:
        """Print remote output and return the utility."""
        output, utility = output_utility_tuple
        return PyFn.effect(lambda: env.collaborators.printer().new_line_fn().print_fn(output)).map(lambda _: utility)


@staticmethod
def generate_installer_welcome(
    utilities_to_install: List[Installable.Utility], environment: Optional[RunEnvironment], is_uninstall: bool = False
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

    operation = "uninstall" if is_uninstall else "install"
    return f"""About to {operation} the following CLI utilities:
{selected_utils_names}
{env_indicator}"""
