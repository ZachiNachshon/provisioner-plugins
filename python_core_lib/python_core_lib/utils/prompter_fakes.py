#!/usr/bin/env python3

from typing import List

from python_core_lib.errors.cli_errors import FakeEnvironmentAssertionError

from python_core_lib.infra.context import Context
from python_core_lib.utils.prompter import Prompter, PromptLevel


class FakePrompter(Prompter):

    press_enter_response: bool = None
    registered_yes_no_prompts: List[str] = None
    registered_user_input_prompts: List[str] = None
    registered_user_selection_prompts: List[str] = None

    def __init__(self, auto_prompt: bool, dry_run: bool):
        super().__init__(auto_prompt=auto_prompt, dry_run=dry_run)
        self.press_enter_response = True
        self.registered_yes_no_prompts = []
        self.registered_user_input_prompts = []
        self.registered_user_selection_prompts = []

    @staticmethod
    def _create_fake(auto_prompt: bool, dry_run: bool) -> "FakePrompter":
        prompter = FakePrompter(auto_prompt, dry_run)
        prompter.prompt_user_selection_fn = lambda message, options, multi_select=False: prompter._register_user_selection_prompt(message)
        prompter.prompt_user_input_fn = lambda message, default=None, redact_default=False, level=PromptLevel.HIGHLIGHT, post_user_input_message=None: prompter._register_user_input_prompt(
            message
        )
        prompter.prompt_yes_no_fn = lambda message, level=PromptLevel.INFO, post_yes_message=None, post_no_message=None: prompter._register_yes_no_prompt_approve(
            message
        )
        prompter.prompt_for_enter_fn = lambda level=PromptLevel.INFO: prompter.press_enter_response
        return prompter

    @staticmethod
    def create(ctx: Context) -> "FakePrompter":
        return FakePrompter._create_fake(auto_prompt=ctx.is_auto_prompt(), dry_run=ctx.is_dry_run())

    def _register_yes_no_prompt_approve(self, prompt_str: str) -> bool:
        self.registered_yes_no_prompts.append(prompt_str)
        return True

    def _register_yes_no_prompt_reject(self, prompt_str: str) -> bool:
        self.registered_yes_no_prompts.append(prompt_str)
        return False

    def assert_yes_no_prompt(self, message: str) -> None:
        found = False
        for prompt in self.registered_yes_no_prompts:
            if message in prompt:
                found = True
                break
        if not found:
            raise FakeEnvironmentAssertionError("Prompter expected a yes/no message but it never triggered. message: " + message)

    def _register_user_input_prompt(self, prompt_str: str):
        self.registered_user_input_prompts.append(prompt_str)

    def assert_user_input_prompt(self, message: str) -> None:
        if message not in self.registered_user_input_prompts:
            raise FakeEnvironmentAssertionError("Prompter expected a user input message but it never triggered. message: " + message)

    def _register_user_selection_prompt(self, prompt_str: str):
        self.registered_user_selection_prompts.append(prompt_str)

    def assert_user_selection_prompt(self, message: str) -> None:
        if message not in self.registered_user_selection_prompts:
            raise FakeEnvironmentAssertionError("Prompter expected a user selection message but it never triggered. message: " + message)
