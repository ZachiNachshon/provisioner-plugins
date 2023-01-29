#!/usr/bin/env python3

from provisioner_single_board_plugin.config.domain.config import RpiConfig


class TestDataSingleBoardConfig:
    TEST_DATA_ACTIVE_SYSTEM = "64bit"
    TEST_DATA_DOWNLOAD_URL_32BIT = "https://test-data-download-url-32bit.com"
    TEST_DATA_DOWNLOAD_URL_64BIT = "https://test-data-download-url-64bit.com"
    TEST_DATA_DOWNLOAD_PATH = "/test/path/to/download/os/image"
    TEST_DATA_GW_IP_ADDRESS = "1.1.1.1"
    TEST_DATA_DNS_IP_ADDRESS = "2.2.2.2"

    @staticmethod
    def create_fake_rpi_config() -> RpiConfig:
        return RpiConfig(
            os=RpiConfig.RpiOsConfig(
                active_system=TestDataSingleBoardConfig.TEST_DATA_ACTIVE_SYSTEM,
                download_url_32bit=TestDataSingleBoardConfig.TEST_DATA_DOWNLOAD_URL_32BIT,
                download_url_64bit=TestDataSingleBoardConfig.TEST_DATA_DOWNLOAD_URL_64BIT,
                download_path=TestDataSingleBoardConfig.TEST_DATA_DOWNLOAD_PATH,
            ),
            network=RpiConfig.RpiNetworkConfig(
                gw_ip_address=TestDataSingleBoardConfig.TEST_DATA_GW_IP_ADDRESS,
                dns_ip_address=TestDataSingleBoardConfig.TEST_DATA_DNS_IP_ADDRESS,
            ),
        )
