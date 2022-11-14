#!/usr/bin/env python3


class RemoteConfig:
    class Host:
        name: str
        address: str

        def __init__(self, name: str, address: str) -> None:
            self.name = name
            self.address = address

    class LanScan:
        ip_discovery_range: str = None

    class Auth:
        node_username: str = None
        node_password: str = None
        ssh_private_key_file_path: str = None

    lan_scan: LanScan = LanScan()
    auth: Auth = Auth()
    hosts: dict[str, Host] = None
