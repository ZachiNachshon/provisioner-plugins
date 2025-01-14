#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_single_board_plugin.src.raspberry_pi.os.burn_image_cmd import (
    RPiOsBurnImageCmd,
    RPiOsBurnImageCmdArgs,
)

from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv

ARG_IMAGE_DOWNLOAD_URL = "https://test-image-download-url.com"
ARG_IMAGE_DOWNLOAD_PATH = "/test/image/download/path"

IMAGE_BURNER_COMMAND_RUNNER_PATH = "provisioner_shared.components.sd_card.image_burner.ImageBurnerCmdRunner"


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/os/burn_image_cmd_test.py
#
class RPiOsInstallTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_burn_image_cmd_args(self) -> RPiOsBurnImageCmdArgs:
        return RPiOsBurnImageCmdArgs(
            image_download_url=ARG_IMAGE_DOWNLOAD_URL, image_download_path=ARG_IMAGE_DOWNLOAD_PATH
        )

    @mock.patch(f"{IMAGE_BURNER_COMMAND_RUNNER_PATH}.run")
    def test_burn_os_raspbian_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        fake_cmd_args = self.create_fake_burn_image_cmd_args()

        RPiOsBurnImageCmd().run(ctx=self.env.get_context(), args=fake_cmd_args)

        def assertion_callback(args):
            print(args.__dict__)
            self.assertEqual(args.image_download_url, fake_cmd_args.image_download_url)
            self.assertEqual(args.image_download_path, fake_cmd_args.image_download_path)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=self.env.get_context())
