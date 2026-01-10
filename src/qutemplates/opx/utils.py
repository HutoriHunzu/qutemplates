"""OPX utility functions."""


def ns_to_clock_cycles(duration_ns: int) -> int:
    """Convert nanoseconds to OPX clock cycles.

    OPX operates at 1 GHz with 4ns clock cycles.

    Args:
        duration_ns: Duration in nanoseconds

    Returns:
        Duration in clock cycles (1 cycle = 4ns)
    """
    return int((duration_ns // 4) * 4)
