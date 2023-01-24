#!/usr/bin/env python3

from provisioner_features_lib.shared.domain.config import GitHubConfig


class AnchorConfig:
    
    github: GitHubConfig = None

    def __init__(self, github: GitHubConfig = GitHubConfig()) -> None:
        self.github = github