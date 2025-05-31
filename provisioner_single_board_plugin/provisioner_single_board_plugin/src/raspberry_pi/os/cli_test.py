#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_single_board_plugin.main_fake import get_fake_app

from provisioner_shared.components.runtime.errors.cli_errors import (
    StepEvaluationFailure,
)
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner
from provisioner_shared.test_lib.test_env import TestEnv

ARG_IMAGE_DOWNLOAD_URL = "http://test.image.download.url.com"

AUTO_PROMPT_RESPONSE = "DRY_RUN_RESPONSE"
RPI_OS_MODULE_PATH = "provisioner_single_board_plugin.src.raspberry_pi.os"

STEP_ERROR_OUTPUT = "This is a sample step error output for a test expected to fail"


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/os/cli_test.py
#
class RaspberryPiOsCliTestShould(unittest.TestCase):

    env = TestEnv.create()

    @staticmethod
    def create_os_burn_image_runner():
        return TestCliRunner.run(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "single-board",
                "raspberry-pi",
                "os",
                "burn-image",
                f"--image-download-url={ARG_IMAGE_DOWNLOAD_URL}",
            ],
        )

    @staticmethod
    def create_os_burn_image_runner_darwin():
        return TestCliRunner.run(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "--os-arch=darwin_amd64",
                "single-board",
                "raspberry-pi",
                "os",
                "burn-image",
                f"--image-download-url={ARG_IMAGE_DOWNLOAD_URL}",
            ],
        )

    @staticmethod
    def create_os_burn_image_runner_linux():
        return TestCliRunner.run(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "--os-arch=linux_amd64",
                "single-board",
                "raspberry-pi",
                "os",
                "burn-image",
                f"--image-download-url={ARG_IMAGE_DOWNLOAD_URL}",
            ],
        )

    @mock.patch(f"{RPI_OS_MODULE_PATH}.burn_image_cmd.RPiOsBurnImageCmd.run")
    def test_run_rpi_os_burn_image_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        self.create_os_burn_image_runner()

        def assertion_callback(args):
            self.assertEqual(args.image_download_url, ARG_IMAGE_DOWNLOAD_URL)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_exists(self, run_call, arg_name="ctx")

    @mock.patch(
        f"{RPI_OS_MODULE_PATH}.burn_image_cmd.RPiOsBurnImageCmd.run",
        side_effect=StepEvaluationFailure(STEP_ERROR_OUTPUT),
    )
    def test_run_rpi_os_burn_image_cmd_managed_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_output(
            self,
            expected=STEP_ERROR_OUTPUT,
            method_to_run=lambda: self.create_os_burn_image_runner(),
        )

    #
    # TODO: need to understand why although the 'CliApplicationException' is raised, the test fails
    #
    # @mock.patch(f"{RPI_OS_MODULE_PATH}.burn_image_cmd.RPiOsBurnImageCmd.run", side_effect=Exception())
    # def test_run_rpi_os_burn_image_cmd_unmanaged_failure(self, run_call: mock.MagicMock) -> None:
    #     Assertion.expect_raised_failure(
    #         self,
    #         ex_type=CliApplicationException,
    #         method_to_run=lambda: self.create_os_burn_image_runner(),
    #     )

    @mock.patch("provisioner_shared.components.sd_card.image_burner.ImageBurnerCmdRunner._find_raspberry_pi_boot_partition")
    @mock.patch("provisioner_shared.components.sd_card.image_burner.ImageBurnerCmdRunner._extract_image_file")
    def test_run_rpi_os_burn_image_darwin_success(self, mock_extract: mock.MagicMock, mock_boot_partition: mock.MagicMock) -> None:
        # Mock the extraction to return the original file path for ZIP files in dry-run
        mock_extract.return_value = ("DRY_RUN_DOWNLOAD_FILE_PATH", None)
        # Mock the boot partition to return the expected path
        mock_boot_partition.return_value = "/Volumes/boot"
        
        Assertion.expect_outputs(
            self,
            expected=[
                "diskutil list",
                f"diskutil unmountDisk {AUTO_PROMPT_RESPONSE}",
                f"sudo dd if=DRY_RUN_DOWNLOAD_FILE_PATH of={AUTO_PROMPT_RESPONSE} bs=1m conv=sync status=progress",
                "sync",
                f"diskutil unmountDisk {AUTO_PROMPT_RESPONSE}",
                f"diskutil mountDisk {AUTO_PROMPT_RESPONSE}",
                "sudo cp", # Configuration files are copied
                f"diskutil eject {AUTO_PROMPT_RESPONSE}",
            ],
            method_to_run=lambda: self.create_os_burn_image_runner_darwin(),
        )

    @mock.patch("provisioner_shared.components.sd_card.image_burner.ImageBurnerCmdRunner._find_raspberry_pi_boot_partition")
    @mock.patch("provisioner_shared.components.sd_card.image_burner.ImageBurnerCmdRunner._extract_image_file")
    def test_run_rpi_os_burn_image_linux_success(self, mock_extract: mock.MagicMock, mock_boot_partition: mock.MagicMock) -> None:
        # Mock the extraction to return the original file path for ZIP files in dry-run
        mock_extract.return_value = ("DRY_RUN_DOWNLOAD_FILE_PATH", None)
        # Mock the boot partition to return the expected path
        mock_boot_partition.return_value = "/Volumes/boot"
        
        Assertion.expect_outputs(
            self,
            expected=[
                "lsblk -p",
                f"dd if=DRY_RUN_DOWNLOAD_FILE_PATH of={AUTO_PROMPT_RESPONSE} bs=4M conv=fsync status=progress",
                "sync",
            ],
            method_to_run=lambda: self.create_os_burn_image_runner_linux(),
        )
