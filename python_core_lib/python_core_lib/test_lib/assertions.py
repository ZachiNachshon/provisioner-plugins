#!/usr/bin/env python3

from typing import Any, Callable, Type
from unittest import mock


class Assertion:

    @staticmethod
    def expect_call_argument(testObj, method_run_call: mock.MagicMock, arg_name: str, expected_value: Any) -> None:
        try:
            print(method_run_call)
            print(method_run_call)
            print(method_run_call)
            print(method_run_call.call_args)
            print(method_run_call.call_args)
            print(method_run_call.call_args)
            run_call_kwargs = method_run_call.call_args.kwargs
            call_arg = run_call_kwargs[arg_name]
            testObj.assertEqual(expected_value, call_arg)
        except Exception as ex:
            testObj.fail(f"Method call argument did not have the expected value. message: {str(ex)}")
    
    @staticmethod
    def expect_call_arguments(testObj, method_run_call: mock.MagicMock, arg_name: str, assertion_callable: Callable[..., Any]) -> None:
        try:
            run_call_kwargs = method_run_call.call_args.kwargs
            call_arg = run_call_kwargs[arg_name]
            callable(call_arg)
            # testObj.assertEqual(expected_value, call_arg)
        except Exception as ex:
            testObj.fail(f"Method call arguments did not have the expected values. message: {str(ex)}")

    @staticmethod
    def expect_failure(testObj, ex_type: Type, method_to_run) -> None:
        failed = False
        try:
            method_to_run()
        except Exception as ex:
            failed = True
            testObj.assertIsInstance(ex, ex_type)

        testObj.assertTrue(failed)

    @staticmethod
    def expect_success(testObj, method_to_run) -> Any:
        output = None
        success = False
        try:
            output = method_to_run()
            success = True
        except Exception as ex:
            testObj.fail(f"Test was expected to pass. message: {str(ex)}")

        testObj.assertTrue(success)
        return output
