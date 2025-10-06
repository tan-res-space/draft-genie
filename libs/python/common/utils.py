"""Utility functions for DraftGenie."""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


async def async_retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiplier for exponential backoff
        on_retry: Optional callback on retry
        
    Returns:
        Result of the function
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            if attempt == max_attempts:
                raise

            if on_retry:
                on_retry(attempt, e)

            delay = delay_seconds * (backoff_multiplier ** (attempt - 1))
            await asyncio.sleep(delay)

    # This should never be reached, but for type safety
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed without exception")


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string."""
    return datetime.fromisoformat(dt_str)


def calculate_percentage(value: float, total: float) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return (value / total) * 100


def round_to(value: float, decimals: int = 2) -> float:
    """Round to specified decimal places."""
    return round(value, decimals)


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks."""
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def is_valid_uuid(value: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result: Dict[str, Any] = {}
    for d in dicts:
        result.update(d)
    return result


def flatten_dict(
    data: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items: List[tuple[str, Any]] = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

