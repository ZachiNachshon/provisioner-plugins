#!/usr/bin/env python3


from enum import Enum


class InstallerSubCommandName(str, Enum):
    CLI = "cli"
    K3S = "k3s"
