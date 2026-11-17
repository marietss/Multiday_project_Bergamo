"""One representation for project-owned event timestamps: aware UTC ISO 8601."""
from datetime import datetime, timezone


def utc_isoformat(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('A timezone-aware datetime is required.')
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds')
