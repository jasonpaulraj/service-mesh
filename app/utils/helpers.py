"""
Helper functions for the application.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Union[int, float, str, datetime]) -> str:
    """
    Format a timestamp to ISO format.
    
    Args:
        timestamp: Timestamp to format
        
    Returns:
        str: Formatted timestamp
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
            except ValueError:
                logger.warning(f"Unable to parse timestamp: {timestamp}")
                return str(timestamp)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        logger.warning(f"Unsupported timestamp type: {type(timestamp)}")
        return str(timestamp)
    
    return dt.isoformat()


def parse_duration(duration: str) -> int:
    """
    Parse a duration string into seconds.
    
    Args:
        duration: Duration string (e.g., "30s", "5m", "1h")
        
    Returns:
        int: Duration in seconds
    """
    if not duration:
        return 0
    
    unit = duration[-1].lower()
    try:
        value = int(duration[:-1])
    except ValueError:
        logger.warning(f"Unable to parse duration: {duration}")
        return 0
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    else:
        try:
            return int(duration)
        except ValueError:
            logger.warning(f"Unknown duration unit in: {duration}")
            return 0


def bytes_to_human_readable(bytes_value: Union[int, float]) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        bytes_value: Value in bytes
        
    Returns:
        str: Human-readable string
    """
    if not bytes_value:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    
    return f"{bytes_value:.2f} EB"


def filter_dict(data: Dict, keys_to_include: List[str]) -> Dict:
    """
    Filter a dictionary to include only specific keys.
    
    Args:
        data: Dictionary to filter
        keys_to_include: List of keys to include
        
    Returns:
        Dict: Filtered dictionary
    """
    return {k: v for k, v in data.items() if k in keys_to_include}
