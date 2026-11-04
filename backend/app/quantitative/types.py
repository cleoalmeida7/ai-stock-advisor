from dataclasses import dataclass


@dataclass(frozen=True)
class MetricValue:
    """
    Every scalar metric in this package returns one of these instead of a
    bare number - insufficient_data is an explicit, first-class outcome,
    never a silently-partial or guessed value.
    """

    value: float | None
    insufficient_data: bool
    observations_used: int
