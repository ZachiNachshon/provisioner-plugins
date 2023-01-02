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
    __io: IOUtils
    __checks: Checks
    __json_util: JsonUtil
    __summary: Summary
    __prompter: Prompter
    __printer: Printer
    __process: Process
    __ansible_runner: AnsibleRunner
    __network_util: NetworkUtil
    __github: GitHub
    __hosts_file: HostsFile
    __http_client: HttpClient

    __ctx: Context = None

    def __init__(self, ctx: Context) -> None:
        self.__lock = threading.Lock()
        self.__ctx = ctx

    def _lock_and_get(self, item: Any, callback: Callable) -> Any:
        if not item:
            with self.__lock:
                return callback()
        return item

    def io_utils(self) -> IOUtils:
        return self._lock_and_get(self.__io, IOUtils.create(self.__ctx))

    def checks(self) -> Checks:
        return self._lock_and_get(self.__checks, Checks.create(self.__ctx))

    def json_util(self) -> JsonUtil:
        return self._lock_and_get(self.__json_util, JsonUtil.create(self.__ctx, self.io_utils()))

    def process(self) -> Process:
        return self._lock_and_get(self.__process, Process.create(self.__ctx))

    def printer(self) -> Printer:
        return self._lock_and_get(self.__printer, Printer.create(self.__ctx, ProgressIndicator.create(self.__ctx, self.io_utils())))

    def prompter(self) -> Prompter:
        return self._lock_and_get(self.__prompter, Prompter.create(self.__ctx))

    def ansible_runner(self) -> AnsibleRunner:
        return self._lock_and_get(self.__ansible_runner, AnsibleRunner.create(self.__ctx, self.io_utils(), self.process()))

    def network_util(self) -> NetworkUtil:
        return self._lock_and_get(self.__network_util, NetworkUtil.create(self.__ctx, self.printer()))

    def github(self) -> GitHub:
        return self._lock_and_get(self.__github, GitHub.create(self.__ctx, self.http_client()))

    def summary(self) -> Summary:
        return self._lock_and_get(self.__summary, Summary.create(self.__ctx, self.json_util(), self.printer(), self.prompter()))

    def hosts_file(self) -> HostsFile:
        return self._lock_and_get(self.__hosts_file, HostsFile.create(self.__ctx, self.process()))

    def http_client(self) -> HttpClient:
        return self._lock_and_get(self.__http_client, HttpClient.create(self.__ctx, io_utils=self.io_utils(), printer=self.printer()))
