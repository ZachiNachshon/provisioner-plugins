#!/usr/bin/env python3


class Versions:
    class Tooling:
        sshpass_ver: str = "1.10"
        anchor_ver: str = "v0.12.0"
        helm_ver: str = "v3.17.3"
        k3s_agent_ver: str = "v1.32.3+k3s1"
        k3s_server_ver: str = "v1.32.3+k3s1"


ToolingVersions: Versions.Tooling = Versions.Tooling()
