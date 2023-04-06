# #!/usr/bin/env python3

# from typing import List, Optional

# from loguru import logger

# from python_core_lib.errors.cli_errors import (
#     ExternalDependencyFileNotFound,
#     InvalidAnsibleHostPair,
# )
# from python_core_lib.infra.context import Context
# from python_core_lib.utils.io_utils import IOUtils
# from python_core_lib.utils.paths import Paths
# from python_core_lib.utils.process import Process

# # import importlib.resources

# # print("Modules name: " + __name__)
# # print("Modules name: " + __name__)
# # print("Modules name: " + __name__)

# # ANSIBLE_SHELL_RUNNER_PATH = importlib.resources.path(
# #     package="provisioner/external/shell_scripts_lib/runner/ansible",
# #     resource="ansible.sh")

# ANSIBLE_SHELL_RUNNER_PATH = "external/shell_scripts_lib/runner/ansible/ansible.sh"


# class AnsibleHost:
#     host: str
#     ip_address: str
#     username: str
#     password: str
#     ssh_private_key_file_path: str

#     def __init__(
#         self,
#         host: str,
#         ip_address: str,
#         username: str = None,
#         password: Optional[str] = None,
#         ssh_private_key_file_path: Optional[str] = None,
#     ) -> None:

#         self.host = host
#         self.ip_address = ip_address
#         self.username = username
#         self.password = password
#         self.ssh_private_key_file_path = ssh_private_key_file_path

#     @staticmethod
#     def from_dict(ansible_host_dict: dict) -> "AnsibleHost":
#         return AnsibleHost(
#             host=ansible_host_dict["hostname"],
#             ip_address=ansible_host_dict["ip_address"],
#             username=ansible_host_dict["username"] if "username" in ansible_host_dict else None,
#             password=ansible_host_dict["password"] if "password" in ansible_host_dict else None,
#             ssh_private_key_file_path=ansible_host_dict["ssh_private_key_file_path"]
#             if "ssh_private_key_file_path" in ansible_host_dict
#             else None,
#         )


# class AnsibleRunner:
#     class WithPaths:
#         _working_dir: str
#         _playbook_path: str
#         _extra_modules_paths: Optional[List[str]]

#         def __init__(
#             self, working_dir: str, playbook_path: str, extra_modules_paths: Optional[List[str]] = None
#         ) -> None:
#             self._working_dir = working_dir
#             self._playbook_path = playbook_path
#             self._extra_modules_paths = extra_modules_paths

#         def __eq__(self, other):
#             # print("=========== COMPARE ============")
#             # print(f"this: " + str(self.__dict__))
#             # print(f"that: " + str(other.__dict__))
#             if isinstance(other, self.__class__):
#                 return hash(self) == hash(other)
#             return False

#         def __hash__(self):
#             return hash(
#                 (
#                     self._working_dir,
#                     self._playbook_path,
#                     tuple(self._extra_modules_paths),
#                 )
#             )

#         @staticmethod
#         def create(paths: Paths, script_import_name_var, playbook_path: str) -> "AnsibleRunner.WithPaths":
#             return AnsibleRunner.WithPaths(
#                 working_dir=paths.get_path_from_exec_module_root_fn(),
#                 playbook_path=paths.get_path_relative_from_module_root_fn(script_import_name_var, playbook_path),
#                 extra_modules_paths=[paths.get_path_abs_to_module_root_fn(script_import_name_var)],
#             )

#         @staticmethod
#         def create_custom(
#             working_dir: str, playbook_path: str, extra_modules_paths: Optional[List[str]] = None
#         ) -> "AnsibleRunner.WithPaths":
#             return AnsibleRunner.WithPaths(
#                 working_dir=working_dir,
#                 playbook_path=playbook_path,
#                 extra_modules_paths=extra_modules_paths,
#             )

#     _dry_run: bool = None
#     _verbose: bool = None
#     _paths: Paths = None
#     _process: Process = None
#     _io_utils: IOUtils = None
#     _ansible_shell_runner_path: str = None

#     def __init__(
#         self,
#         io_utils: IOUtils,
#         process: Process,
#         paths: Paths,
#         dry_run: bool,
#         verbose: bool,
#         ansible_shell_runner_path: str,
#     ) -> None:

#         self._io_utils = io_utils
#         self._process = process
#         self.paths = paths
#         self._dry_run = dry_run
#         self._verbose = verbose
#         self._ansible_shell_runner_path = ansible_shell_runner_path

#     @staticmethod
#     def create(
#         ctx: Context,
#         io_utils: IOUtils,
#         process: Process,
#         paths: Paths,
#         ansible_shell_runner_path: Optional[str] = ANSIBLE_SHELL_RUNNER_PATH,
#     ) -> "AnsibleRunner":

#         dry_run = ctx.is_dry_run()
#         verbose = ctx.is_verbose()
#         logger.debug(f"Creating Ansible runner (dry_run: {dry_run}, verbose: {verbose})...")
#         return AnsibleRunner(io_utils, process, paths, dry_run, verbose, ansible_shell_runner_path)

#     def _generate_call_parameter_list(self, param_name: str, params: List[str]) -> List[str]:
#         result_list = []
#         if params and len(params) > 0:
#             for param in params:
#                 result_list.append(f"{param_name}: {param}")
#         return result_list

#     def _verify_ansible_runner_script(self):
#         if not self._io_utils.file_exists_fn(file_path=self._ansible_shell_runner_path):
#             err_msg = f"Ansible runner external script not found. path: {self._ansible_shell_runner_path}"
#             logger.error(err_msg)
#             raise ExternalDependencyFileNotFound(err_msg)
#         logger.debug("Ansible runner external script was found")

#     def _prepare_ansible_host_items(self, ansible_hosts: List[AnsibleHost]) -> List[str]:
#         result = []

#         if self._dry_run and len(ansible_hosts) == 0:
#             return result

#         for host in ansible_hosts:
#             if not host.host or not host.ip_address and not self._dry_run:
#                 err_msg = (
#                     f"Ansible selected host is missing a manadatory arguments. host: {host.host}, ip: {host.ip_address}"
#                 )
#                 logger.error(err_msg)
#                 raise InvalidAnsibleHostPair(err_msg)

#             # Do not append 'ansible_host=' prefix for local connection
#             if "ansible_connection=local" in host.ip_address:
#                 result.append(f"{host.host} {host.ip_address}")
#             else:
#                 host_entry = f"{host.host} ansible_host={host.ip_address} ansible_user={host.username}"
#                 if host.password:
#                     # k8s-master ansible_host=1.1.1.1 ansible_user=user1 ansible_password=password1
#                     host_entry += f" ansible_password={host.password}"
#                 if host.ssh_private_key_file_path:
#                     # k8s-node1 ansible_host=1.1.1.2 ansible_user=user2 ansible_private_key_file=~/.ssh/rsa_key
#                     host_entry += f" ansible_private_key_file={host.ssh_private_key_file_path}"
#                 result.append(host_entry)

#         return result

#     def _run(
#         self,
#         selected_hosts: List[AnsibleHost],
#         with_paths: WithPaths,
#         ansible_vars: Optional[List[str]] = None,
#         ansible_tags: Optional[List[str]] = None,
#         force_dockerized: Optional[bool] = False,
#     ) -> str:
#         """
#         Call the ansible shell runner to trigger an ansible playbook.
#         Selected hosts are pairs of (hostname ip_address)
#         For additional information please refer to the file located at
#         ANSIBLE_SHELL_RUNNER_PATH
#         """
#         if not self._dry_run:
#             self._verify_ansible_runner_script()

#         ansible_hosts_list = self._prepare_ansible_host_items(selected_hosts)
#         selected_hosts_items_list = self._generate_call_parameter_list("selected_host", ansible_hosts_list)
#         ansible_vars_items_list = self._generate_call_parameter_list("ansible_var", ansible_vars)
#         ansible_tags_items_list = self._generate_call_parameter_list("ansible_tag", ansible_tags)
#         extra_modules_paths_items_list = self._generate_call_parameter_list(
#             "extra_module_path", with_paths._extra_modules_paths
#         )

#         run_cmd = [
#             "bash",
#             f"{self._ansible_shell_runner_path}",
#             f"working_dir: {with_paths._working_dir}",
#             f"playbook_path: {with_paths._playbook_path}",
#         ]

#         if len(selected_hosts_items_list) > 0:
#             run_cmd += selected_hosts_items_list
#         if len(ansible_vars_items_list) > 0:
#             run_cmd += ansible_vars_items_list
#         if len(ansible_tags_items_list) > 0:
#             run_cmd += ansible_tags_items_list
#         if len(extra_modules_paths_items_list) > 0:
#             run_cmd += extra_modules_paths_items_list

#         if force_dockerized:
#             run_cmd.append("--force-dockerized")
#         if self._dry_run:
#             run_cmd.append("--dry-run")
#         if self._verbose:
#             run_cmd.append("--verbose")

#         return self._process.run_fn(args=run_cmd)

#     run_fn = _run
