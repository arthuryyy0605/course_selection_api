import logging
import time
from functools import wraps
from typing import Callable
from .setting import EnvironmentSettings


class Settings(EnvironmentSettings):
    logging_level: str = 'INFO'


def init_logger() -> logging.Logger:
    global logger
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.getLevelName(Settings().logging_level))
    return logger


logger = init_logger()


class PerfixAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['perfix'], msg), kwargs


def get_prefix_logger_adapter(perfix) -> logging.LoggerAdapter:
    return PerfixAdapter(logger, {'perfix': perfix})


def async_execution_time_logger_decorator(logger: logging.LoggerAdapter):
    def decorator(func):
        @wraps(func)
        async def async_timeit_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            action = 'Took'
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as exc:
                action = f'get {exc.__class__.__name__} in'
                raise exc
            finally:
                total_time = time.perf_counter() - start_time
                logger.debug(
                    f'Function {func.__name__} {action} {total_time:.4f} seconds')

        return async_timeit_wrapper

    return decorator


def execution_time_logger_decorator(logger: logging.LoggerAdapter):
    def decorator(func):
        @wraps(func)
        def timeit_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            action = 'Took'
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as exc:
                action = f'get {exc.__class__.__name__} in'
                raise exc
            finally:
                total_time = time.perf_counter() - start_time
                logger.debug(
                    f'Function {func.__name__} {action} {total_time:.4f} seconds')

        return timeit_wrapper

    return decorator


def async_input_output_logger_decorator(log_method: Callable[[str], None] = logging.debug):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            log_method(f"Calling {func.__name__} with args: {args} and kwargs: {kwargs}")
            try:
                result = await func(*args, **kwargs)
                log_method(f"{func.__name__} returned: {result}")
                return result
            except Exception as exc:
                log_method(f"Exception occurred in {func.__name__}: {exc}")
                raise exc

        return async_wrapper

    return decorator


def input_output_logger_decorator(log_method: Callable[[str], None] = logging.debug):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log_method(f"Calling {func.__name__} with args: {args} and kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                log_method(f"{func.__name__} returned: {result}")
                return result
            except Exception as exc:
                log_method(f"Exception occurred in {func.__name__}: {exc}")
                raise exc

        return wrapper

    return decorator
