import logging
from typing import Optional, Iterable
from enum import Enum

import ujson

DEFAULT_MAX_LOG_LENGTH = 32000

DEFAULT_SEPARATOR = f'\n\n{"=" * 50}\n\n'


class FormatterMode(str, Enum):
    """Available formatter modes."""

    COMPACT = 'compact'
    VERBOSE = 'verbose'


class LogFormatter(logging.Formatter):
    """Formatter to format log records in a human-readable way."""

    def __init__(  # noqa: WPS211
        self,
        formatter_mode: FormatterMode = FormatterMode.VERBOSE,
        limit_keys_to: Optional[Iterable] = ('input_data', 'result'),
        max_length: Optional[int] = DEFAULT_MAX_LOG_LENGTH,
        separator: str = DEFAULT_SEPARATOR,
        **kwargs,
    ):
        super(LogFormatter, self).__init__(**kwargs)  # noqa: WPS608

        available_formatters = {
            FormatterMode.COMPACT: self.compact_formatter,
            FormatterMode.VERBOSE: self.verbose_formatter,
        }
        self.selected_formatter = available_formatters.get(formatter_mode)
        if self.selected_formatter is None:
            raise Exception(f'Formatter {formatter_mode} is unavailable')  # noqa: WPS454

        self.limit_keys_to = limit_keys_to
        self.max_length = max_length
        self.separator = separator

    def format(self, record: logging.LogRecord) -> str:
        """Converts log record to readable string."""
        return self.selected_formatter(record)  # noqa

    def compact_formatter(self, record: logging.LogRecord) -> str:
        """Converts log record to single-line compact readable string for console output."""
        formatted = super(LogFormatter, self).format(record)  # noqa: WPS608

        record_data = record.__dict__
        extra = {}
        for i, j in record_data.items():
            if (self.limit_keys_to is None) or (i in self.limit_keys_to):
                extra[i] = j

        return self._strip_message_if_needed(f'{formatted} {extra}')

    def verbose_formatter(self, record: logging.LogRecord) -> str:
        """Converts log record to multi-line verbose readable string for log storage."""
        record_data = record.__dict__

        result = record_data.get('msg', '')
        result += '\n' * 2

        for i, j in record_data.items():
            if (self.limit_keys_to is not None) and (i not in self.limit_keys_to):
                continue

            try:
                prepared_value = ujson.dumps(j, indent=2, ensure_ascii=False)
            except TypeError:
                prepared_value = j

            result += f'{self.separator}{str(i).upper().replace("_", " ")}:\n{prepared_value}'

        result += self.separator

        return self._strip_message_if_needed(result)

    def _strip_message_if_needed(self, message):
        if self.max_length is not None and len(message) > self.max_length:
            return f'{message[:self.max_length-3]}...'
        return message
