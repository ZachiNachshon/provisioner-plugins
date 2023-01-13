#!/usr/bin/env python3

from typing import Any
from python_core_lib.errors.cli_errors import TestEnvironmentAssertionError
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.summary import Summary
from python_core_lib.infra.context import Context


class FakeSummary(Summary):

    registered_values: dict[str, Any] = {}

    def __init__(self, json_util: JsonUtil):
        super().__init__(dry_run=True, verbose=False, auto_prompt=False, json_util=json_util, printer=None, prompter=None) 

    @staticmethod
    def _create_fake(json_util: JsonUtil) -> "FakeSummary":
        fake_summary = FakeSummary(json_util=json_util)
        fake_summary.append = lambda attribute_name, value: fake_summary.assert_value(attribute_name, value)
        fake_summary.show_summary_and_prompt_for_enter = lambda title: fake_summary.assert_summary(title)
        return fake_summary

    @staticmethod
    def create(ctx: Context) -> "FakeSummary":
        return FakeSummary._create_fake(json_util=JsonUtil.create(ctx=ctx, io_utils=None))

    def register_value_assertion(self, attribute_name: str, value: Any) -> None:
        self.registered_values[attribute_name] = self._json_util.to_json_fn(value)

    def assert_value(self, attribute_name: str, value: Any) -> None:
        if attribute_name not in self.registered_values:
            raise TestEnvironmentAssertionError("Fake summary attribute name is not defined")
        
        assert_json = self._json_util.to_json_fn(self.registered_values[attribute_name])
        value_json = self._json_util.to_json_fn(value)
        if assert_json != value_json:
            raise TestEnvironmentAssertionError("Fake summary attribute value is not the same as expected")
