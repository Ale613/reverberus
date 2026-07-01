"""Simulates hardware sensors for the hackathon prototype.

Provides dummy data generators to simulate GPS coordinates and 
accelerometer events (e.g., detecting a fall/man-down scenario) 
without needing real physical hardware.
"""
import random
import time
from typing import Tuple

# Starting coordinates set to Cagliari, Sardinia for a realistic local test
_current_lat = 39.2238
_current_lon = 9.1217

_last_lat = None
_last_lon = None
_last_move_time = time.time()

_is_simulating_stop = False
_stop_start_time = 0

def read_gps() -> Tuple[float, float]:
    """Reads the current GPS coordinates.

    Returns:
      A tuple containing (latitude, longitude) as floats.
      
    Raises:
      IOError: If the simulated sensor cannot be read.
    """
    global _current_lat, _current_lon, _is_simulating_stop, _stop_start_time
    
    current_time = time.time()
    
    if not _is_simulating_stop and random.random() < 0.05: 
        _is_simulating_stop = True
        _stop_start_time = current_time
        print("\n[GPS STOP] The operator has stopped moving!")
        
    if _is_simulating_stop:
        if current_time - _stop_start_time > 20:
            _is_simulating_stop = False
            print("\n[GPS STOP] The operator has resumed moving!")
    else:
        # Random walk
        _current_lat += random.uniform(-0.0001, 0.0001)
        _current_lon += random.uniform(-0.0001, 0.0001)
        
    return (_current_lat, _current_lon)

def check_man_down_event(current_lat: float, current_lon: float) -> bool:
    """Checks if the GPS position hasn't changed for 30 seconds.

    Args:
      current_lat: The current latitude to check.
      current_lon: The current longitude to check.

    Returns:
      True if the position has been static for >= 120 seconds, False otherwise.
    """
    global _last_lat, _last_lon, _last_move_time
    
    current_time = time.time()
    
    if _last_lat is None or _last_lon is None:
        _last_lat = current_lat
        _last_lon = current_lon
        _last_move_time = current_time
        return False
        
    delta_lat = abs(current_lat - _last_lat)
    delta_lon = abs(current_lon - _last_lon)
    
    if delta_lat < 1e-6 and delta_lon < 1e-6:
        # L'operatore è nella stessa identica posizione. Da quanto tempo?
        if current_time - _last_move_time >= 12.0:
            return True 
    else:
        _last_lat = current_lat
        _last_lon = current_lon
        _last_move_time = current_time
        
    return False