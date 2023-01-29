#!/usr/bin/env python3

from typing import Any
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.summary import Summary
from python_core_lib.infra.context import Context


class FakeSummary(Summary):

    registered_values: dict[str, Any] = {}

    def __init__(self, json_util: JsonUtil):
        super().__init__(dry_run=True, verbose=False, auto_prompt=False, json_util=json_util, printer=None, prompter=None) 

    def _record_summary_attribute(self, attribute_name, value) -> None:
        self.registered_values[attribute_name] = value

    @staticmethod
    def _create_fake(json_util: JsonUtil) -> "FakeSummary":
        fake_summary = FakeSummary(json_util=json_util)
        fake_summary.append = lambda attribute_name, value: fake_summary.register_appended_value(attribute_name, value)
        fake_summary.show_summary_and_prompt_for_enter = lambda title: None
        return fake_summary

    @staticmethod
    def create(ctx: Context) -> "FakeSummary":
        return FakeSummary._create_fake(json_util=JsonUtil.create(ctx=ctx, io_utils=None))

    def register_appended_value(self, attribute_name: str, value: Any) -> None:
        self.registered_values[attribute_name] = value

    def assert_value(self, attribute_name: str, value: Any) -> None:
        if attribute_name not in self.registered_values:
            raise FakeEnvironmentAssertionError(f"Summary expected to have an attribute name which never met. name: {attribute_name}")
        
        assert_hash = hash(self.registered_values[attribute_name])
        value_hash = hash(value)
        if assert_hash != value_hash:
            raise FakeEnvironmentAssertionError(f"Summary expected attribute value was not the same as expected. name: {attribute_name}")
