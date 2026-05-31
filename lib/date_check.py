from datetime import datetime, timezone
import requests
import os
import base64
import logging

_logger = logging.getLogger(__name__)

TIME_SOURCES = [
    ("https://timeapi.io/api/time/current/zone?timeZone=UTC", lambda r: r.json()["dateTime"]),
    ("https://time.now/developer/api/timezone/UTC",            lambda r: r.json()["datetime"]),
]

def get_real_utc_time() -> datetime | None:
    """Fetch real UTC time from online sources. Returns None if all fail."""
    for url, extractor in TIME_SOURCES:
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            dt_str = extractor(r)
            if dt_str:
                # Trim or parse cleanly. ISO formats can have Z, +00:00, or decimal seconds.
                dt_str = dt_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(dt_str)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                else:
                    return dt.astimezone(timezone.utc)
        except (requests.RequestException, KeyError, ValueError, AttributeError) as e:
            _logger.debug("time_source_failed url=%s err=%s", url, e)
            continue

    # Last resort: use HTTP Date header from a reliable host
    try:
        r = requests.head("https://www.google.com", timeout=5)
        date_str = r.headers.get("Date", "")
        if date_str:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except (requests.RequestException, ValueError) as e:
        _logger.debug("http_head_time_failed err=%s", e)

    return None

def load_last_run(file_path: str) -> datetime | None:
    """Load and decode the last run time from an obfuscated file."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            encoded = f.read()
            decoded = base64.b64decode(encoded).decode("utf-8").strip()
            return datetime.fromisoformat(decoded).astimezone(timezone.utc)
    except (OSError, ValueError, UnicodeDecodeError):
        return None

def save_last_run(file_path: str, dt: datetime) -> None:
    """Encode and save the last run time to an obfuscated file."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        iso_str = dt.astimezone(timezone.utc).isoformat()
        encoded = base64.b64encode(iso_str.encode("utf-8"))
        with open(file_path, "wb") as f:
            f.write(encoded)
    except OSError:
        pass

def check_license(build_date: datetime, expiry_days: int, last_run_file: str) -> tuple[bool, str]:
    """
    Checks the evaluation license validity.
    Returns (is_valid, message).
    """
    # Enforce UTC timezone on build_date
    if build_date.tzinfo is None:
        build_date = build_date.replace(tzinfo=timezone.utc)
    else:
        build_date = build_date.astimezone(timezone.utc)

    # 1. Determine the current date/time
    online_time = get_real_utc_time()
    is_online = online_time is not None
    now = online_time if is_online else datetime.now(timezone.utc)

    # 2. Check for system clock rollback using the last run file
    last_run = load_last_run(last_run_file)
    if last_run is not None:
        # Enforce UTC
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        else:
            last_run = last_run.astimezone(timezone.utc)

        if now < last_run:
            # Clock rollback detected!
            return False, "License validation failed: clock rollback or invalid system date detected."

    # 3. Check if current time is before the build date
    if now < build_date:
        return False, "License validation failed: system date is set before the software build date."

    # 4. Check if license has expired
    delta = (now - build_date).days
    if delta > expiry_days:
        return False, f"This evaluation copy expired {delta - expiry_days} day(s) ago."

    # 5. License is valid, update the last run file
    # We update with the verified online time or current system time (whichever is later)
    # to prevent system clock tampering while offline.
    new_last_run = now
    if last_run is not None and last_run > new_last_run:
        new_last_run = last_run
    
    save_last_run(last_run_file, new_last_run)

    days_left = expiry_days - delta
    status_msg = "Evaluation license valid."
    if not is_online:
        status_msg += " (Offline mode)"
    
    return True, f"{status_msg} {days_left} day(s) remaining."