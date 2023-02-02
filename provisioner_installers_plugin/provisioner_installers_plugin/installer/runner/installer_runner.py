#!/usr/bin/env python3

import os
from typing import List, Optional

from loguru import logger
from python_core_lib.errors.cli_errors import (
    FailedToResolveLatestVersionFromGitHub,
    InstallerUtilityNotSupported,
    OsArchNotSupported,
)
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.github import GitHub
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.process import Process
from python_core_lib.utils.prompter import Prompter
from python_core_lib.utils.summary import Summary
from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.remote_connector import RemoteMachineConnector
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts

from provisioner_installers_plugin.installer.installables import (
    Installables,
    SupportedInstallables,
)

# Since Ansible can be executed within a Docker container we need to use the absolute path
# as a mounted volume, this is done by reading the path using io_utils
ProvisionerRunAnsiblePlaybookRelativePath = "provisioner_installers_plugin/installer/playbooks/provisioner_run.yaml"
ProvisionerInstallableBinariesPath = os.path.expanduser("~/.config/provisioner/binaries")
ProvisionerInstallableSymlinksPath = os.path.expanduser("~/.local/bin")


class UtilityInstallerRunnerCmdArgs:

    utilities: List[str]
    remote_opts: CliRemoteOpts

    def __init__(self, utilities: List[str], remote_opts: CliRemoteOpts) -> None:
        self.utilities = utilities
        self.remote_opts = remote_opts


class UtilityInstallerCmdRunner:
    def run(
        self,
        ctx: Context,
        args: UtilityInstallerRunnerCmdArgs,
        collaborators: CoreCollaborators,
    ) -> None:

        logger.debug("Inside UtilityInstallerCmdRunner run()")

        utilities_to_install = Evaluator.eval_size_else_throws(
            call=lambda: self._verify_utilities_choice(SupportedInstallables, args.utilities),
            ctx=ctx,
            err_msg="No utilities were resolved",
        )
        collaborators.summary().append("utilities", utilities_to_install)

        collaborators.printer().print_with_rich_table_fn(
            generate_installer_welcome(args.utilities, args.remote_opts.environment)
        )

        selected_run_env = Evaluator.eval_step_with_return_throw_on_failure(
            call=lambda: self._resolve_run_environment(args.remote_opts.environment, collaborators.prompter()),
            ctx=ctx,
            err_msg="Could not resolve run environment",
        )
        collaborators.summary().append("run_env", selected_run_env)

        if selected_run_env == RunEnvironment.Local:
            Evaluator.eval_step_no_return_throw_on_failure(
                call=lambda: self._run_local_installation(ctx, utilities_to_install, collaborators),
                ctx=ctx,
                err_msg=f"Failed to install a CLI utility locally.",
            )

        elif selected_run_env == RunEnvironment.Remote:
            Evaluator.eval_step_no_return_throw_on_failure(
                call=lambda: self._run_remote_installation(ctx, utilities_to_install, collaborators, args.remote_opts),
                ctx=ctx,
                err_msg=f"Failed to install a CLI utility on a remote machine.",
            )

    def _run_local_installation(
        self, ctx: Context, utilities: List[Installables.InstallableUtility], collaborators: CoreCollaborators
    ):

        # TODO: resolve OS/Arch

        for utility in utilities:

            # TODO: check if tool exists locally

            self._print_pre_install_summary(
                utility.name, ctx.is_auto_prompt(), collaborators.printer(), collaborators.prompter(), collaborators.summary()
            )
            self._install_utility_locally(
                ctx=ctx,
                utility=utility,
                github=collaborators.github(),
                process=collaborators.process(),
                printer=collaborators.printer(),
            )

    def _install_utility_locally(
        self, ctx: Context, utility: Installables.InstallableUtility, github: GitHub, process: Process, printer: Printer
    ):

        # TODO: for command lines we need to support additional install args
        # if utility.has_install_command():
        #     output = process.run_fn(args=[utility.install_cmd], allow_single_shell_command_str=True)

        binary_name = utility.get_binary_name_by_os_arch(ctx.os_arch)
        if not binary_name:
            raise OsArchNotSupported(
                f"OS/Arch is not supported. name: {utility.display_name}, os_arch: {ctx.os_arch.as_pair()}"
            )

        latest_version = github.get_latest_version_fn(owner=utility.owner, repo=utility.repo)
        if not latest_version:
            raise FailedToResolveLatestVersionFromGitHub(
                f"Failed to resolve latest version from GitHub. owner: {utility.owner}, repo: {utility.repo}"
            )

        printer.new_line_fn()
        printer.print_fn(f"LATEST VERSION: {latest_version}")
        github.download_binary_fn(
            owner=utility.owner,
            repo=utility.repo,
            version=latest_version,
            binary_name=binary_name,
            binary_path=self._genreate_binary_path(binary_name),
        )

        # TODO: If binary is archive - extract

        # TODO: Set chmod +x on the binary

        # TODO: create symlink

    def _genreate_binary_path(self, binary_name: str) -> str:
        return f"{ProvisionerInstallableBinariesPath}/{binary_name}"

    def _run_remote_installation(
        self,
        ctx: Context,
        utilities: List[Installables.InstallableUtility],
        collaborators: CoreCollaborators,
        remote_opts: CliRemoteOpts,
    ):

        remote_connector = None
        ssh_conn_info = None
        remote_connector = RemoteMachineConnector(
            collaborators.checks(), collaborators.printer(), collaborators.prompter(), collaborators.network_util()
        )
        ssh_conn_info = Evaluator.eval_step_with_return_throw_on_failure(
            call=lambda: remote_connector.collect_ssh_connection_info(ctx, remote_opts),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().append("ssh_conn_info", ssh_conn_info)

        for utility in utilities:
            self._print_pre_install_summary(
                utility.name, ctx.is_auto_prompt(), collaborators.printer(), collaborators.prompter(), collaborators.summary()
            )

            ansible_vars = [f"\"provisioner_command='provisioner -y install cli --environment=Local {utility.name}'\""]

            collaborators.printer().new_line_fn()

            output = collaborators.printer().progress_indicator.status.long_running_process_fn(
                call=lambda: collaborators.ansible_runner().run_fn(
                    working_dir=collaborators.paths().get_path_from_exec_module_root_fn(),
                    username=ssh_conn_info.username,
                    password=ssh_conn_info.password,
                    ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                    playbook_path=collaborators.paths().get_path_relative_from_module_root_fn(
                        __name__, ProvisionerRunAnsiblePlaybookRelativePath
                    ),
                    extra_modules_paths=[collaborators.paths().get_path_abs_to_module_root_fn(__name__)],
                    ansible_vars=ansible_vars,
                    ansible_tags=["provisioner_run"],
                    selected_hosts=ssh_conn_info.host_ip_pairs,
                ),
                desc_run="Running Ansible playbook (Provisioner Run)",
                desc_end="Ansible playbook finished (Provisioner Run).",
            )

            collaborators.printer().new_line_fn()
            collaborators.printer().print_fn(output)

    def _verify_utilities_choice(
        self, installables: Installables, utilities_names: List[str]
    ) -> List[Installables.InstallableUtility]:
        result: List[Installables.InstallableUtility] = []
        for utility_name in utilities_names:
            if utility_name not in installables.utilities:
                raise InstallerUtilityNotSupported(f"{utility_name} is not supported as an installable utility")
            result.append(installables.utilities[utility_name])

        return result

    def _resolve_run_environment(self, run_env: RunEnvironment, prompter: Prompter) -> RunEnvironment:
        if run_env:
            return run_env

        options_dict: List[str] = ["Local", "Remote"]
        selected_scanned_item: dict = prompter.prompt_user_single_selection_fn(
            message="Please choose an environment", options=options_dict
        )
        if selected_scanned_item == "Local":
            return RunEnvironment.Local
        elif selected_scanned_item == "Remote":
            return RunEnvironment.Remote
        return None

    def _print_pre_install_summary(self, name: str, summary: Summary) -> None:
        summary.show_summary_and_prompt_for_enter(f"Installing Utility: {name}")

def generate_installer_welcome(utilities_to_install: List[str], environment: Optional[RunEnvironment]) -> str:
    selected_utils_names = ""
    if utilities_to_install:
        for utility in utilities_to_install:
            selected_utils_names += f"  - {utility}\n"

    env_indicator = ""
    if not environment:
        env_indicator = """[yellow]Environment was not set, you will be prompted to select a local/remote environment.[/yellow]

When opting-in for the remote option you will be prompted for additional arguments."""
    else:
        env_indicator = f"Running on [yellow]{environment}[/yellow] environment."

    return f"""About to install the following CLI utilities:
{selected_utils_names}
{env_indicator}"""


# utilities_to_install = Evaluator.eval_size_else_throws(
#             call=lambda: self._resolve_utilities_metadata(collaborators.io, collaborators.json_util, collaborators.prompter, args),
#             ctx=ctx,
#             err_msg="No utilities were resolved",
#         )
#         collaborators.summary.append("utilities", utilities_to_install)

# def _resolve_utilities_metadata(
#         self, io_utiles: IOUtils, json_util: JsonUtil, prompter: Prompter, args: UtilityInstallerRunnerCmdArgs
#     ) -> List[Installables.InstallableUtility]:
#         """
#         Verify the installable CLI utilities are supported.
#         """
#         installables_json_path = io_utiles.get_path_abs_to_module_root_fn(__name__, InstallablesJsonFileRelativePath)
#         installables = self._read_installables(installables_json_path, json_util)
#         if args.utilities and len(args.utilities) > 0:
#             return self._verify_utilities_choice(installables, args.utilities)
#         return None

#     def _read_installables(self, installables_json_path: str, json_util: JsonUtil) -> Installables:
#         return json_util.read_file_fn(file_path=installables_json_path, class_name=Installables)

# InstallablesJsonFileRelativePath = "provisioner_installers_plugin/installer/installables.json"

# class Installables(SerializationBase):
#     class InstallableUtility:
#         name: str
#         owner: str
#         repo: str
#         version: str

#         def __init__(self, name: str, owner: str, repo: str, version: str) -> None:
#             self.name = name
#             self.owner = owner
#             self.repo = repo
#             self.version = version

#     def _parse_utilities_block(self, utilities_block: dict):
#         for utility in utilities_block:
#             if "name" in utility and "owner" in utility and "repo" in utility and "version" in utility:
#                 u_obj = Installables.InstallableUtility(
#                     name=utility["name"],
#                     owner=utility["owner"],
#                     repo=utility["repo"],
#                     version=utility["version"])

#                 self.utilities[utility["name"]] = u_obj
#             else:
#                 logger.debug(f"Bad utility configuration, please check JSON file. name: {utility['name']}, file: installables.json")

#     def _try_parse_config(self, dict_obj: dict):
#         if "utilities" in dict_obj:
#             self.utilities = {}
#             self._parse_utilities_block(dict_obj["utilities"])

#     utilities: dict[str, InstallableUtility] = None


# def _start_utility_selection(
#         self, installables: Installables, prompter: Prompter
#     ) -> List[Installables.InstallableUtility]:
#         options_list: List[str] = []
#         for key in installables.utilities.keys():
#             options_list.append(key)
#         selected_utilities: dict = prompter.prompt_user_multi_selection_fn(
#             message="Please choose utilities", options=options_list
#         )

#         result: List[Installables.InstallableUtility] = []
#         for utility_name in selected_utilities:
#             if utility_name in installables.utilities:
#                 result.append(installables.utilities[utility_name])

#         return result
