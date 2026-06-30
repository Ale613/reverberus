"""Defines the data schemas and payloads for the IoT network.

Provides standardized payload structures to ensure that all data 
passed through Zenoh is well-formed and easy to parse by subscribers.
"""
from typing import Dict, Any

def create_position_payload(lat: float, lon: float, timestamp: float) -> Dict[str, Any]:
    """Constructs a standardized dictionary for position telemetry.

    Args:
      lat: The latitude of the operator.
      lon: The longitude of the operator.
      timestamp: The Unix epoch time of the GPS reading.

    Returns:
      A dictionary representing the serialized payload ready to be sent via Zenoh.
      
    Raises:
      ValueError: If latitude or longitude values are out of valid bounds.
    """
    pass

def create_liveliness_payload(status: str) -> Dict[str, Any]:
    """Constructs a payload for the liveliness token initialization.

    Args:
      status: The initial status string of the operator (e.g., 'ACTIVE').

    Returns:
      A dictionary representing the liveliness metadata.
    """
    pass