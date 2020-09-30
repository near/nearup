import functools


class NetworkError(Exception):
    """Designates a non-fatal networking error"""


def capture_and_raise(exception):
    """Capture any exception raised by the wrapped function and re-raise as the given exception."""
    def wrap(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as ex:
                raise exception() from ex

        return wrapped
    return wrap
