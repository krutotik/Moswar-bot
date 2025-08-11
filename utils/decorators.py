import functools
from typing import Any, Callable

from utils.custom_logging import logger

F = Callable[..., Any]


def require_location_page(func: F) -> F:
    """
    Decorator that requires the driver to be on the location's main page (as determined by is_opened()).
    """

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.is_opened():
            logger.error(f"Driver is not on the required page ({self.BASE_URL}). Operation aborted.")
            return None
        return func(self, *args, **kwargs)

    return functools.update_wrapper(wrapper, func)


def require_page_prefix(prefix: str):
    """
    Decorator that requires the driver to be on a page whose URL starts with the given prefix.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if not self.driver.current_url.startswith(prefix):
                logger.error(f"Driver is not on a page starting with '{prefix}'. Operation aborted.")
                return None
            return func(self, *args, **kwargs)

        return functools.update_wrapper(wrapper, func)

    return decorator
