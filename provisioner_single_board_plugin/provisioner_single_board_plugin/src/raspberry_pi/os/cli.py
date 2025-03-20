#!/usr/bin/env python3

from typing import Optional

import click
from provisioner_single_board_plugin.src.config.domain.config import (
    SingleBoardConfig,
)
from provisioner_single_board_plugin.src.raspberry_pi.os.burn_image_cmd import RPiOsBurnImageCmd, RPiOsBurnImageCmdArgs

from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_os_commands(cli_group: click.Group, single_board_cfg: Optional[SingleBoardConfig] = None):

    @cli_group.command()
    @click.option(
        "--image-download-url",
        type=str,
        help="OS image file download URL",
        show_default=False,
        envvar="PROV_IMAGE_DOWNLOAD_URL",
    )
    @cli_modifiers
    @click.pass_context
    def burn_image(ctx: click.Context, image_download_url: Optional[str] = None) -> None:
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
                    image_download_path=single_board_cfg.maybe_get("os.download_path"),
                ),
            ),
            error_message="Failed to burn Raspbian OS",
            verbose=cli_ctx.is_verbose(),
        )
