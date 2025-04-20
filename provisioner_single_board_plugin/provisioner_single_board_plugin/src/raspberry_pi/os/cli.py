#!/usr/bin/env python3

from typing import Optional

import click
from loguru import logger
from provisioner_single_board_plugin.src.config.domain.config import (
    SingleBoardConfig,
)
from provisioner_single_board_plugin.src.raspberry_pi.os.burn_image_cmd import RPiOsBurnImageCmd, RPiOsBurnImageCmdArgs

from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
import os


def register_os_commands(cli_group: click.Group, single_board_cfg: Optional[SingleBoardConfig] = None):

    first_boot_username = single_board_cfg.maybe_get("os.raspbian.first_boot_username") if single_board_cfg else ""
    first_boot_password = single_board_cfg.maybe_get("os.raspbian.first_boot_password") if single_board_cfg else ""
    maybe_image_download_url = single_board_cfg.maybe_get("os.raspbian.download_url.url_64bit")
    maybe_image_download_path = single_board_cfg.maybe_get("os.raspbian.download_path")
    
    @cli_group.command()
    @click.option(
        "--image-download-url",
        type=str,
        help="OS image file download URL",
        show_default=True,
        default=maybe_image_download_url if maybe_image_download_url else "",
        envvar="PROV_SINGLE_BOARD_IMAGE_DOWNLOAD_URL",
    )
    @click.option(
        "--image-download-path",
        type=str,
        help="OS image file download path",
        show_default=True,
        default=maybe_image_download_path if maybe_image_download_path else "",
        envvar="PROV_SINGLE_BOARD_IMAGE_DOWNLOAD_PATH",
    )
    @click.option(
        "--first-boot-username",
        type=str,
        help="First boot username",
        show_default=True,
        default=first_boot_username,
        envvar="PROV_SINGLE_BOARD_FIRST_BOOT_USERNAME",
    )
    @click.option(
        "--first-boot-password",
        type=str,
        help="First boot password",
        show_default=True,
        default=first_boot_password,
        envvar="PROV_SINGLE_BOARD_FIRST_BOOT_PASSWORD",
    )
    @cli_modifiers
    @click.pass_context
    def burn_image(ctx: click.Context, image_download_url: str, image_download_path: str, first_boot_username: str, first_boot_password: str) -> None:
        """
        Select an available block device to burn a Raspbian OS image (SD-Card / HDD)
        """
        cli_ctx = CliContextManager.create(modifiers=CliModifiers.from_click_ctx(ctx))
        Evaluator.eval_cli_entrypoint_step(
            name="Raspbian OS Image Burn",
            call=lambda: RPiOsBurnImageCmd().run(
                ctx=cli_ctx,
                args=RPiOsBurnImageCmdArgs(
                    image_download_url=image_download_url,
                    image_download_path=image_download_path,
                    first_boot_username=first_boot_username,
                    first_boot_password=first_boot_password,
                ),
            ),
            error_message="Failed to burn Raspbian OS",
            verbose=cli_ctx.is_verbose(),
        )
