"""Defines system-wide constants and key expression generators for Zenoh.

This module centralizes the taxonomy of the P2P network to avoid
hardcoded strings across the repository and prevent routing errors.
"""
from typing import Literal

BASE_PATH = "soccorso"

def get_key_expr(
    team: str, 
    operator_id: str, 
    topic_type: Literal["liveliness", "position", "history"]
) -> str:
    """Generates the formatted Zenoh key based on the established taxonomy.

    Args:
      team: The identifier for the rescue team (e.g., 'alpha').
      operator_id: The unique identifier for the operator on the ground.
      topic_type: The specific telemetry or event type to append to the path.

    Returns:
      The fully qualified Zenoh key expression string.

    Raises:
      ValueError: If the provided topic_type is not recognized.
    """
    if topic_type not in ["liveliness", "position", "history"]:
        raise ValueError(f"Unknown topic_type: {topic_type}")
    
    return f"{BASE_PATH}/{team}/{operator_id}/{topic_type}"