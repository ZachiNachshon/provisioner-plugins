#!/usr/bin/env python3


from provisioner.config.domain.config import ProvisionerConfig
from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.remote.domain.config import RemoteConfig


class SingleBoardConfig(SerializationBase):
    """
    Configuration structure -

    single_board:
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
    anchor: {}
    """
    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        provisioner_data = dict_obj["provisioner"]
        # if "remote" in provisioner_data:
        #     self._parse_remote_block(provisioner_data["remote"])
        # if "anchor" in provisioner_data:
        #     self._parse_anchor_block(provisioner_data["anchor"])
        if "single_board" in provisioner_data:
            self._parse_single_board_block(provisioner_data["single_board"])
    
    def merge(self, other: ProvisionerConfig) -> SerializationBase:
        if other.single_board.os.active_system:
            self.single_board.os.active_system = other.single_board.os.active_system
        if other.single_board.os.download_path:
            self.single_board.os.download_path = other.single_board.os.download_path
        if other.single_board.os.download_url_32bit:
            self.single_board.os.download_url_32bit = other.single_board.os.download_url_32bit
        if other.single_board.os.download_url_64bit:
            self.single_board.os.download_url_64bit = other.single_board.os.download_url_64bit

        if other.single_board.network.gw_ip_address:
            self.single_board.network.gw_ip_address = other.single_board.network.gw_ip_address
        if other.single_board.network.dns_ip_address:
            self.single_board.network.dns_ip_address = other.single_board.network.dns_ip_address

        return self
    
    def _parse_single_board_block(self, single_board_block: dict):
        if "os" in single_board_block:
            os_block = single_board_block["os"]
            if "raspbian" in os_block:
                raspbian_block = os_block["raspbian"]
                if "download_path" in raspbian_block:
                    self.single_board.os.download_path = raspbian_block["download_path"]
                if "active_system" in raspbian_block:
                    self.single_board.os.active_system = raspbian_block["active_system"]
                if "download_url" in raspbian_block:
                    download_url_block = raspbian_block["download_url"]
                    if "32bit" in download_url_block:
                        self.single_board.os.download_url_32bit = download_url_block["32bit"]
                    if "64bit" in download_url_block:
                        self.single_board.os.download_url_64bit = download_url_block["64bit"]

        if "network" in single_board_block:
            network_block = single_board_block["network"]
            if "gw_ip_address" in network_block:
                self.single_board.network.gw_ip_address = network_block["gw_ip_address"]
            if "dns_ip_address" in network_block:
                self.single_board.network.dns_ip_address = network_block["dns_ip_address"]

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
    remote: RemoteConfig = None
    anchor: AnchorConfig = None
