#!/usr/bin/env python3


from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.vcs.domain.config import VersionControlConfig

SINGLE_BOARD_PLUGIN_NAME = "single_board_plugin"

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


class DownloadUrl(SerializationBase):
    url_32bit: str = ""
    url_64bit: str = ""

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "DownloadUrl") -> SerializationBase:
        if hasattr(other, "url_32bit") and len(other.url_32bit) > 0:
            self.url_32bit = other.url_32bit
        if hasattr(other, "url_64bit") and len(other.url_64bit) > 0:
            self.url_64bit = other.url_64bit
        return self

    def _try_parse_config(self, dict_obj: dict):
        if "url_32bit" in dict_obj:
            self.url_32bit = dict_obj["url_32bit"]
        if "url_64bit" in dict_obj:
            self.url_64bit = dict_obj["url_64bit"]


class SingleBoardOsRaspbianConfig(SerializationBase):
    download_path: str = ""
    active_system: str = ""
    download_url: DownloadUrl = DownloadUrl({})

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "SingleBoardOsRaspbianConfig") -> SerializationBase:
        if hasattr(other, "download_path") and len(other.download_path) > 0:
            self.download_path = other.download_path
        if hasattr(other, "active_system") and len(other.active_system) > 0:
            self.active_system = other.active_system
        if hasattr(other, "download_url"):
            self.download_url = self.download_url if self.download_url is not None else DownloadUrl()
            self.download_url.merge(other.download_url)

    def _try_parse_config(self, dict_obj: dict):
        if "download_path" in dict_obj:
            self.download_path = dict_obj["download_path"]
        if "active_system" in dict_obj:
            self.active_system = dict_obj["active_system"]
        if "download_url" in dict_obj:
            self.download_url = DownloadUrl(dict_obj["download_url"])


class SingleBoardOsConfig(SerializationBase):
    raspbian: SingleBoardOsRaspbianConfig = SingleBoardOsRaspbianConfig({})

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "SingleBoardOsConfig") -> SerializationBase:
        if hasattr(other, "raspbian"):
            self.raspbian = self.raspbian if self.raspbian is not None else SingleBoardOsRaspbianConfig()
            self.raspbian.merge(other.raspbian)

    def _try_parse_config(self, dict_obj: dict):
        if "raspbian" in dict_obj:
            self.raspbian = SingleBoardOsRaspbianConfig(dict_obj["raspbian"])


class SingleBoardNetworkConfig(SerializationBase):
    gw_ip_address: str = ""
    dns_ip_address: str = ""

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "SingleBoardNetworkConfig") -> SerializationBase:
        if hasattr(other, "gw_ip_address") and len(other.gw_ip_address) > 0:
            self.gw_ip_address = other.gw_ip_address
        if hasattr(other, "dns_ip_address") and len(other.dns_ip_address) > 0:
            self.dns_ip_address = other.dns_ip_address

    def _try_parse_config(self, dict_obj: dict):
        if "gw_ip_address" in dict_obj:
            self.gw_ip_address = dict_obj["gw_ip_address"]
        if "dns_ip_address" in dict_obj:
            self.dns_ip_address = dict_obj["dns_ip_address"]


class SingleBoardConfig(SerializationBase):
    os: SingleBoardOsConfig = SingleBoardOsConfig({})
    network: SingleBoardNetworkConfig = SingleBoardNetworkConfig({})
    remote: RemoteConfig = RemoteConfig({})
    vcs: VersionControlConfig = VersionControlConfig({})

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def merge(self, other: "SingleBoardConfig") -> SerializationBase:
        if hasattr(other, "remote"):
            self.remote.merge(other.remote)
        if hasattr(other, "vcs"):
            self.vcs.merge(other.vcs)
        if hasattr(other, "os"):
            self.os = self.os if self.os is not None else SingleBoardOsConfig()
            self.os.merge(other.os)
        if hasattr(other, "network"):
            self.network = self.network if self.network is not None else SingleBoardNetworkConfig()
            self.network.merge(other.network)

        return self

    def _try_parse_config(self, dict_obj: dict) -> None:
        if "remote" in dict_obj:
            self.remote = RemoteConfig(dict_obj["remote"])
        if "vcs" in dict_obj:
            self.vcs = VersionControlConfig(dict_obj["vcs"])
        if "os" in dict_obj:
            self.os = SingleBoardOsConfig(dict_obj["os"])
        if "network" in dict_obj:
            self.network = SingleBoardNetworkConfig(dict_obj["network"])

    def get_os_raspbian_download_url(self):
        if self.os is None or self.os.raspbian is None or self.os.raspbian.active_system is None:
            return None
        if self.os.raspbian.active_system == "64bit":
            return self.os.raspbian.download_url.url_64bit
        return self.os.raspbian.download_url.url_32bit
