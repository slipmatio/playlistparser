def time_str_to_seconds(time: str) -> int:
    """
    Convert a time string to seconds.

    0:01:00 -> 60
    """
    try:
        secs = sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(time.split(":"))))
    except Exception:
        secs = 0
    return secs
