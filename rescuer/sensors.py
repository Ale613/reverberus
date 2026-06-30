"""Simulates hardware sensors for the hackathon prototype.

Provides dummy data generators to simulate GPS coordinates and 
accelerometer events (e.g., detecting a fall/man-down scenario) 
without needing real physical hardware.
"""
from typing import Tuple

def read_gps() -> Tuple[float, float]:
    """Reads the current GPS coordinates.

    Returns:
      A tuple containing (latitude, longitude) as floats.
      
    Raises:
      IOError: If the simulated sensor cannot be read.
    """
    pass

def check_man_down_event() -> bool:
    """Checks the accelerometer for a sudden drop or lack of movement.

    Returns:
      True if a 'man-down' event is detected, False otherwise.
    """
    pass