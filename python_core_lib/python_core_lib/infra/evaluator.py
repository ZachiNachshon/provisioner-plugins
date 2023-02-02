#!/usr/bin/env python3

from loguru import logger
from typing import Any, Callable

from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import StepEvaluationFailure
from python_core_lib.infra.context import Context


class Evaluator:
    @staticmethod
    def eval_step_no_return_throw_on_failure(ctx: Context, err_msg: str, call: Callable) -> None:
        try:
            call()
        except Exception as e:
            raise StepEvaluationFailure(f"{err_msg}, ex: {e.__class__.__name__}, message: {str(e)}")

    @staticmethod
    def eval_step_with_return_throw_on_failure(ctx: Context, err_msg: str, call: Callable) -> Any:
        step_response = call()
        if not step_response and not ctx.is_dry_run():
            raise StepEvaluationFailure(err_msg)
        return step_response

    @staticmethod
    def eval_size_else_throws(ctx: Context, err_msg: str, call: Callable) -> Any:
        step_response = call()
        if not step_response and len(step_response) == 0 and not ctx.is_dry_run():
            raise StepEvaluationFailure(err_msg)

        return step_response
    
    @staticmethod
    def eval_cli_entrypoint_step(ctx: Context, err_msg: str, call: Callable) -> None:
        try:
            call()
        except StepEvaluationFailure as sef:
            logger.critical(f"{err_msg}, ex: {sef.__class__.__name__}, message: {str(sef)}")
        except Exception as e:
            logger.critical(f"{err_msg}, ex: {e.__class__.__name__}, message: {str(e)}")
            if CliGlobalArgs.is_verbose():
                raise e

    @staticmethod
    def eval_installer_cli_entrypoint_step(ctx: Context, name: str, call: Callable) -> None:
        try:
            call()
        except StepEvaluationFailure as sef:
            logger.critical(f"Failed to install CLI utility. name: {name}, ex: {sef.__class__.__name__}, message: {str(sef)}")
        except Exception as e:
            logger.critical(f"Failed to install CLI utility. name: {name}, ex: {e.__class__.__name__}, message: {str(e)}")
            if CliGlobalArgs.is_verbose():
                raise e