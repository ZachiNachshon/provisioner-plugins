#!/usr/bin/env python3


from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.vcs.domain.config import VersionControlConfig

SINGLE_BOARD_PLUGIN_NAME = "single_board_plugin"


class SingleBoardConfig(SerializationBase):
    """
    Configuration structure -

    os:
      raspbian:
        download_path: $HOME/temp/rpi_raspios_image
        active_system: 64bit
        download_url:
          64bit: https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2022-01-28/2022-01-28-raspios-bullseye-arm64-lite.zip
          32bit: https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2022-01-28/2022-01-28-raspios-bullseye-armhf-lite.zi

    network:
      gw_ip_address: 192.168.1.1
      dns_ip_address: 192.168.1.1

    remote: {}
    vcs: {}
    """

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        if "remote" in dict_obj:
            self.remote = RemoteConfig(dict_obj)
        if "vcs" in dict_obj:
            self.vcs = VersionControlConfig(dict_obj)
        if "os" in dict_obj:
            self._parse_os_block(dict_obj["os"])
        if "network" in dict_obj:
            self._parse_network_block(dict_obj["network"])

    def merge(self, other: "SingleBoardConfig") -> SerializationBase:
        if hasattr(other, "remote"):
            self.remote.merge(other.remote)
        if hasattr(other, "vcs"):
            self.vcs.merge(other.vcs)
        if hasattr(other, "os"):
            self.os = self.SingleBoardOsConfig()
            self.os.merge(other.os)
        if hasattr(other, "network"):
            self.network = self.SingleBoardNetworkConfig()
            self.network.merge(other.network)

        return self

    def _parse_os_block(self, os_block: dict):
        self.os = self.SingleBoardOsConfig()
        if "raspbian" in os_block:
            self.os.raspbian = self.SingleBoardOsConfig.SingleBoardOsRaspbianConfig()
            raspbian_block = os_block["raspbian"]
            if "download_path" in raspbian_block:
                self.os.raspbian.download_path = raspbian_block["download_path"]
            if "active_system" in raspbian_block:
                self.os.raspbian.active_system = raspbian_block["active_system"]
            if "download_url" in raspbian_block:
                self.os.raspbian.download_url = self.SingleBoardOsConfig.SingleBoardOsRaspbianConfig.DownloadUrl()
                download_url_block = raspbian_block["download_url"]
                if "url_32bit" in download_url_block:
                    self.os.raspbian.download_url.url_32bit = download_url_block["url_32bit"]
                if "url_64bit" in download_url_block:
                    self.os.raspbian.download_url.url_64bit = download_url_block["url_64bit"]

    def _parse_network_block(self, network_block: dict):
        self.network = self.SingleBoardNetworkConfig()
        if "gw_ip_address" in network_block:
            self.network.gw_ip_address = network_block["gw_ip_address"]
        if "dns_ip_address" in network_block:
            self.network.dns_ip_address = network_block["dns_ip_address"]

    def get_os_raspbian_download_url(self):
        if self.os is None or self.os.raspbian is None or self.os.raspbian.active_system is None:
            return None
        if self.os.raspbian.active_system == "64bit":
            return self.os.raspbian.download_url.url_64bit
        return self.os.raspbian.download_url.url_32bit

    class SingleBoardNetworkConfig:
        gw_ip_address: str
        dns_ip_address: str

        def __init__(self, gw_ip_address: str = None, dns_ip_address: str = None) -> None:
            self.gw_ip_address = gw_ip_address
            self.dns_ip_address = dns_ip_address

        def merge(self, other: "SingleBoardConfig.SingleBoardNetworkConfig") -> SerializationBase:
            if hasattr(other, "gw_ip_address"):
                self.gw_ip_address = other.gw_ip_address
            if hasattr(other, "dns_ip_address"):
                self.dns_ip_address = other.dns_ip_address

            return self

    class SingleBoardOsConfig:
        class SingleBoardOsRaspbianConfig:
            class DownloadUrl:
                def __init__(self, url_32bit: str = None, url_64bit: str = None) -> None:
                    self.url_32bit = url_32bit
                    self.url_64bit = url_64bit

                url_32bit: str
                url_64bit: str

            download_path: str
            active_system: str
            download_url: DownloadUrl

            def __init__(
                self,
                download_path: str = None,
                active_system: str = None,
                download_url: DownloadUrl = None,
            ) -> None:

                self.active_system = active_system
                self.download_url = download_url
                self.download_path = download_path

            def merge(self, other: "SingleBoardConfig.SingleBoardOsConfig.SingleBoardOsRaspbianConfig") -> SerializationBase:
                if hasattr(other, "download_path"):
                    self.download_path = other.download_path
                if hasattr(other, "active_system"):
                    self.active_system = other.active_system
                if hasattr(other, "download_url"):
                    self.download_url = other.download_url

                return self
        
        raspbian: SingleBoardOsRaspbianConfig

        def __init__(self, raspbian: SingleBoardOsRaspbianConfig = None) -> None:
            self.raspbian = raspbian

        def merge(self, other: "SingleBoardConfig.SingleBoardOsConfig") -> SerializationBase:
            if hasattr(other, "raspbian"):
                self.raspbian = SingleBoardConfig.SingleBoardOsConfig.SingleBoardOsRaspbianConfig()
                self.raspbian.merge(other.raspbian)

            return self

    os: SingleBoardOsConfig = None
    network: SingleBoardNetworkConfig = None
    remote: RemoteConfig = None
    vcs: VersionControlConfig = None
