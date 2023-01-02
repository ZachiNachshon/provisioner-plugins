#!/usr/bin/env python3

from python_features_lib.anchor.typer_anchor_opts import (
    TyperAnchorOpts,
    TyperResolvedAnchorOpts,
)


def anchor_args_callback(github_access_token: str = TyperAnchorOpts.github_access_token()):
    TyperResolvedAnchorOpts.create(
        github_access_token,
    )
