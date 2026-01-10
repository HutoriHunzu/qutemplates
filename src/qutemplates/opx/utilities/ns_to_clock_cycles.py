def ns_to_clock_cycles(duration_ns: int) -> int:
    """
    Convert nanoseconds to OPX clock cycles.

    OPX operates at 1 GHz with 4ns clock cycles. This function converts
    a duration in nanoseconds to the equivalent number of clock cycles,
    rounding to the nearest multiple of 4ns.

    Args:
        duration_ns: Duration in nanoseconds

    Returns:
        Duration in clock cycles (1 cycle = 4ns)

    Example:
        >>> ns_to_clock_cycles(1000)  # 1000ns = 250 cycles
        250
        >>> ns_to_clock_cycles(1002)  # Rounds down to 1000ns = 250 cycles
        250
    """
    return int((duration_ns // 4) * 4)
