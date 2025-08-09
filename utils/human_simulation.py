import random
import time


# Function to introduce a small random delay
def random_delay(min_time: float = 3, max_time: float = 4) -> None:
    """
    Pause execution for a random duration within a specified range.

    This function introduces a delay to simulate human-like behavior.

    Parameters:
        min_time (float): The minimum delay time in seconds. Default is 3 seconds.
        max_time (float): The maximum delay time in seconds. Default is 4 seconds.

    Example:
        random_delay(1, 3)  # Pauses execution for a random duration between 1 and 3 seconds.
    """
    if max_time < min_time:
        raise ValueError("max_time must be greater than or equal to min_time")

    if min_time < 0 or max_time < 0:
        raise ValueError("min_time and max_time must be non-negative")

    max_time = max(min_time, max_time)
    time.sleep(random.uniform(min_time, max_time))
