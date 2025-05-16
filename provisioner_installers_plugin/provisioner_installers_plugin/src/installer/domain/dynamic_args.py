#!/usr/bin/env python3


from typing import Any, List


class DynamicArgs:

    dynamic_args: dict[str, Any]

    def __init__(self, dynamic_args: dict[str, Any] = None) -> None:
        self.dynamic_args = dynamic_args if dynamic_args is not None else {}

    def as_ansible_vars(self) -> List[str]:
        if not self.dynamic_args:
            return []
        return [f"{key}='{value}'" for key, value in self.dynamic_args.items()]

    def as_dict(self) -> dict[str, Any]:
        return self.dynamic_args if self.dynamic_args is not None else {}

    def as_cli_args(self) -> str:
        if not self.dynamic_args:
            return ""
        return " ".join(
            [
                f"--{key}" if isinstance(value, bool) and value else f"--{key}={value}"
                for key, value in self.dynamic_args.items()
                if not (isinstance(value, bool) and not value)
            ]
        )
