import random
import time


# Function to introduce a small random delay
def random_delay(min_time: float = 2, max_time: float = 3) -> None:
    """
    Pause execution for a random duration within a specified range.

    This function introduces a delay to simulate human-like behavior.

    Parameters:
        min_time (float): The minimum delay time in seconds. Default is 2 seconds.
        max_time (float): The maximum delay time in seconds. Default is 3 seconds.

    Example:
        random_delay(1, 3)  # Pauses execution for a random duration between 1 and 3 seconds.
    """
    time.sleep(random.uniform(min_time, max_time))
