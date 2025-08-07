from enum import StrEnum


class EnemySearchType(StrEnum):
    """
    Enum for enemy search types.
    """

    WEAK = "weak"
    EQUAL = "equal"
    STRONG = "strong"
    BY_NAME = "by_name"
    BY_LEVEL = "by_level"


class ResetTimerType(StrEnum):
    """
    Enum for reset timer types.
    """

    ENERGY = "energy"
    SNICKERS = "snickers"
