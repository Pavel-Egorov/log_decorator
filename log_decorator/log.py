import inspect
import json
import logging
import re
import time
from copy import deepcopy
from uuid import uuid1

from wrapt import decorator

HIDE_ANNOTATION = 'hide'

HIDDEN_VALUE = 'hidden'

SECONDS_TO_MS = 1000

LOGS_COUNTER = {}


def get_logger(logger_name='service_logger'):
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    return logger


def log(
    logger_inst=get_logger(),
    lvl: int = logging.INFO,
    *,
    hide_output=False,
    hidden_params=(),
    exceptions_only=False,
    track_exec_time=False,
    frequency=None,
    exception_hook=None,
):
    # noinspection DuplicatedCode
    @decorator
    def _log(wrapped, instance, args, kwargs):
        func_name = f'{wrapped.__module__}.{wrapped.__qualname__}'
        extra = {'call_id': uuid1().hex, 'function': func_name}

        send_log = True

        if frequency is not None:
            log_counter = LOGS_COUNTER.setdefault(func_name, 0) + 1
            LOGS_COUNTER[func_name] = log_counter

            if log_counter % frequency != 0:
                send_log = False

        try:
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

            extra['result'] = normalize_for_log(result) if not hide_output else HIDDEN_VALUE

            if send_log and not exceptions_only:
                logger_inst.log(level=lvl, msg=f'return {func_name}', extra=extra)

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


def get_logged_args(params, args, kwargs, hidden_params):
    result = {}
    annotations = params.annotations

    for i, v in enumerate(args[:len(params.args)]):
        arg_name = params.args[i]
        arg_value = _hide_items(v, arg_name, annotations, hidden_params)
        result[arg_name] = normalize_for_log(arg_value)

    varargs = params.varargs
    if varargs:
        if _hide_items(args[len(params.args):], varargs, annotations, hidden_params) == HIDDEN_VALUE:
            result['*args'] = f'hidden {len(args) - len(params.args)} args'
        else:
            result['*args'] = tuple(normalize_for_log(i) for i in args[len(params.args):])

    for k, v in kwargs.items():
        if params.varkw and k not in params.kwonlyargs and k not in params.args:
            result[k] = HIDDEN_VALUE
            continue
        kwarg = _hide_items(v, k, annotations, hidden_params)
        result[k] = normalize_for_log(kwarg)

    return result


def normalize_for_log(value):
    if isinstance(value, bool) or value is None:
        return str(value)
    elif isinstance(value, dict):
        return {k: normalize_for_log(v) for k, v in value.items()}
    elif isinstance(value, (list, set, frozenset, tuple)):
        return type(value)(normalize_for_log(i) for i in value)
    else:
        return _get_log_repr(value)


def _get_log_repr(value):
    has_log_id = hasattr(value, 'get_log_id')
    if has_log_id:
        return value.get_log_id()

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _hide_items(item, item_name, annotations, hidden_params):
    if item_name in hidden_params:
        return HIDDEN_VALUE

    annotation = annotations.get(item_name)
    hide_annotation = annotation
    if annotation is None or isinstance(annotation, type):
        hide_annotation = []

    if isinstance(hide_annotation, str):
        hide_annotation = [hide_annotation]

    hidden_pointers = []
    for i in hide_annotation:
        if i == HIDE_ANNOTATION:
            return HIDDEN_VALUE
        if re.match(HIDE_ANNOTATION, str(i)):
            hidden_pointers.append(i.split('__')[1:])

    for i in hidden_params:
        if re.match(item_name, i):
            pointer = i.split('__')[1:]
            if pointer not in hidden_pointers:
                hidden_pointers.append(pointer)

    result = deepcopy(item)
    for i in hidden_pointers:
        try:
            result = _hide_items_impl(result, i)
        except (KeyError, IndexError):
            continue

    return result


def _hide_items_impl(item, pointers):
    pointer = pointers[0]
    if isinstance(item, list):
        pointer = int(pointers[0])

    if (isinstance(item[pointer], dict) or isinstance(item[pointer], list)) and len(pointers) > 1:
        item[pointer] = _hide_items_impl(item[pointer], pointers[1:])
    else:
        item[pointer] = HIDDEN_VALUE

    return item
