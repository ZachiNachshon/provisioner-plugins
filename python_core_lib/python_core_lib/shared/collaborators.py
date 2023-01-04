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

    def __init__(self, ctx: Context) -> None:
        # self.__lock = threading.Lock()
        self.__ctx: Context = ctx
        self.__io: IOUtils = None
        self.__checks: Checks = None
        self.__json_util: JsonUtil = None
        self.__summary: Summary = None
        self.__prompter: Prompter = None
        self.__printer: Printer = None
        self.__process: Process = None
        self.__ansible_runner: AnsibleRunner = None
        self.__network_util: NetworkUtil = None
        self.__github: GitHub = None
        self.__hosts_file: HostsFile = None
        self.__http_client: HttpClient = None

    def _lock_and_get(self, item: Any, callback: Callable) -> Any:
        self.__lock = threading.Lock()
        with self.__lock:
            if not item:
                return callback()
        return item

    def io_utils(self) -> IOUtils:
        return self._lock_and_get(self.__io, lambda: IOUtils.create(self.__ctx))

    def checks(self) -> Checks:
        return self._lock_and_get(self.__checks, lambda: Checks.create(self.__ctx))

    def json_util(self) -> JsonUtil:
        return self._lock_and_get(self.__json_util, lambda: JsonUtil.create(self.__ctx, self.io_utils()))

    def process(self) -> Process:
        return self._lock_and_get(self.__process, lambda: Process.create(self.__ctx))

    def printer(self) -> Printer:
        return self._lock_and_get(self.__printer, lambda: Printer.create(self.__ctx, ProgressIndicator.create(self.__ctx, self.io_utils())))

    def prompter(self) -> Prompter:
        return self._lock_and_get(self.__prompter, lambda: Prompter.create(self.__ctx))

    def ansible_runner(self) -> AnsibleRunner:
        return self._lock_and_get(self.__ansible_runner, lambda: AnsibleRunner.create(self.__ctx, self.io_utils(), self.process()))

    def network_util(self) -> NetworkUtil:
        return self._lock_and_get(self.__network_util, lambda: NetworkUtil.create(self.__ctx, self.printer()))

    def github(self) -> GitHub:
        return self._lock_and_get(self.__github, lambda: GitHub.create(self.__ctx, self.http_client()))

    def summary(self) -> Summary:
        return self._lock_and_get(self.__summary, lambda: Summary.create(self.__ctx, self.json_util(), self.printer(), self.prompter()))

    def hosts_file(self) -> HostsFile:
        return self._lock_and_get(self.__hosts_file, lambda: HostsFile.create(self.__ctx, self.process()))

    def http_client(self) -> HttpClient:
        return self._lock_and_get(self.__http_client, lambda: HttpClient.create(self.__ctx, io_utils=self.io_utils(), printer=self.printer()))
