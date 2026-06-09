"""
file_manager.py - File and directory management utilities.
"""

import os
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


def ensure_directory(dir_path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    Returns the absolute path.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return str(path.absolute())


def get_reports_dir() -> str:
    """Get the reports directory path, creating it if needed."""
    reports_dir = os.path.join(os.getcwd(), "reports")
    return ensure_directory(reports_dir)


def get_report_path(business_id: int, extension: str = "html") -> str:
    """Generate a report file path for a business."""
    reports_dir = get_reports_dir()
    filename = f"report_business_{business_id}.{extension}"
    return os.path.join(reports_dir, filename)


def save_file(filepath: str, content: str) -> bool:
    """Save content to a file."""
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            ensure_directory(parent_dir)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"File saved: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving file {filepath}: {e}")
        return False


def read_file(filepath: str) -> str | None:
    """Read content from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None


def file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return os.path.isfile(filepath)
