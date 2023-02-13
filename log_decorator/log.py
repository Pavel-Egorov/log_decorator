import inspect
import logging
import re
import time
from copy import deepcopy
from types import FunctionType
from typing import Any, Callable, Iterable, List, Tuple
from uuid import uuid1

import ujson
from wrapt import decorator

HIDDEN_VALUE = 'hidden'

SECONDS_TO_MS = 1000

LOWEST_LOG_LVL = 5

LOGS_COUNTER = {}  # noqa: WPS407


def get_logger(logger_name: str = 'service_logger') -> logging.Logger:
    """Get logger with specified name with disabled propagation to avoid several log records related to one event."""
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    return logger


def log(  # noqa: WPS211
    logger_inst: logging.Logger = get_logger(),
    lvl: int = logging.INFO,
    *,
    hide_output: bool = False,
    minify_logs: bool = False,
    hide_input_from_return: bool = False,
    hidden_params: Iterable = (),
    exceptions_only: bool = False,
    track_exec_time: bool = False,
    frequency: int = None,
    exception_hook: FunctionType = None,
) -> Callable:
    """
    Decorator to trace function calls in logs.

    It logs function call, function return and any exceptions with separate log records.
    This high-level function is needed to pass additional parameters and customise _log behavior.
    """
    # noinspection DuplicatedCode
    @decorator
    def _log(wrapped: FunctionType, instance: Any, args: tuple[Any], kwargs: dict[str, Any]) -> Any:
        """Actual implementation of the above decorator."""
        func_name = f'{wrapped.__module__}.{wrapped.__qualname__}'
        extra = {'call_id': uuid1().hex, 'function': func_name}

        _hide_input_from_return = hide_input_from_return if not minify_logs else True

        send_log = True

        if frequency is not None:
            log_counter = LOGS_COUNTER.setdefault(func_name, 0) + 1
            LOGS_COUNTER[func_name] = log_counter

            if log_counter % frequency != 0:
                send_log = False

        try:  # noqa: WPS229
            params = inspect.getfullargspec(wrapped)
            extra['input_data'] = get_logged_args(
                params,
                [instance] + list(args) if instance else args,
                kwargs,
                hidden_params,
            )
            if send_log and not exceptions_only:
                logger_inst.log(level=lvl, msg=f'call {func_name}', extra=extra)

            start_time = time.time()

            result = wrapped(*args, **kwargs)
            if track_exec_time:
                extra['execution_time_ms'] = int((time.time() - start_time) * SECONDS_TO_MS)

            extra['result'] = HIDDEN_VALUE if hide_output else normalize_for_log(result)

            if send_log and not exceptions_only:
                return_extra = deepcopy(extra)
                if _hide_input_from_return:
                    return_extra['input_data'] = HIDDEN_VALUE

                logger_inst.log(level=lvl, msg=f'return {func_name}', extra=return_extra)

            return result
        except Exception as exc:  # noqa
            error_msg = f'error in {func_name}'

            if send_log:
                logger_inst.exception(msg=error_msg, extra=extra if extra is not None else {})

            if exception_hook is not None:
                exception_hook(logger_inst, exc, extra)

            if hasattr(exc, 'return_value'):
                return exc.return_value

            raise

    return _log


def get_logged_args(
    params: inspect.FullArgSpec,
    args: tuple[Any],
    kwargs: dict[str, Any],
    hidden_params: Iterable,
) -> dict[str, Any]:
    """Return dict with function call argument names and their values casted to primitive types."""
    result = {}

    for i, v in enumerate(args[:len(params.args)]):
        arg_name = params.args[i]
        arg_value = _hide_items(v, arg_name, hidden_params)
        result[arg_name] = normalize_for_log(arg_value)

    varargs = params.varargs
    if varargs:
        if _hide_items(args[len(params.args):], varargs, hidden_params) == HIDDEN_VALUE:
            result['*args'] = f'hidden {len(args) - len(params.args)} args'
        else:
            result['*args'] = tuple(normalize_for_log(i) for i in args[len(params.args):])  # noqa: WPS441

    for k, v in kwargs.items():
        kwarg = _hide_items(v, k, hidden_params)
        result[k] = normalize_for_log(kwarg)

    return result


def normalize_for_log(value: Any) -> Any:
    """Cast any value to a primitive type."""
    if isinstance(value, bool) or value is None:
        return str(value)
    elif isinstance(value, dict):
        return {k: normalize_for_log(v) for k, v in value.items()}
    elif isinstance(value, (list, set, frozenset, tuple)):
        return type(value)(normalize_for_log(i) for i in value)

    return _get_log_repr(value)


def _get_log_repr(value: Any) -> Any:
    """Cast value of complex type to a primitive type."""
    if inspect.isclass(value):
        return str(value)

    has_log_id = hasattr(value, 'get_log_id')
    if has_log_id:
        return value.get_log_id()

    try:
        ujson.dumps(value)
    except TypeError:
        return str(value)

    return value


def _hide_items(item: Any, item_name: str, hidden_params: Iterable) -> Any:
    """Hide items according go configuration."""
    if item_name in hidden_params:
        return HIDDEN_VALUE

    hide_pointers = []

    for i in hidden_params:
        if re.match(item_name, i):
            pointer = i.split('__')[1:]
            if pointer not in hide_pointers:
                hide_pointers.append(pointer)

    if not hide_pointers:
        return item

    result = deepcopy(item)
    for i in hide_pointers:
        try:
            result = _hide_items_impl(result, i)
        except (KeyError, IndexError):
            pass

    return result


def _hide_items_impl(item: Any, pointers: List | Tuple):
    pointer = pointers[0]
    if isinstance(item, list):
        pointer = int(pointer)

    if isinstance(item[pointer], (dict, list)) and len(pointers) > 1:
        item[pointer] = _hide_items_impl(item[pointer], pointers[1:])
    else:
        item[pointer] = HIDDEN_VALUE

    return item
