#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger
from provisioner_single_board_plugin.src.config.domain.config import SINGLE_BOARD_PLUGIN_NAME
from provisioner_single_board_plugin.src.raspberry_pi.os.burn_image_cmd import (
    RPiOsBurnImageCmd,
    RPiOsBurnImageCmdArgs,
)
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator

rpi_os_cli_app = typer.Typer()


@rpi_os_cli_app.command(name="burn-image")
@logger.catch(reraise=True)
def burn_image(
    image_download_url: Optional[str] = typer.Option(
        ConfigManager.instance().get_plugin_config(SINGLE_BOARD_PLUGIN_NAME).get_os_raspbian_download_url(),
        help="OS image file download URL",
        envvar="PROV_IMAGE_DOWNLOAD_URL",
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
                image_download_path=ConfigManager.instance()
                .get_plugin_config(SINGLE_BOARD_PLUGIN_NAME)
                .maybe_get("os.download_path"),
            ),
        ),
        error_message="Failed to burn Raspbian OS",
    )
