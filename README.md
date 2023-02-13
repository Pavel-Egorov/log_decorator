Log Decorator
===

This package provides log decorators for sync and async Python functions which logs function input arguments, 
result and raised exceptions in verbose manner.

REQUIREMENTS
---

1. Python >= 3.6 (async/await and f-strings are used in the package).
2. Python packages from setup.py `install_requires`.

INSTALLATION
---

    pip install verbose-log-decorator

OVERVIEW
---

To integrate log decorators into your code you should just perform a few steps:

1. Choose/implement function which you want to log.
2. Choose right decorator to use (sync or async) and add it to your function:

        import logging
        import sys

        from log_decorator.log import log
        from log_decorator.log_formatter import LogFormatter

        logger = logging.getLogger('service_logger')
        handler = logging.StreamHandler(sys.stdout)

        formatter = LogFormatter(fmt='%(asctime)s %(message)s', formatter_mode='compact')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


        @log()
        def test_log_function(x, y):
            return x / y

3. Call you function and receive output:

        test_log_function(4, 2)

        # Log output:

        # 2021-08-17 12:39:59,282 call __main__.test_log_function {'input_data': {'x': 4, 'y': 2}}
        # 2021-08-17 12:39:59,283 return __main__.test_log_function {'input_data': {'x': 4, 'y': 2}, 'result': 2}

To log exceptions nothing additional is required:

        @log()
        def test_log_function(x, y):
            return x / y

        test_log_function(4, 0)

        # Log output:

        # 2021-08-17 13:14:16,508 call __main__.test_log_function {'input_data': {'x': 4, 'y': 0}}
        # 2021-08-17 13:14:16,509 error in __main__.test_log_function Traceback (most recent call last):
        # File ".../test.py", line 69, in _log
        #   result = wrapped(*args, **kwargs)
        # File "test.py", line 19, in test_log_function
        #   return x / y
        # ZeroDivisionError: division by zero {'input_data': {'x': 4, 'y': 0}}

ADVANCED USAGE
---

`log_formatter.py`

This module provides class LogFormatter which can be used with or without log decorators from the package.
This class can be used as regular log formatters from standard library, but has some additional attributes.

```
class LogFormatter(
    formatter_mode: FormatterMode = FormatterMode.VERBOSE,
    limit_keys_to: Optional[Iterable] = ('input_data', 'result'),
    max_length: Optional[int] = DEFAULT_MAX_LOG_LENGTH,
    separator: str = DEFAULT_SEPARATOR,
    **kwargs,
)
``` 

- `formatter_mode` - either `FormatterMode.COMPACT` or `FormatterMode.VERBOSE` (default):
  - in `verbose` mode logs will be formatted in human-readable way with new lines, separators etc., this mode is 
    recommended for external log storage/explorer such as Graylog.
  - in `compact` mode logs will be formatted as single-line records (except exceptions), this mode is recommended for 
    logging to console.
- `limit_keys_to` - it allows you to restrict which info to add to log records, pass any iterable here or `None` to 
  disable any restrictions.
- `max_length` - restricts max single record length, pass `None` to disable any restrictions.
- `separator` - used in `verbose` mode only to separate different additional log items to improve readability, pass 
  `None` to disable separation.
- `kwargs` - these arguments will be passed to base class (`logging.Formatter`).

---

`log.py`

This module provides log decorator for **sync** functions and methods and some utility functions.

```
def get_logger(logger_name: str = 'service_logger') -> logger isntance with specified name and disabled propagation
```

```
def log(
    logger_inst: logging.Logger = get_logger(),
    lvl: int = logging.INFO,
    *,
    hide_output: bool = False,
    hidden_params: Iterable[str] = (),
    exceptions_only: bool = False,
    track_exec_time: bool = False,
    frequency: int or None = None,
    exception_hook: Callable or None = None,
) -> log_decorator_implementation
```

- `logger_inst` - logger instance to use, by passing you own instance you can configure some additional details such 
  as logger name etc.
- `lvl` - logging level, function calls and returns will be logged with this level, exceptions will be logger with 
  `ERROR` level.
- `hide_output` - if `True` then result of the function call will be completely hidden in log.
- `minify_logs` - if `True` then logs would be minified to reduce storage consumption.
- `hide_input_from_return` - if `True` then return log will not contain input arguments.
- `hidden_params` - pass iterable of strings to hide some arguments or their parts from the log. To hide part of an 
  argument use `__` to access key or index in dict or in an iterable and then its name/index, e.g. if you will pass 
  `hidden_params=['test__key__1']` to log decorator and call function with argument `test={'key': [1,2,3]}` then in 
  logs you will see `test: {'key': [1, 'hidden', 3]}`. To hide multiple parts add all desired paths to `hidden_params`
- `exceptions_only` - if `True` then only exception will be logged.
- `track_exec_time` - if `True` an additional key `execution_time_ms` will be added to log, don't forget to add it 
  to `limit_keys_to` in formatter to see it in final log.
- `frequency` - if passed then only each `n` function call will be logged, use it e.g. to obtain some sort of 
  statistics of functions which are called too intensively to log each call.
- `exception_hook` - pass any callable to execute it when an exception occurs, e.g. it is an easy way to send some 
  notification on errors, `logger_inst`, `exc` (exception instance), `extra` (all collected additional info) will be 
  passed to this hook.

---

`async_log.py`

This module provides log decorator for **async** functions and methods.

```
def log(...) -> async_log_decorator_implementation
```

Look at sync log for signature description, the only difference is that exception_hook should be async if passed.

This decorator doesn't provide async logging, but only async function calls.
To use with async code consider either stdout/UDP inputs or use approach like:
[non-blocking handlers](https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block).

---

Additional features:
1. It is possible to define `get_log_id` method for your classes to represent them in logs in some special way. This 
   method will be called without arguments except of class instance or class itself (in case of passing class itself 
   to the logged function).
2. Each log record will contain `call_id` parameter which will be equal for call, return and exception records of 
   the same call, it is to simplify logs reading and understanding their relations.
3. If an exception will be raised during function call and its instance will have `return_value` attribute then 
   exception will be logged, but not reraised, instead the value of this attribute will be returned.

TESTING
---

The package has built-in unittests with 100% coverage, to run them:
1. Clone repository.
2. Install test dependencies: `pip install pytest pytest-asyncio pytest-cov`
3. Run tests and generate HTML coverage report: `pytest --cov-report html --cov=log_decorator`
4. Review results in `htmlcov/index.html`

CONTRIBUTE
---

If You have found an error or want to offer changes - create a pull request, and I will review it as soon as possible!
