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
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180.")
        
    return {
        "lat": float(lat),
        "lon": float(lon),
        "timestamp": float(timestamp)
    }

def create_liveliness_payload(status: str) -> Dict[str, Any]:
    """Constructs a payload for the liveliness token initialization.

    Args:
      status: The initial status string of the operator (e.g., 'ACTIVE').

    Returns:
      A dictionary representing the liveliness metadata.
    """
    return {
        "status": str(status)
    }