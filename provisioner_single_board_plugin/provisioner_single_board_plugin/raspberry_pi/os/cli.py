#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger
from provisioner_features_lib.config.config_resolver import ConfigResolver
from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
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
    try:
        RPiOsBurnImageCmd().run(
            ctx=CliContextManager.create(),
            args=RPiOsBurnImageCmdArgs(
                image_download_url=image_download_url,
                image_download_path=ConfigResolver.get_config().single_board.os.download_path,
            ),
        )
    except StepEvaluationFailure as sef:
        logger.critical("Failed to burn Raspbian OS. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to burn Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)
