import re

PRESET_DURATIONS = [
    (10, "10 minutes"),
    (15, "15 minutes"),
    (30, "30 minutes"),
    (45, "45 minutes"),
    (60, "1 hour"),
    (120, "2 hours"),
    (180, "3 hours"),
    (None, "Indefinite"),
]
PRESET_MINUTES = [minutes for minutes, _ in PRESET_DURATIONS]

# ponytail: single-unit only, extend regex to sum multiple h/m groups if combined format ("1h30m") is requested
_DURATION_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes)?$",
    re.IGNORECASE,
)


def parse_duration(text: str) -> float | None:
    """Parse free-form duration text ('12m', '2.5h', '45') into minutes.

    Empty text or "indefinite" means no limit (returns None). Raises ValueError.
    """
    text = text.strip()
    if not text or text.lower() == "indefinite":
        return None
    match = _DURATION_RE.match(text)
    if not match:
        raise ValueError(f"unrecognized duration: {text!r}")
    value = float(match.group(1))
    unit = (match.group(2) or "m").lower()
    minutes = value * 60 if unit.startswith("h") else value
    if minutes <= 0:
        raise ValueError(f"duration must be positive: {text!r}")
    return minutes


def _demo():
    assert parse_duration("12m") == 12
    assert parse_duration("2.5h") == 150
    assert parse_duration("45") == 45
    assert abs(parse_duration("1.5h") - 90) < 1e-9
    assert parse_duration("") is None
    assert parse_duration("indefinite") is None
    for bad in ["abc", "-5m", "0h", "h", "5x", "1h30m"]:
        try:
            parse_duration(bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad!r}")
    print("duration self-check OK")


if __name__ == "__main__":
    _demo()
