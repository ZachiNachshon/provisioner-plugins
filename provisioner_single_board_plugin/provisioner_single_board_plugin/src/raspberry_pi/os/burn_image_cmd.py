#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.sd_card.image_burner import (
    ImageBurnerArgs,
    ImageBurnerCmdRunner,
)


class RPiOsBurnImageCmdArgs:

    image_download_url: str
    image_download_path: str
    first_boot_username: str
    first_boot_password: str

    def __init__(self, image_download_url: str, image_download_path: str, first_boot_username: str, first_boot_password: str) -> None:
        self.image_download_url = image_download_url
        self.image_download_path = image_download_path
        self.first_boot_username = first_boot_username
        self.first_boot_password = first_boot_password

    def print(self) -> None:
        logger.debug(
            "RPiOsBurnImageCmdArgs: \n"
            + f"  image_download_url: {self.image_download_url}\n"
            + f"  image_download_path: {self.image_download_path}\n"
            + f"  first_boot_username: {self.first_boot_username}\n"
            + f"  first_boot_password: {self.first_boot_password}\n"
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
                first_boot_username=args.first_boot_username,
                first_boot_password=args.first_boot_password,
            ),
            collaborators=CoreCollaborators(ctx),
        )
