#!/usr/bin/env python3

from typing import List, Optional

from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible import AnsibleHost, AnsibleRunner
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.json_util import JsonUtil


class FakeAnsibleRunner(AnsibleRunner):

    # Used to serialize objects to string for assertion error logs
    json_util: JsonUtil = None

    @staticmethod
    def calculate_hash(
        selected_hosts: List[AnsibleHost],
        with_paths: AnsibleRunner.WithPaths,
        ansible_vars: List[str],
        ansible_tags: List[str],
        force_dockerized: bool,
    ) -> str:
        return hash(
            (tuple(selected_hosts), hash(with_paths), tuple(ansible_vars), tuple(ansible_tags), force_dockerized)
        )

    class FakeAnsibleCommandArgs:
        selected_hosts: List[AnsibleHost]
        with_paths: AnsibleRunner.WithPaths
        ansible_vars: List[str]
        ansible_tags: List[str]
        force_dockerized: bool

        def __init__(
            self,
            selected_hosts: List[AnsibleHost],
            with_paths: Optional[AnsibleRunner.WithPaths] = None,
            ansible_vars: Optional[List[str]] = None,
            ansible_tags: Optional[List[str]] = None,
            force_dockerized: Optional[bool] = False,
        ) -> None:

            self.selected_hosts = selected_hosts
            self.with_paths = with_paths
            self.ansible_vars = ansible_vars
            self.ansible_tags = ansible_tags
            self.force_dockerized = force_dockerized

        def __eq__(self, other):
            # print("=========== COMPARE ============")
            # print(f"this: " + str(self.__dict__))
            # print(f"that: " + str(other.__dict__))
            if isinstance(other, self.__class__):
                return hash(self) == hash(other)
            return False

        def __hash__(self):
            return FakeAnsibleRunner.calculate_hash(
                selected_hosts=self.selected_hosts,
                with_paths=self.with_paths,
                ansible_vars=self.ansible_vars,
                ansible_tags=self.ansible_tags,
                force_dockerized=self.force_dockerized,
            )

    registered_commands: List[FakeAnsibleCommandArgs] = []

    def __init__(self, dry_run: bool, verbose: bool, ansible_shell_runner_path: str) -> None:

        super().__init__(
            io_utils=None,
            process=None,
            paths=None,
            dry_run=dry_run,
            verbose=verbose,
            ansible_shell_runner_path=ansible_shell_runner_path,
        )
        ctx = Context.create()
        self.json_util = JsonUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool, ansible_shell_runner_path: str) -> "FakeAnsibleRunner":
        ansible_runner = FakeAnsibleRunner(
            dry_run=dry_run, verbose=verbose, ansible_shell_runner_path=ansible_shell_runner_path
        )
        ansible_runner.run_fn = lambda selected_hosts, with_paths, ansible_vars=None, ansible_tags=None, force_dockerized=False: ansible_runner._record_command(
            selected_hosts=selected_hosts,
            with_paths=with_paths,
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags,
            force_dockerized=force_dockerized,
        )
        return ansible_runner

    @staticmethod
    def create(ctx: Context) -> "FakeAnsibleRunner":
        return FakeAnsibleRunner._create_fake(
            dry_run=ctx.is_dry_run(),
            verbose=ctx.is_verbose(),
            ansible_shell_runner_path="/path/to/ansible/shell/runner/ansible.sh",
        )

    def _record_command(
        self,
        selected_hosts: List[AnsibleHost],
        with_paths: AnsibleRunner.WithPaths,
        ansible_vars: List[str],
        ansible_tags: List[str],
        force_dockerized: bool,
    ):
        self.registered_commands.append(
            FakeAnsibleRunner.FakeAnsibleCommandArgs(
                selected_hosts=selected_hosts,
                with_paths=with_paths,
                ansible_vars=ansible_vars,
                ansible_tags=ansible_tags,
                force_dockerized=force_dockerized,
            )
        )

    def assert_command(
        self,
        selected_hosts: List[AnsibleHost],
        with_paths: AnsibleRunner.WithPaths,
        ansible_vars: List[str],
        ansible_tags: List[str],
        force_dockerized: bool,
    ) -> FakeAnsibleCommandArgs:

        cmd_args = FakeAnsibleRunner.FakeAnsibleCommandArgs(
            selected_hosts=selected_hosts,
            with_paths=with_paths,
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags,
            force_dockerized=force_dockerized,
        )
        if cmd_args not in self.registered_commands:
            cmd_args_json = self.json_util.to_json_fn(cmd_args)
            raise FakeEnvironmentAssertionError(
                f"Ansible command was not triggered with expected arguments. args:\n{str(cmd_args_json)}"
            )
        return cmd_args
