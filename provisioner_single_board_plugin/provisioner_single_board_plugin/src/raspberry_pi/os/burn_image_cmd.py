#!/usr/bin/env python3

import pathlib

from loguru import logger

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.sd_card.image_burner import (
    ImageBurnerArgs,
    ImageBurnerCmdRunner,
)

PROJECT_ROOT_FOLDER = str(pathlib.Path(__file__).parent.parent.parent.parent)
RPI_IMAGE_BURN_RESOURCES_PATH = f"{PROJECT_ROOT_FOLDER}/resources/raspberrypi"


class RPiOsBurnImageCmdArgs:

    image_download_url: str
    image_download_path: str
    first_boot_username: str

    def __init__(self, image_download_url: str, image_download_path: str, first_boot_username: str) -> None:
        self.image_download_url = image_download_url
        self.image_download_path = image_download_path
        self.first_boot_username = first_boot_username

    def print(self) -> None:
        logger.debug(
            "RPiOsBurnImageCmdArgs: \n"
            + f"  image_download_url: {self.image_download_url}\n"
            + f"  image_download_path: {self.image_download_path}\n"
            + f"  first_boot_username: {self.first_boot_username}\n"
        )


class RPiOsBurnImageCmd:
    def run(self, ctx: Context, args: RPiOsBurnImageCmdArgs) -> None:
        logger.debug("Inside RPiOsBurnImageCmd run()")
        args.print()

        ImageBurnerCmdRunner().run(
            ctx=ctx,
            args=ImageBurnerArgs(
                image_download_url=args.image_download_url,
                image_download_path=args.image_download_path,
                maybe_resources_path=RPI_IMAGE_BURN_RESOURCES_PATH,
            ),
            collaborators=CoreCollaborators(ctx),
        )
