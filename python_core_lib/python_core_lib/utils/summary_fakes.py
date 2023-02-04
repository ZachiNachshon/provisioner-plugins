#!/usr/bin/env python3

from typing import Any, List
from python_core_lib.test_lib.test_errors import FakeEnvironmentAssertionError
from python_core_lib.utils.json_util import JsonUtil
from python_core_lib.utils.summary import Summary
from python_core_lib.infra.context import Context


class FakeSummary(Summary):

    __registered_values: dict[str, Any] = None
    __registered_titles: List[str] = None

    def __init__(self, json_util: JsonUtil):
        super().__init__(dry_run=True, verbose=False, auto_prompt=False, json_util=json_util, printer=None, prompter=None) 
        self.__registered_values = {}
        self.__registered_titles = []

    def _record_summary_attribute(self, attribute_name, value) -> None:
        self.__registered_values[attribute_name] = value

    @staticmethod
    def _create_fake(json_util: JsonUtil) -> "FakeSummary":
        fake_summary = FakeSummary(json_util=json_util)
        fake_summary.append = lambda attribute_name, value: fake_summary._register_appended_value(attribute_name, value)
        fake_summary.show_summary_and_prompt_for_enter = lambda title: fake_summary._register_show_summary_title(title)
        return fake_summary

    @staticmethod
    def create(ctx: Context) -> "FakeSummary":
        return FakeSummary._create_fake(json_util=JsonUtil.create(ctx=ctx, io_utils=None))

    def _register_appended_value(self, attribute_name: str, value: Any) -> None:
        self.__registered_values[attribute_name] = value

    def assert_value(self, attribute_name: str, value: Any) -> None:
        if attribute_name not in self.__registered_values:
            raise FakeEnvironmentAssertionError(f"Summary expected to have an attribute name which never met. name: {attribute_name}")
        
        assert_hash = hash(self.__registered_values[attribute_name])
        value_hash = hash(value)
        if assert_hash != value_hash:
            raise FakeEnvironmentAssertionError(f"Summary expected attribute value was not the same as expected. name: {attribute_name}")

    def _register_show_summary_title(self, title: str) -> None:
        self.__registered_titles.append(title)

    def assert_show_summay_title(self, title: str) -> None:
        if title not in self.__registered_titles:
            raise FakeEnvironmentAssertionError(f"Summary expected to have an title on summary display. title: {title}")
