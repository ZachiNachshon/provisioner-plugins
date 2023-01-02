#!/usr/bin/env python3

import threading
from typing import Any, Callable
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible import AnsibleRunner
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.github import GitHub
from python_core_lib.utils.hosts_file import HostsFile
from python_core_lib.utils.httpclient import HttpClient
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.network import NetworkUtil
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.process import Process
from python_core_lib.utils.progress_indicator import ProgressIndicator
from python_core_lib.utils.prompter import Prompter
from python_core_lib.utils.summary import Summary

class CoreCollaborators:
    io: IOUtils
    checks: Checks
    json_util: JsonUtil
    summary: Summary
    prompter: Prompter
    printer: Printer
    process: Process
    ansible_runner: AnsibleRunner
    network_util: NetworkUtil
    github: GitHub
    hosts_file: HostsFile

    ctx: Context = None

    def __init__(self, ctx: Context) -> None:
        self._lock = threading.Lock()
        self.ctx = ctx

    def _lock_and_get(self, item: Any, callback: Callable) -> Any:
        if not item:
            with self._lock:
                return callback()
        return item

    def get_io_utils(self) -> IOUtils:
        return self._lock_and_get(self.io, IOUtils.create(self.ctx))

    def get_checks(self) -> Checks:
        return self._lock_and_get(self.checks, Checks.create(self.ctx))

    def get_json_util(self) -> JsonUtil:
        return self._lock_and_get(self.json_util, JsonUtil.create(self.ctx, self.get_io_utils()))

    def get_process(self) -> Process:
        return self._lock_and_get(self.process, Process.create(self.ctx))

    def get_printer(self) -> Printer:
        return self._lock_and_get(self.printer, Printer.create(self.ctx, ProgressIndicator.create(self.ctx, self.get_io_utils())))

    def get_prompter(self) -> Prompter:
        return self._lock_and_get(self.prompter, Prompter.create(self.ctx))

    def get_ansible_runner(self) -> AnsibleRunner:
        return self._lock_and_get(self.ansible_runner, AnsibleRunner.create(self.ctx, self.get_io_utils(), self.get_process()))

    def get_network_util(self) -> NetworkUtil:
        return self._lock_and_get(self.network_util, NetworkUtil.create(self.ctx, self.get_printer()))

    def get_github(self) -> GitHub:
        return self._lock_and_get(self.github, GitHub.create(self.ctx, HttpClient.create(self.ctx, io_utils=self.get_io_utils(), printer=self.get_printer())))

    def get_summary(self) -> Summary:
        return self._lock_and_get(self.summary, Summary.create(self.ctx, self.get_json_util(), self.get_printer(), self.get_prompter()))

    def get_hosts_file(self) -> HostsFile:
        return self._lock_and_get(self.hosts_file, HostsFile.create(self.ctx, self.get_process()))

