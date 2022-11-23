    
#!/usr/bin/env python3

import typer
from typing import Optional
from loguru import logger

from python_features_lib.anchor.domain.config import AnchorConfig

class TyperAnchorOpts:
    """
    Load method MUST be called to populate the config object after values were
    read from local configuration file
    """

    # Static variable
    anchor_config: AnchorConfig

    @staticmethod
    def load(anchor_config: AnchorConfig) -> None:
        TyperAnchorOpts.anchor_config = anchor_config

    def github_access_token():
        return typer.Option(
            TyperAnchorOpts.anchor_config.github.github_access_token,
            show_default=False,
            help="GitHub access token for accessing installers private repo",
            envvar="GITHUB_ACCESS_TOKEN",
        )

class TyperResolvedAnchorOpts:
    
    github_access_token: Optional[str]

    def __init__(self, github_access_token: Optional[str]) -> None:
        self.github_access_token = github_access_token

    @staticmethod
    def create(
        github_access_token: Optional[str] = None,
    ) -> None:

        try:
            global typer_cli_anchor_opts
            typer_cli_anchor_opts = TyperResolvedAnchorOpts(github_access_token)

        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create CLI anchor args object. ex: {}, message: {}", e_name, str(e))

    @staticmethod
    def github_access_token() -> Optional[str]:
        return typer_cli_anchor_opts.github_access_token

typer_cli_anchor_opts: TyperResolvedAnchorOpts = None

class CliAnchorOpts:
    github_access_token: Optional[str]

    def __init__(self) -> None:
        self.github_access_token = TyperResolvedAnchorOpts.github_access_token()

    @staticmethod
    def maybe_get() -> "CliAnchorOpts":
        if typer_cli_anchor_opts:
            return CliAnchorOpts()
        return None

    def print(self) -> None:
        logger.debug(
            f"CliAnchorOpts: \n"
            + f"  github_access_token: {self.github_access_token}\n"
        )