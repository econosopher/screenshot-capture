from __future__ import annotations

import re
from typing import Iterable, List


_HMS_RE = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2}(?:\.\d{1,6})?)$")


def parse_time_to_seconds(value: str) -> float:
    """Parse a time string into seconds (float).

    Supported formats:
    - seconds: "12" or "12.34"
    - HH:MM:SS[.ms]: "01:02:03" or "01:02:03.250" or "02:03.25"
    - MM:SS[.ms]: "02:03" or "02:03.25"
    """
    s = value.strip()
    if not s:
        raise ValueError("Empty time value")

    # Try HH:MM:SS[.ms] or MM:SS[.ms]
    m = _HMS_RE.match(s)
    if m:
        h = int(m.group(1) or 0)
        m_ = int(m.group(2))
        sec = float(m.group(3))
        return h * 3600 + m_ * 60 + sec

    # Fallback: seconds (float)
    try:
        return float(s)
    except ValueError as exc:
        raise ValueError(f"Invalid time value: {value!r}") from exc


def parse_many(times: Iterable[str]) -> List[float]:
    out: List[float] = []
    for item in times:
        for part in str(item).split(","):
            part = part.strip()
            if not part:
                continue
            out.append(parse_time_to_seconds(part))
    return out


def seconds_to_name(seconds: float) -> str:
    """Format seconds into a filename-friendly HH-MM-SS.mmm string."""
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    # Use millisecond precision for names
    if h:
        return f"{h:02d}-{m:02d}-{int(s):02d}.{int((s-int(s))*1000):03d}"
    else:
        return f"{m:02d}-{int(s):02d}.{int((s-int(s))*1000):03d}"

