import logging
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch, ANY
from uuid import uuid1

from log_decorator import log


class TestLog(TestCase):
    def setUp(self):
        self.test_call_id = uuid1().hex
        self.uuid1_mock = MagicMock(return_value=MagicMock(hex=self.test_call_id))
        self.logger_inst_mock = MagicMock()

    def tearDown(self):
        self.logger_inst_mock.reset_mock()

    def test_get_logger(self):
        logger = log.get_logger()
        self.assertFalse(logger.propagate)
        self.assertEqual(logger.name, 'service_logger')

    def test_log_general(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_general.<locals>.test'

        test_arg1 = None
        test_arg2 = 1
        test_arg3 = 1
        test_kwarg1 = 1
        test_kwarg2 = 1
        test_kwarg3 = {'kwarg3': 1}

        @log.log(self.logger_inst_mock)
        def test(arg1, arg2, *args, kwarg1, kwarg2, **varkw):
            return arg1, arg2, args, kwarg1, kwarg2, varkw

        with patch('log_decorator.log.uuid1', self.uuid1_mock):
            result = test(test_arg1, test_arg2, test_arg3, kwarg1=test_kwarg1, kwarg2=test_kwarg2, **test_kwarg3)

        self.assertEqual(result, (test_arg1, test_arg2, (test_arg3,), test_kwarg1, test_kwarg2, test_kwarg3))

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': self.test_call_id,
                'function': test_func_name,
                'input_data': {
                    'arg1': str(test_arg1),
                    'arg2': test_arg2,
                    '*args': (test_arg3,),
                    'kwarg1': test_kwarg1,
                    'kwarg2': test_kwarg2,
                    'kwarg3': test_kwarg3['kwarg3'],
                },
                'result': (str(test_arg1), test_arg2, (test_arg3,), test_kwarg1, test_kwarg2, test_kwarg3),
            },
        )

    def test_log_with_hidden_varargs(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_with_hidden_varargs.<locals>.test'

        test_arg1 = 1

        @log.log(self.logger_inst_mock, hidden_params=['args'])
        def test(*args):
            return args

        result = test(test_arg1)

        self.assertEqual(result, (1,))
        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {
                    '*args': f'{log.HIDDEN_VALUE} 1 args',
                },
                'result': (test_arg1,),
            },
        )

    def test_log_with_hidden_nested_structure(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_with_hidden_nested_structure.<locals>.test'

        test_arg = [[1], ['test']]
        test_kwarg = {'test': {'test_token': 12345, 'test_info': 'info'}}
        test_kwarg_1 = {'test': {'t': ['123'], 'x': 'x'}, 'test1': 123}

        @log.log(self.logger_inst_mock, hidden_params=[
            'arg__1__0',
            'kwarg__test__test_token',
            'kwarg1__test1',
            'kwarg1__test__t',
        ])
        def test(
            arg,
            kwarg,
            kwarg1,
        ):
            return arg, kwarg, kwarg1

        result = test(test_arg, kwarg=test_kwarg, kwarg1=test_kwarg_1)

        self.assertEqual(result, (test_arg, test_kwarg, test_kwarg_1))

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {
                    'arg': [[1], [log.HIDDEN_VALUE]],
                    'kwarg': {'test': {'test_token': log.HIDDEN_VALUE, 'test_info': 'info'}},
                    'kwarg1': {'test': {'t': log.HIDDEN_VALUE, 'x': 'x'}, 'test1': log.HIDDEN_VALUE},
                },
                'result': (test_arg, test_kwarg, test_kwarg_1),
            },
        )

    def test_log_hide_output(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_hide_output.<locals>.test'

        @log.log(self.logger_inst_mock, hide_output=True)
        def test():
            return

        result = test()

        self.assertIsNone(result)

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
                'result': log.HIDDEN_VALUE,
            },
        )

    def test_log_minify_logs(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_minify_logs.<locals>.test'

        @log.log(self.logger_inst_mock, minify_logs=True)
        def test():
            return

        result = test()

        self.assertIsNone(result)

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': log.HIDDEN_VALUE,
                'result': 'None',
            },
        )

    def test_log_hide_input_from_return(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_hide_input_from_return.<locals>.test'

        @log.log(self.logger_inst_mock, hide_input_from_return=True)
        def test():
            return

        result = test()

        self.assertIsNone(result)

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': log.HIDDEN_VALUE,
                'result': 'None',
            },
        )

    def test_log_hidden_params(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_hidden_params.<locals>.test'

        test_arg = [[1], ['test']]
        test_arg_1 = [[1], ['test']]
        test_arg_2 = [[1], ['test']]
        test_kwarg = {'test': {'test_token': 12345, 'test_info': 'info'}}
        test_kwarg_1 = {'test': {'t': ['123'], 'x': 'x'}, 'test1': 123}

        @log.log(self.logger_inst_mock, hidden_params=[
            'arg__1__0',
            'arg_2',
            'kwarg__test__test_token',
            'kwarg1__test1',
            'kwarg1__test__t',
        ])
        def test(arg, arg_1, arg_2, kwarg, kwarg1):
            return arg, arg_1, arg_2, kwarg, kwarg1

        result = test(test_arg, test_arg_1, test_arg_2, kwarg=test_kwarg, kwarg1=test_kwarg_1)

        self.assertEqual(result, (test_arg, test_arg_1, test_arg_2, test_kwarg, test_kwarg_1))

        self.logger_inst_mock.log.assert_called_with(
            level=logging.INFO,
            msg=f'return {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {
                    'arg': [[1], [log.HIDDEN_VALUE]],
                    'arg_1': [[1], ['test']],
                    'arg_2': log.HIDDEN_VALUE,
                    'kwarg': {'test': {'test_token': log.HIDDEN_VALUE, 'test_info': 'info'}},
                    'kwarg1': {'test': {'t': log.HIDDEN_VALUE, 'x': 'x'}, 'test1': log.HIDDEN_VALUE},
                },
                'result': (test_arg, test_arg_1, test_arg_2, test_kwarg, test_kwarg_1),
            },
        )

    def test_log_track_exec_time(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_track_exec_time.<locals>.test'

        @log.log(self.logger_inst_mock, track_exec_time=True)
        def test():
            return

        result = test()

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

    def test_log_frequency(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_frequency.<locals>.test'

        @log.log(self.logger_inst_mock, frequency=2)
        def test():
            raise Exception()

        for i in range(2):
            self.assertRaises(Exception, test)

        self.logger_inst_mock.exception.assert_called_once_with(
            msg=f'error in {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )

    def test_normalize_for_log(self):

        class TestClass:
            @staticmethod
            def get_log_id():
                return 'test_class_log_representation'

        self.assertEqual(log.normalize_for_log(TestClass()), 'test_class_log_representation')
        self.assertEqual(log.normalize_for_log(dict), "<class 'dict'>")
        self.assertEqual(log.normalize_for_log(None), 'None')
        self.assertEqual(log.normalize_for_log(True), 'True')
        self.assertEqual(log.normalize_for_log([1]), [1])
        self.assertEqual(log.normalize_for_log({'Test': 11}), {'Test': 11})

        test_datetime = datetime.utcnow()
        self.assertEqual(log.normalize_for_log(test_datetime), str(test_datetime))

    def test_log_with_exception(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_with_exception.<locals>.test'

        class TestException(Exception):
            pass

        @log.log(self.logger_inst_mock)
        def test():
            raise TestException()

        self.assertRaises(TestException, test)

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

    def test_log_with_exception_and_return(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_with_exception_and_return.<locals>.test'

        @log.log(self.logger_inst_mock)
        def test():
            e = Exception()
            e.return_value = None
            raise e

        result = test()

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

    def test_log_exception_hook(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_exception_hook.<locals>.test'

        test_exception_hook = MagicMock()

        test_exception = Exception()

        @log.log(self.logger_inst_mock, exception_hook=test_exception_hook)
        def test():
            raise test_exception

        self.assertRaises(Exception, test)
        test_exception_hook.assert_called_once_with(
            self.logger_inst_mock,
            test_exception,
            {
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )

    def test_log_exception_only(self):
        test_func_name = 'log_decorator.tests.test_log.TestLog.test_log_exception_only.<locals>.test'

        @log.log(self.logger_inst_mock, exceptions_only=True)
        def test():
            raise Exception()

        self.assertRaises(Exception, test)

        self.logger_inst_mock.log.assert_not_called()

        self.logger_inst_mock.exception.assert_called_once_with(
            msg=f'error in {test_func_name}',
            extra={
                'call_id': ANY,
                'function': test_func_name,
                'input_data': {},
            },
        )
