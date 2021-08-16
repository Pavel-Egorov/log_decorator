import inspect
import logging
import time
from uuid import uuid1

from wrapt import decorator

from .log import HIDDEN_VALUE, LOGS_COUNTER, SECONDS_TO_MS, get_logged_args, get_logger, normalize_for_log


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
    async def _log(wrapped, instance, args, kwargs):
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

            result = await wrapped(*args, **kwargs)

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
                await exception_hook(logger_inst, exc, extra)

            if hasattr(exc, 'return_value'):
                return exc.return_value

            raise

    return _log
