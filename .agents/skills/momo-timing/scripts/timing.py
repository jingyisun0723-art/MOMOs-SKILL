"""Check the exact startup command and elapsed-time/account-usage bounds."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import re
import sys


TRIGGER = re.compile(r"timing(?=$|\s|[:：])\s*[:：]?\s*")


def activation(message):
    message = message.strip()
    match = TRIGGER.match(message)
    if not match:
        return {"triggered": False, "task": None}
    task = message[match.end() :].strip()
    return {"triggered": True, "task": task or None}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamps must be ISO 8601 strings with a timezone offset")
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("timestamps must include a timezone offset")
    return result


def number(value, field, minimum, maximum):
    if (
        type(value) not in (int, float)
        or not minimum <= value <= maximum
        or not math.isfinite(value)
    ):
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return value


def guard(data):
    now = timestamp(data["now"])
    if "deadline" in data:
        if "started_at" in data or "minutes" in data:
            raise ValueError("provide either deadline or started_at and minutes")
        deadline = timestamp(data["deadline"])
    else:
        start = timestamp(data["started_at"])
        if now < start:
            raise ValueError("now cannot precede started_at")
        minutes = number(data["minutes"], "minutes", 0, math.inf)
        if minutes == 0:
            raise ValueError("minutes must be positive")
        deadline = (start.astimezone(timezone.utc) + timedelta(minutes=minutes)).astimezone(
            start.tzinfo
        )

    reserve = number(data["reserve_percent"], "reserve_percent", 0, 100)
    windows = data.get("windows", {})
    if not isinstance(windows, dict):
        raise ValueError("windows must map names to used percentages or null")
    usage_allowed = data.get("usage_allowed")
    if usage_allowed is not None and type(usage_allowed) is not bool:
        raise ValueError("usage_allowed must be a boolean or null")

    remaining = {
        name: None if used is None else 100 - number(used, name, 0, 100)
        for name, used in windows.items()
    }
    seconds_left = (deadline - now).total_seconds()
    known = [value for value in remaining.values() if value is not None]

    if seconds_left <= 0:
        status = "deadline"
    elif usage_allowed is False:
        status = "usage_unavailable"
    elif any(value <= reserve for value in known):
        status = "reserve"
    elif not remaining or len(known) < len(remaining):
        status = "unknown"
    else:
        status = "within_bounds"

    return {
        "deadline": deadline.isoformat(),
        "seconds_left": max(0, seconds_left),
        "remaining_percent": remaining,
        "status": status,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("trigger", "guard"))
    command = parser.parse_args().command
    try:
        raw = sys.stdin.buffer.read().decode("utf-8-sig")
        if command == "trigger":
            result = activation(raw)
        else:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("guard input must be a JSON object")
            result = guard(data)
    except (KeyError, OverflowError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
