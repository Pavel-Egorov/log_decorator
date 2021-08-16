import logging
import unittest
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from log_decorator import async_log, log


class TestAsyncLog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()

        self.logger_inst_mock = MagicMock()

    @pytest.mark.asyncio
    async def test_log_general(self):
        test_func_name = 'log_decorator.test.test_async_log.TestAsyncLog.test_log_general.<locals>.test'

        test_arg1 = None
        test_arg2 = 1
        test_kwarg1 = 1
        test_kwarg2 = 1

        @async_log.log(self.logger_inst_mock)
        async def test(arg1, arg2: log.HIDE_ANNOTATION, *, kwarg1, kwarg2: log.HIDE_ANNOTATION):
            return arg1, arg2, kwarg1, kwarg2

        result = await test(test_arg1, test_arg2, kwarg1=test_kwarg1, kwarg2=test_kwarg2)

        self.assertEqual(result, (test_arg1, test_arg2, test_kwarg1, test_kwarg2))

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {
                    'arg1': str(test_arg1),
                    'arg2': log.HIDDEN_VALUE,
                    'kwarg1': test_kwarg1,
                    'kwarg2': log.HIDDEN_VALUE,
                },
                'result': (str(test_arg1), test_arg2, test_kwarg1, test_kwarg2),
            },
        )

    @pytest.mark.asyncio
    async def test_log_track_exec_time(self):
        test_func_name = 'log_decorator.test.test_async_log.TestAsyncLog.test_log_track_exec_time.<locals>.test'

        @async_log.log(self.logger_inst_mock, track_exec_time=True)
        async def test():
            return

        result = await test()

        self.assertIsNone(result)

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
                'execution_time_ms': ANY,
                'result': 'None',
            },
        )

    @pytest.mark.asyncio
    async def test_log_frequency(self):
        test_func_name = 'log_decorator.test.test_async_log.TestAsyncLog.test_log_frequency.<locals>.test'

        class TestException(Exception):
            pass

        @async_log.log(self.logger_inst_mock, frequency=2)
        async def test():
            raise TestException()

        for i in range(2):
            try:
                await test()
            except TestException:  # noqa
                pass

        self.logger_inst_mock.exception.assert_called_once_with(
            msg=f'error in {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )

    @pytest.mark.asyncio
    async def test_log_exception_hook(self):
        test_func_name = 'log_decorator.test.test_async_log.TestAsyncLog.test_log_exception_hook.<locals>.test'

        test_exception_hook = AsyncMock()

        class TestException(Exception):
            pass

        test_exception = TestException()

        @async_log.log(self.logger_inst_mock, exception_hook=test_exception_hook)
        async def test():
            raise test_exception

        try:
            await test()
        except TestException:
            pass

        test_exception_hook.assert_called_once_with(
            self.logger_inst_mock,
            test_exception,
            {
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )

    # noinspection DuplicatedCode
    @pytest.mark.asyncio
    async def test_log_with_exception_and_return(self):
        test_func_name = 'log_decorator.test.test_async_log.TestAsyncLog.test_log_with_exception_and_return.<locals>.' \
                         'test'

        @async_log.log(self.logger_inst_mock)
        async def test():
            e = Exception()
            e.return_value = None
            raise e

        result = await test()

        self.assertIsNone(result)

        self.logger_inst_mock.log.assert_called_once_with(
            level=logging.INFO,
            msg=f'call {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )

        self.logger_inst_mock.exception.assert_called_once_with(
            msg=f'error in {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )
