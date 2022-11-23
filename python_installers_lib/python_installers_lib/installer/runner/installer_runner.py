#!/usr/bin/env python3

import pathlib
from typing import List, Optional

from loguru import logger
from python_core_lib.domain.serialize import SerializationBase
from python_core_lib.errors.cli_errors import InstallerUtilityNotSupported
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.runner.ansible.ansible import AnsibleRunner
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.network import NetworkUtil
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.process import Process
from python_core_lib.utils.progress_indicator import ProgressIndicator
from python_core_lib.utils.prompter import Prompter
from python_core_lib.utils.summary import Summary
from python_features_lib.remote.domain.config import RunEnvironment

from python_features_lib.remote.remote_connector import (
    RemoteMachineConnector,
)
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts

InstallablesJsonFilePath = f"{pathlib.Path(__file__).parent.parent}/installables.json"

class Installables(SerializationBase):
    class InstallableUtility:
        name: str
        owner: str
        repo: str
        version: str

        def __init__(self, name: str, owner: str, repo: str, version: str) -> None:
            self.name = name
            self.owner = owner
            self.repo = repo
            self.version = version

    def _parse_utilities_block(self, utilities_block: dict):
        for utility in utilities_block:
            if "name" in utility and "owner" in utility and "repo" in utility and "version" in utility:
                u_obj = Installables.InstallableUtility(
                    name=utility["name"],
                    owner=utility["owner"],
                    repo=utility["repo"],
                    version=utility["version"])
                    
                self.utilities[utility["name"]] = u_obj
            else:
                logger.debug(f"Bad utility configuration, please check JSON file. name: {utility['name']}, file: installables.json")

    def _try_parse_config(self, dict_obj: dict):
        if "utilities" in dict_obj:
            self.utilities = {}
            self._parse_utilities_block(dict_obj["utilities"])

    utilities: dict[str, InstallableUtility] = None


class UtilityInstallerRunnerCmdArgs:

    utilities: List[str]
    remote_opts: CliRemoteOpts

    def __init__(self, utilities: List[str], remote_opts: CliRemoteOpts) -> None:
        self.utilities = utilities
        self.remote_opts = remote_opts


class Collaborators:
    io: IOUtils
    checks: Checks
    json_util: JsonUtil
    summary: Summary
    prompter: Prompter
    printer: Printer
    process: Process
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil


class UtilityInstallerCmdRunnerCollaborators(Collaborators):
    def __init__(self, ctx: Context) -> None:
        self.io = IOUtils.create(ctx)
        self.checks = Checks.create(ctx)
        self.json_util = JsonUtil.create(ctx, self.io)
        self.process = Process.create(ctx)
        self.printer = Printer.create(ctx, ProgressIndicator.create(ctx, self.io))
        self.prompter = Prompter.create(ctx)
        self.ansible_runner = AnsibleRunner.create(ctx, self.io, self.process)
        self.network_util = NetworkUtil.create(ctx, self.printer)
        self.summary = Summary.create(ctx, self.json_util, self.printer, self.prompter)

class UtilityInstallerCmdRunner:
    def run(
        self,
        ctx: Context,
        args: UtilityInstallerRunnerCmdArgs,
        collaborators: Collaborators,
    ) -> None:

        logger.debug("Inside UtilityInstallerCmdRunner run()")

        utilities_to_install = Evaluator.eval_size_else_throws(
            call=lambda: self._resolve_utilities_metadata(collaborators.json_util, collaborators.prompter, args),
            ctx=ctx,
            err_msg="No utilities were resolved",
        )
        collaborators.summary.add_values("utilities", utilities_to_install)

        collaborators.printer.print_with_rich_table_fn(generate_installer_welcome(args.utilities, args.remote_opts.environment))        

        selected_run_env = Evaluator.eval_step_return_failure_throws(
            call=lambda: self._resolve_run_environment(args.remote_opts.environment, collaborators.prompter),
            ctx=ctx,
            err_msg="Could not resolve run environment",
        )
        collaborators.summary.add_value("run_env", selected_run_env)

        if selected_run_env == RunEnvironment.Local:
            Evaluator.eval_step_no_return_failure_throws(
                ctx=ctx,
                err_msg=f"Failed to install a CLI utility locally.",
                call=lambda: self._run_local_installation(ctx, utilities_to_install, collaborators))

        elif selected_run_env == RunEnvironment.Remote:
            Evaluator.eval_step_no_return_failure_throws(
                ctx=ctx,
                err_msg=f"Failed to install a CLI utility on a remote machine.",
                call=lambda: self._run_remote_installation(ctx, utilities_to_install, collaborators, args.remote_opts))

    def _run_local_installation(self,
        ctx: Context,
        utilities: List[Installables.InstallableUtility],
        collaborators: Collaborators):

        for utility in utilities:
            self._print_pre_install_summary(utility.name, ctx.is_auto_prompt(), collaborators.printer, collaborators.prompter, collaborators.summay)

    def _run_remote_installation(self,
        ctx: Context,
        utilities: List[Installables.InstallableUtility],
        collaborators: Collaborators,
        remote_opts: CliRemoteOpts):

        remote_connector = None
        ssh_conn_info = None
        remote_connector = RemoteMachineConnector(
            collaborators.checks, collaborators.printer, collaborators.prompter, collaborators.network_util
        )
        ssh_conn_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: remote_connector.collect_ssh_connection_info(ctx, remote_opts),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary.add_values("ssh_conn_info", ssh_conn_info)

        for utility in utilities:
            self._print_pre_install_summary(utility.name, ctx.is_auto_prompt(), collaborators.printer, collaborators.prompter, collaborators.summay)

            ansible_vars = [f"\"provision_command='{args.username}'\""]

            collaborators.printer.new_line_fn()

            working_dir = collaborators.io.get_project_root_path_fn(__file__)

            output = collaborators.printer.progress_indicator.status.long_running_process_fn(
                call=lambda: collaborators.ansible_runner.run_fn(
                    working_dir=working_dir,
                    username=ssh_conn_info.username,
                    password=ssh_conn_info.password,
                    ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                    playbook_path=args.ansible_playbook_relative_path_from_root,
                    ansible_vars=ansible_vars,
                    ansible_tags=["hello"],
                    selected_hosts=ssh_conn_info.host_ip_pairs,
                ),
                desc_run="Running Ansible playbook (Hello World)",
                desc_end="Ansible playbook finished (Hello World).",
            )

            collaborators.printer.new_line_fn()
            collaborators.printer.print_fn(output)

    def _resolve_utilities_metadata(
        self, json_util: JsonUtil, prompter: Prompter, args: UtilityInstallerRunnerCmdArgs
    ) -> List[Installables.InstallableUtility]:
        """
        Verify the installable CLI utilities are supported.
        """
        installables = self.read_installables(json_util)
        if args.utilities and len(args.utilities) > 0:
            return self._verify_utilities_choice(installables, args.utilities)
        return None

    def read_installables(self, json_util: JsonUtil) -> Installables:
        return json_util.read_file_fn(file_path=InstallablesJsonFilePath, class_name=Installables)

    def _verify_utilities_choice(
        self, installables: Installables, utilities_names: List[str]
    ) -> List[Installables.InstallableUtility]:
        result: List[Installables.InstallableUtility] = []
        for utility_name in utilities_names:
            if utility_name not in installables.utilities:
                raise InstallerUtilityNotSupported(f"{utility_name} is missing from the installables.json file")
            result.append(installables.utilities[utility_name])

        return result

    def _resolve_run_environment(self, run_env: RunEnvironment, prompter: Prompter) -> RunEnvironment:
        if run_env:
            return run_env

        options_dict: List[str] = ["Local", "Remote"]
        selected_scanned_item: dict = prompter.prompt_user_selection_fn(
            message="Please choose an environment", options=options_dict
        )
        if selected_scanned_item == "Local":
            return RunEnvironment.Local
        elif selected_scanned_item == "Remote":
            return RunEnvironment.Remote
        return None

    def _print_pre_install_summary(
        self, 
        name: str, 
        is_auto_prompt: bool, 
        printer: Printer, 
        prompter: Prompter,
        summary: Summary) -> None:

        printer.new_line_fn()
        printer.print_horizontal_line_fn(f"Installing Utility: {name}")
        printer.print_fn(summary.get_text())
        if not is_auto_prompt:
            printer.new_line_fn()
            prompter.prompt_for_enter_fn()

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