import logging
import time
import functools
from typing import Callable, Tuple, Type


def get_logger(name: str = __name__):
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    return logging.getLogger(name)


def retry(
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """Decorator for retrying a function with exponential backoff.

    Usage:
    @retry(tries=3, delay=1)
    def call_api(...):
        ...
    """

    def deco_retry(f: Callable):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            last_exc = None
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    mtries -= 1
                    if mtries <= 0:
                        raise
                    time.sleep(mdelay)
                    mdelay *= backoff
            # If somehow not returned, raise last
            if last_exc:
                raise last_exc
        return f_retry

    return deco_retry
