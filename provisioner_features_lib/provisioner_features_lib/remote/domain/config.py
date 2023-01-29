#!/usr/bin/env python3

from enum import Enum


class RunEnvironment(str, Enum):
    Local = "Local"
    Remote = "Remote"


class RemoteConfig:
    """
    Configuration structure -

    remote:
        hosts:
        - name: kmaster
            address: 192.168.1.200
        - name: knode1
            address: 192.168.1.201

        lan_scan:
            ip_discovery_range: 192.168.1.1/24

        auth:
            username: pi
            password: raspberry
            ssh_private_key_file_path: /path/to/unknown
    """

    class Host:
        name: str
        address: str

        def __init__(self, name: str, address: str) -> None:
            self.name = name
            self.address = address

    class LanScan:
        ip_discovery_range: str = None

        def __init__(self, ip_discovery_range: str = None) -> None:
            self.ip_discovery_range = ip_discovery_range

    class Auth:
        node_username: str = None
        node_password: str = None
        ssh_private_key_file_path: str = None

        def __init__(self, node_username: str = None, node_password: str = None, ssh_private_key_file_path: str = None) -> None:
            self.node_username = node_username
            self.node_password = node_password
            self.ssh_private_key_file_path = ssh_private_key_file_path

    def __init__(self, lan_scan: LanScan = LanScan(), auth: Auth = Auth(), hosts: dict[str, Host] = None) -> None:
        self.lan_scan = lan_scan
        self.auth = auth
        self.hosts = hosts

    lan_scan: LanScan = None
    auth: Auth = None
    hosts: dict[str, Host] = None
