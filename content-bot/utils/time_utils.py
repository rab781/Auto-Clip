"""
Utility functions for time formatting.
"""

def format_timestamp(seconds: float, format_type: str = 'srt') -> str:
    """
    Convert seconds to timestamp string.

    Args:
        seconds (float): Time in seconds.
        format_type (str): Format type ('srt' or 'ass').

    Returns:
        str: Formatted timestamp string.

    Note:
        Uses rounding to nearest millisecond/centisecond.
    """
    if format_type == 'srt':
        total_millis = round(seconds * 1000)
        hours = total_millis // 3600000
        minutes = (total_millis % 3600000) // 60000
        secs = (total_millis % 60000) // 1000
        millis = total_millis % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    elif format_type == 'ass':
        total_cs = round(seconds * 100)
        hours = total_cs // 360000
        minutes = (total_cs % 360000) // 6000
        secs = (total_cs % 6000) // 100
        centiseconds = total_cs % 100
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    else:
        raise ValueError(f"Unknown format type: {format_type}")
