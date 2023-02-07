#!/usr/bin/env python3


class SingleBoardConfig:
    def get_os_raspbian_download_url(self):
        if self.os.active_system == "64bit":
            return self.os.download_url_64bit
        return self.os.download_url_32bit

    class SingleBoardOsConfig:
        active_system: str
        download_url_32bit: str
        download_url_64bit: str
        download_path: str

        def __init__(
            self,
            active_system: str = None,
            download_url_32bit: str = None,
            download_url_64bit: str = None,
            download_path: str = None,
        ) -> None:

            self.active_system = active_system
            self.download_url_32bit = download_url_32bit
            self.download_url_64bit = download_url_64bit
            self.download_path = download_path

    class SingleBoardNetworkConfig:
        gw_ip_address: str
        dns_ip_address: str

        def __init__(self, gw_ip_address: str = None, dns_ip_address: str = None) -> None:
            self.gw_ip_address = gw_ip_address
            self.dns_ip_address = dns_ip_address

    def __init__(
        self,
        os: SingleBoardOsConfig = SingleBoardOsConfig(),
        network: SingleBoardNetworkConfig = SingleBoardNetworkConfig(),
    ) -> None:

        self.os = os
        self.network = network

    os: SingleBoardOsConfig = None
    network: SingleBoardNetworkConfig = None
