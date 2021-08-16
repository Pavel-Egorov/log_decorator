import logging
from unittest import TestCase

from log_decorator.log_formatter import LogFormatter

TEST_VERBOSE_RESULT_1 = '''test msg



==================================================

INPUT DATA:
{
  "test": "123"
}

==================================================

RESULT:
{'1'}

==================================================

'''

TEST_VERBOSE_RESULT_2 = '''test msg



==================================================

TEST:
{}

==================================================

'''

TEST_VERBOSE_RESULT_3 = '''test msg



INPUT DATA:
{
  "test": "123"
}

RESULT:
{'1'}

'''


class TestLogFormatter(TestCase):
    def test_wrong_formatter_mode(self):
        with self.assertRaises(Exception):
            LogFormatter(formatter_mode='test')

    def test_compact_formatter(self):
        test_formatter = LogFormatter(formatter_mode='compact')
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, "test msg {'input_data': {'test': '123'}, 'result': {'1'}}")

        test_formatter = LogFormatter(formatter_mode='compact', limit_keys_to=['test'])
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, "test msg {'test': {}}")

        test_formatter = LogFormatter(formatter_mode='compact', limit_keys_to=None)
        test_formatter.format(self._get_record_mock())

        test_formatter = LogFormatter(formatter_mode='compact', max_length=10)
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, 'test msg {...')

        test_formatter = LogFormatter(formatter_mode='compact', max_length=57)
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, "test msg {'input_data': {'test': '123'}, 'result': {'1'}}")

    def test_verbose_formatter(self):
        test_formatter = LogFormatter()
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, TEST_VERBOSE_RESULT_1)

        test_formatter = LogFormatter(limit_keys_to=['test'])
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, TEST_VERBOSE_RESULT_2)

        test_formatter = LogFormatter(limit_keys_to=None)
        test_formatter.format(self._get_record_mock())

        test_formatter = LogFormatter(max_length=10)
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, f'{TEST_VERBOSE_RESULT_2[:10]}...')

        test_formatter = LogFormatter(separator='\n\n')
        result = test_formatter.format(self._get_record_mock())
        self.assertEqual(result, TEST_VERBOSE_RESULT_3)

    @staticmethod
    def _get_record_mock():
        return logging.getLogger('unittest').makeRecord(
            name='test',
            level=logging.DEBUG,
            fn='',
            lno=0,
            msg='test msg',
            args=(),
            exc_info=None,
            extra={
                'input_data': {'test': '123'},
                'result': {'1'},
                'test': {},
            },
        )
