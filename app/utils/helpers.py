"""
helpers.py - General utility functions.
"""

from datetime import datetime
from typing import Any, Dict, Optional


def timestamp_now() -> str:
    """Get current timestamp as ISO format string."""
    return datetime.utcnow().isoformat()


def calculate_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calculate a weighted average score.
    
    Args:
        scores: Dict of {category: score} where score is 0-100
        weights: Dict of {category: weight} where weights should sum to 1.0
    
    Returns:
        Weighted average score (0-100)
    """
    total_score = 0.0
    total_weight = 0.0

    for category, weight in weights.items():
        if category in scores and scores[category] is not None:
            total_score += scores[category] * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize if not all categories have scores
    return round(total_score / total_weight, 1)


def truncate_text(text: Optional[str], max_length: int = 200) -> Optional[str]:
    """Truncate text to a maximum length."""
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_score(score: Optional[float]) -> str:
    """Format a score for display."""
    if score is None:
        return "N/A"
    return f"{score:.0f}/100"


def dict_without_none(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}
