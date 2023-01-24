#!/usr/bin/env python3

class GitHubConfig:
    
    organization: str = None
    repository: str = None
    branch: str = None
    github_access_token: str = None

    def __init__(self, organization: str = None, repository: str = None, branch: str = None, github_access_token: str = None) -> None:
        self.organization = organization
        self.repository = repository
        self.branch = branch
        self.github_access_token = github_access_token
