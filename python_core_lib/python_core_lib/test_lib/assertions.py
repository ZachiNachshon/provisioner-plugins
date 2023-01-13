#!/usr/bin/env python3

from typing import Any, Type


class Assertion:
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
