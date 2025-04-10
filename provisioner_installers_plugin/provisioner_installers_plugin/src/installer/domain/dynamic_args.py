#!/usr/bin/env python3


from typing import Any, List


class DynamicArgs:

    dynamic_args: dict[str, Any]

    def __init__(self, dynamic_args: dict[str, Any]) -> None:
        self.dynamic_args = dynamic_args

    def as_ansible_vars(self) -> List[str]:
        return [f"{key}='{value}'" for key, value in self.dynamic_args.items()]
    
    def as_dict(self) -> dict[str, Any]:
        return self.dynamic_args

    def as_cli_args(self) -> str:
        return " ".join([f"--{key}" if isinstance(value, bool) and value else f"--{key}={value}" for key, value in self.dynamic_args.items() if not (isinstance(value, bool) and not value)])