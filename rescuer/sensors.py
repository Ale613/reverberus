"""Simulates hardware sensors for the hackathon prototype.

Provides dummy data generators to simulate GPS coordinates and 
accelerometer events (e.g., detecting a fall/man-down scenario) 
without needing real physical hardware.
"""
import random
from typing import Tuple

# Starting coordinates set to Cagliari, Sardinia for a realistic local test
_current_lat = 39.2238
_current_lon = 9.1217

def read_gps() -> Tuple[float, float]:
    """Reads the current GPS coordinates.

    Returns:
      A tuple containing (latitude, longitude) as floats.
      
    Raises:
      IOError: If the simulated sensor cannot be read.
    """
    global _current_lat, _current_lon
    try:
        # Simulate movement with a small random walk
        _current_lat += random.uniform(-0.0001, 0.0001)
        _current_lon += random.uniform(-0.0001, 0.0001)
        return (_current_lat, _current_lon)
    except Exception as e:
        raise IOError(f"Failed to read simulated GPS sensor: {e}")

def check_man_down_event() -> bool:
    """Checks the accelerometer for a sudden drop or lack of movement.

    Returns:
      True if a 'man-down' event is detected, False otherwise.
    """
    # 5% chance of triggering a man-down alert to simulate realistic anomalies
    return random.random() < 0.05