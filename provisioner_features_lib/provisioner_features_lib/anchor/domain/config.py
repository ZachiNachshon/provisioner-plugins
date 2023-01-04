#!/usr/bin/env python3

from provisioner_features_lib.shared.domain.config import GitHubConfig


class AnchorConfig:
    github: GitHubConfig = GitHubConfig()
