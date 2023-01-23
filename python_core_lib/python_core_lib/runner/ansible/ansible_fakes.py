#!/usr/bin/env python3

from typing import List, Optional
from python_core_lib.errors.cli_errors import FakeEnvironmentAssertionError

from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible import AnsibleRunner, HostIpPair
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.json_util import JsonUtil

class FakeAnsibleRunner(AnsibleRunner):

    # Used to serialize objects to string for assertion error logs
    json_util: JsonUtil = None

    @staticmethod
    def calculate_hash( 
        working_dir: str,
        username: str,
        selected_hosts: List[HostIpPair],
        playbook_path: str,
        password: str,
        ssh_private_key_file_path: str,
        ansible_vars: List[str],
        ansible_tags: List[str],
        extra_modules_paths: List[str],
        force_dockerized: bool) -> str:
        return hash((
                working_dir, 
                username, 
                str(selected_hosts), 
                playbook_path,
                password,
                ssh_private_key_file_path,
                str(ansible_vars),
                str(ansible_tags),
                str(extra_modules_paths),
                force_dockerized,
                ))

    class FakeAnsibleCommandArgs:
        working_dir: str
        username: str
        selected_hosts: List[HostIpPair]
        playbook_path: str
        password: str
        ssh_private_key_file_path: str
        ansible_vars: List[str]
        ansible_tags: List[str]
        extra_modules_paths: List[str]
        force_dockerized: bool

        def __init__(self,
            working_dir: str,
            username: str,
            selected_hosts: List[HostIpPair],
            playbook_path: str,
            password: Optional[str] = None,
            ssh_private_key_file_path: Optional[str] = None,
            ansible_vars: Optional[List[str]] = None,
            ansible_tags: Optional[List[str]] = None,
            extra_modules_paths: Optional[List[str]] = None,
            force_dockerized: Optional[bool] = False) -> None:

            self.working_dir = working_dir
            self.username = username
            self.selected_hosts = selected_hosts
            self.playbook_path = playbook_path
            self.password = password
            self.ssh_private_key_file_path = ssh_private_key_file_path
            self.ansible_vars = ansible_vars
            self.ansible_tags = ansible_tags
            self.extra_modules_paths = extra_modules_paths
            self.force_dockerized = force_dockerized

        def __eq__(self, other):
            # print("=========== COMPARE ============")
            # print("this: " + str(self.__dict__))
            # print("that: " + str(other.__dict__))
            if isinstance(other, FakeAnsibleRunner.FakeAnsibleCommandArgs):
                return hash(self) == hash(other)
            return False

        def __hash__(self):
            return FakeAnsibleRunner.calculate_hash(
                self.working_dir, self.username, self.selected_hosts, self.playbook_path, 
                self.password, self.ssh_private_key_file_path, self.ansible_vars,
                self.ansible_tags, self.extra_modules_paths, self.force_dockerized 
            )

    registered_commands: List[FakeAnsibleCommandArgs] = []

    def __init__(
        self, dry_run: bool, verbose: bool, ansible_shell_runner_path: str
    ) -> None:

        super().__init__(
            io_utils=None,
            process=None,
            dry_run=dry_run,
            verbose=verbose,
            ansible_shell_runner_path=ansible_shell_runner_path,
        )
        ctx = Context.create()
        self.json_util = JsonUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))

    @staticmethod
    def _create_fake(dry_run: bool, verbose: bool, ansible_shell_runner_path: str) -> "FakeAnsibleRunner":
        ansible_runner = FakeAnsibleRunner(dry_run=dry_run, verbose=verbose, ansible_shell_runner_path=ansible_shell_runner_path)
        ansible_runner.run_fn = lambda working_dir, username, selected_hosts, playbook_path, password=None, ssh_private_key_file_path=None, ansible_vars=None, ansible_tags=None, extra_modules_paths=None, force_dockerized=False: ansible_runner._record_command(
            working_dir=working_dir, 
            username=username, 
            selected_hosts=selected_hosts, 
            playbook_path=playbook_path, 
            password=password, 
            ssh_private_key_file_path=ssh_private_key_file_path, 
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags, 
            extra_modules_paths=extra_modules_paths,
            force_dockerized=force_dockerized  
        )
        return ansible_runner

    @staticmethod
    def create(ctx: Context) -> "FakeAnsibleRunner":
        return FakeAnsibleRunner._create_fake(
            dry_run=ctx.is_dry_run(),
            verbose=ctx.is_verbose(),
            ansible_shell_runner_path="/path/to/ansible/shell/runner/ansible.sh",
        )

    def _record_command(self, 
        working_dir: str,
        username: str,
        selected_hosts: List[HostIpPair],
        playbook_path: str,
        password: str,
        ssh_private_key_file_path: str,
        ansible_vars: List[str],
        ansible_tags: List[str],
        extra_modules_paths: List[str],
        force_dockerized: bool):

        self.registered_commands.append(FakeAnsibleRunner.FakeAnsibleCommandArgs(
            working_dir=working_dir, 
            username=username, 
            selected_hosts=selected_hosts, 
            playbook_path=playbook_path, 
            password=password, 
            ssh_private_key_file_path=ssh_private_key_file_path, 
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags, 
            extra_modules_paths=extra_modules_paths,
            force_dockerized=force_dockerized  
            )
        )

    def assert_command(
        self, 
        working_dir: str,
        username: str,
        selected_hosts: List[HostIpPair],
        playbook_path: str,
        password: str,
        ssh_private_key_file_path: str,
        ansible_vars: List[str],
        ansible_tags: List[str],
        extra_modules_paths: List[str],
        force_dockerized: bool) -> FakeAnsibleCommandArgs:

        cmd_args = FakeAnsibleRunner.FakeAnsibleCommandArgs(
            working_dir=working_dir, 
            username=username, 
            selected_hosts=selected_hosts, 
            playbook_path=playbook_path, 
            password=password, 
            ssh_private_key_file_path=ssh_private_key_file_path, 
            ansible_vars=ansible_vars,
            ansible_tags=ansible_tags, 
            extra_modules_paths=extra_modules_paths,
            force_dockerized=force_dockerized  
            )
        if cmd_args not in self.registered_commands:
            cmd_args_json = self.json_util.to_json_fn(cmd_args)
            raise FakeEnvironmentAssertionError(f"Ansible command was not triggered with expected arguments. args:\n{str(cmd_args_json)}")
        return cmd_args
