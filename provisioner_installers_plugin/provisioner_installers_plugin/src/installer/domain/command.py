#!/usr/bin/env python3


from enum import Enum


class InstallerSubCommandName(str, Enum):
    CLI = "cli"
    K8S = "k8s"
    System = "system"
