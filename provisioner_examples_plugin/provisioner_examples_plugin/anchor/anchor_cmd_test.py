#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.infra.context import Context
from python_core_lib.utils.os import MAC_OS, OsArch

from provisioner_examples_plugin.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_examples_plugin/anchor/anchor_cmd_test.py
#
class AnchorCmdTestShould(unittest.TestCase):
    @mock.patch("provisioner_features_lib.anchor.anchor_runner.AnchorCmdRunner.run")
    def test_burn_os_raspbian_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        download_url = "https://burn-image-test-custom.com"
        download_path = "/test/download/path"

        args = AnchorCmdArgs(image_download_url=download_url, image_download_path=download_path)
        runner = AnchorCmd()
        runner.run(ctx=ctx, args=args)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        img_burner_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(download_url, img_burner_call_args.image_download_url)
        self.assertEqual(download_path, img_burner_call_args.image_download_path)
