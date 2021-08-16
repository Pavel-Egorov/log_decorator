import json
import logging

DEFAULT_SEPARATOR = f'\n\n{"=" * 50}\n\n'

DEFAULT_MAX_LOG_LENGTH = 10000


class LogFormatter(logging.Formatter):
    def __init__(
        self,
        formatter_mode='verbose',
        limit_keys_to=('input_data', 'result'),
        max_length=DEFAULT_MAX_LOG_LENGTH,
        separator=DEFAULT_SEPARATOR,
        **kwargs,
    ):
        super(LogFormatter, self).__init__(**kwargs)

        self.limit_keys_to = limit_keys_to
        self.max_length = max_length
        self.separator = separator if separator is not None else ''

        available_formatters = {
            'compact': self.compact_formatter,
            'verbose': self.verbose_formatter,
        }
        if formatter_mode not in available_formatters:
            raise Exception(f'Formatter mode {formatter_mode} not found')
        self.used_formatter = available_formatters[formatter_mode]

    def format(self, record):
        return self.used_formatter(record)  # noqa

    def compact_formatter(self, record):
        formatted = super(LogFormatter, self).format(record)

        record_data = record.__dict__
        extra = {}
        for i, j in record_data.items():
            if self.limit_keys_to is None or i in self.limit_keys_to:
                extra[i] = j

        return self._strip_message_if_needed(f'{formatted} {extra}')

    def verbose_formatter(self, record):
        record_data = record.__dict__

        result = record.__dict__.get('msg', '')
        result += '\n' * 2

        keys_to_log = self.limit_keys_to if self.limit_keys_to is not None else list(record_data)
        for i in keys_to_log:
            value = record_data.pop(i, None)
            if value is not None:
                try:
                    prepared_value = json.dumps(value, indent=2)
                except TypeError:
                    prepared_value = value

                result += f'{self.separator}{str(i).upper().replace("_", " ")}:\n{prepared_value}'

        result += self.separator

        return self._strip_message_if_needed(result)

    def _strip_message_if_needed(self, message):
        if self.max_length is not None and len(message) > self.max_length:
            return f'{message[:self.max_length]}...'
        return message
