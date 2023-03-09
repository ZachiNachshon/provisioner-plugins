#!/usr/bin/env python3

from typing import Optional
from python_core_lib.infra.evaluator import Evaluator

import typer
from loguru import logger
from provisioner_features_lib.config.config_resolver import ConfigResolver
from python_core_lib.infra.context import CliContextManager

from provisioner_single_board_plugin.raspberry_pi.os.burn_image_cmd import (
    RPiOsBurnImageCmd,
    RPiOsBurnImageCmdArgs,
)

rpi_os_cli_app = typer.Typer()


@rpi_os_cli_app.command(name="burn-image")
@logger.catch(reraise=True)
def burn_image(
    image_download_url: Optional[str] = typer.Option(
        ConfigResolver.get_config().single_board.get_os_raspbian_download_url(),
        help="OS image file download URL",
        envvar="IMAGE_DOWNLOAD_URL",
    )
) -> None:
    """
    Select an available block device to burn a Raspbian OS image (SD-Card / HDD)
    """
    Evaluator.eval_cli_entrypoint_step(
        name="Raspbian OS Image Burn",
        call=lambda: RPiOsBurnImageCmd().run(
            ctx=CliContextManager.create(),
            args=RPiOsBurnImageCmdArgs(
                image_download_url=image_download_url,
                image_download_path=ConfigResolver.get_config().single_board.os.download_path,
            ),
        ),
        error_message="Failed to burn Raspbian OS"
    )
