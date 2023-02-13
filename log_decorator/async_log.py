import inspect
import logging
import time
from copy import deepcopy
from types import FunctionType
from typing import Any, Iterable, Callable
from uuid import uuid1

from wrapt import decorator

from .log import HIDDEN_VALUE, LOGS_COUNTER, SECONDS_TO_MS, get_logged_args, get_logger, normalize_for_log


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
    Decorator to trace async function calls in logs.

    This decorator doesn't provide async logging, but only async function calls.
    To use with async code consider either stdout/UDP inputs or use approach like:
    https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block

    It logs function call, function return and any exceptions with separate log records.
    This high-level function is needed to pass additional parameters and customise _log behavior.
    """
    # noinspection DuplicatedCode
    @decorator
    async def _log(wrapped: FunctionType, instance: Any, args: tuple[Any], kwargs: dict[str, Any]) -> Any:
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

            result = await wrapped(*args, **kwargs)

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
                await exception_hook(logger_inst, exc, extra)

            if hasattr(exc, 'return_value'):
                return exc.return_value

            raise

    return _log
