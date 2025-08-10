import functools
from typing import Any, Callable

from utils.custom_logging import logger

F = Callable[..., Any]


def require_location_page(func: F) -> F:
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.is_opened():
            logger.error(f"Driver is not on the required page ({self.BASE_URL}). Operation aborted.")
            return None
        return func(self, *args, **kwargs)

    return functools.update_wrapper(wrapper, func)
