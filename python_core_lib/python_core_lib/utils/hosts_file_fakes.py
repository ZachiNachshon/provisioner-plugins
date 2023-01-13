#!/usr/bin/env python3

from python_core_lib.infra.context import Context
from python_core_lib.utils.hosts_file import HostsFile
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.process import Process


class FakeHostsFile(HostsFile):

    def __init__(self, process: Process, dry_run: bool, verbose: bool):
        super().__init__(process=process, dry_run=dry_run, verbose=verbose)
        self.registered_urls = {}
        self.registered_download_files = {}

    @staticmethod
    def _create_fake(process: Process, dry_run: bool, verbose: bool) -> "FakeHostsFile":
        hosts_file = FakeHostsFile(process=process, dry_run=dry_run, verbose=verbose)
        hosts_file.add_entry_fn = lambda ip_address, dns_names, comment=None, entry_type="ipv4": None
        return hosts_file

    @staticmethod
    def create(ctx: Context, process: Process) -> "FakeHostsFile":
        return FakeHostsFile._create_fake(
            process=process, dry_run=ctx.is_dry_run(), verbose=ctx.is_verbose()
        )
