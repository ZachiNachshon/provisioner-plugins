#!/usr/bin/env python3

import os
import unittest

from provisioner_single_board_plugin.src.config.domain.config import SingleBoardConfig

from provisioner_shared.components.runtime.errors.cli_errors import FailedToSerializeConfiguration
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.utils.io_utils import IOUtils
from provisioner_shared.components.runtime.utils.yaml_util import YamlUtil


# To run as a single test target:
#  ./run.sh provisioner_single_board_plugin/src/config/domain/config_test.py
#
class SingleBoardConfigTestShould(unittest.TestCase):

    def test_config_partial_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
remote:
  hosts:
    - name: test-node
      address: 1.1.1.1
      auth:
        username: pi
        password: raspberry
        ssh_private_key_file_path: /path/to/unknown
  lan_scan:
    ip_discovery_range: 192.168.1.1/24

os:
  raspbian:
    active_system: 64bit
    download_url:
      url_64bit: http://download-url-64-bit.com
      url_32bit: http://download-url-32-bit.com
"""
        internal_config_obj = yaml_util.read_string_fn(yaml_str=internal_yaml_str, cls=SingleBoardConfig)
        print("--- INTERNAL ---")
        print(internal_config_obj.remote.hosts[0].__dict__)
        user_yaml_str = """
remote:
  hosts:
    - name: test-node
      address: 2.2.2.2
      auth:
        username: test-user
        ssh_private_key_file_path: /test/path

os:
  raspbian:
    active_system: 32bit
    download_url:
      url_32bit: http://download-url-32-bit-test-path.com
"""
        user_config_obj = yaml_util.read_string_fn(yaml_str=user_yaml_str, cls=SingleBoardConfig)
        print("--- USER ---")
        print(user_config_obj.remote.hosts[0].__dict__)
        merged_config_obj = internal_config_obj.merge(user_config_obj)
        print("--- MERGED ---")
        print(merged_config_obj.remote.hosts[0].__dict__)

        self.assertEqual(len(merged_config_obj.remote.hosts), 1)
        self.assertEqual(merged_config_obj.remote.hosts[0].name, "test-node")
        self.assertEqual(merged_config_obj.remote.hosts[0].address, "2.2.2.2")
        self.assertEqual(merged_config_obj.remote.hosts[0].auth.username, "test-user")
        self.assertIsNotNone(merged_config_obj.remote.hosts[0].auth.password)
        self.assertEqual(merged_config_obj.remote.hosts[0].auth.ssh_private_key_file_path, "/test/path")

        self.assertEqual(merged_config_obj.remote.lan_scan.ip_discovery_range, "192.168.1.1/24")

        self.assertEqual(merged_config_obj.os.raspbian.active_system, "32bit")
        self.assertEqual(
            merged_config_obj.os.raspbian.download_url.url_32bit, "http://download-url-32-bit-test-path.com"
        )
        self.assertEqual(merged_config_obj.os.raspbian.download_url.url_64bit, "http://download-url-64-bit.com")

    def test_config_full_merge_with_user_config(self):
        ctx = Context.create()
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
os:
  raspbian:
    active_system: 64bit
    download_path: $HOME/temp/rpi_raspios_image
    download_url:
      url_64bit: http://download-url-64-bit.com
      url_32bit: http://download-url-32-bit.com

network:
  gw_ip_address: 192.168.1.1
  dns_ip_address: 192.168.1.1
"""
        internal_config_obj: SingleBoardConfig = yaml_util.read_string_fn(
            yaml_str=internal_yaml_str, cls=SingleBoardConfig
        )

        user_yaml_str = """
os:
  raspbian:
    active_system: 32bit
    download_path: $HOME/temp/rpi_raspios_image_user
    download_url:
      url_64bit: http://download-url-64-bit-user.com
      url_32bit: http://download-url-32-bit-user.com

network:
  gw_ip_address: 1.1.1.1
  dns_ip_address: 2.2.2.2
"""
        user_config_obj: SingleBoardConfig = yaml_util.read_string_fn(yaml_str=user_yaml_str, cls=SingleBoardConfig)
        merged_config_obj: SingleBoardConfig = internal_config_obj.merge(user_config_obj)

        self.assertEqual(merged_config_obj.os.raspbian.active_system, "32bit")
        self.assertEqual(
            merged_config_obj.os.raspbian.download_path, os.path.expanduser("~/temp/rpi_raspios_image_user")
        )
        self.assertEqual(merged_config_obj.os.raspbian.download_url.url_32bit, "http://download-url-32-bit-user.com")
        self.assertEqual(merged_config_obj.os.raspbian.download_url.url_64bit, "http://download-url-64-bit-user.com")

        self.assertEqual(merged_config_obj.network.gw_ip_address, "1.1.1.1")
        self.assertEqual(merged_config_obj.network.dns_ip_address, "2.2.2.2")

    def test_read_os_raspi_download_url(self):
        ctx = Context.create()
        ctx._verbose = True
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        internal_yaml_str = """
os:
  raspbian:
    active_system: 32bit
    download_url:
      url_64bit: http://download-url-64-bit.com
      url_32bit: http://download-url-32-bit.com
"""
        internal_config_obj: SingleBoardConfig = yaml_util.read_string_fn(
            yaml_str=internal_yaml_str, cls=SingleBoardConfig
        )
        internal_config_obj.get_os_raspbian_download_url()
        self.assertEqual(internal_config_obj.get_os_raspbian_download_url(), "http://download-url-32-bit.com")

    # Config classes are validated before entried are added. This test can fail only if there will be an invalid
    # assignment in the config class i.e. dict["bad_key"] = "bad_value"
    @unittest.SkipTest
    def test_config_fail_on_invalid_user_config(self):
        ctx = Context.create()
        # ctx._verbose = True
        yaml_util = YamlUtil.create(ctx=ctx, io_utils=IOUtils.create(ctx))
        user_yaml_str = """
bad_key:
  bad_value: bad
"""
        with self.assertRaises(FailedToSerializeConfiguration):
            yaml_util.read_string_fn(yaml_str=user_yaml_str, cls=SingleBoardConfig)
