"""Manages the local in-memory storage for the Store & Forward mechanism.

Implements a circular buffer to hold recent telemetry data. This ensures 
the device does not run out of memory while retaining enough history 
to answer distributed queries from the Command Center.
"""
from typing import List, Dict, Any
from collections import deque

class LocalStore:
    """A simple circular buffer for storing telemetry data."""

    def __init__(self, max_size: int = 100):
        """Initializes the LocalStore with a maximum capacity.

        Args:
          max_size: The maximum number of records to keep in memory.
        """
        self._store = deque(maxlen=max_size)

    def add_record(self, record: Dict[str, Any]) -> None:
        """Adds a new record to the store, evicting the oldest if full.

        Args:
          record: The telemetry data payload to store.
        """
        self._store.append(record)

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieves all currently stored records.

        Returns:
          A list of all telemetry records currently in the buffer.
        """
        return list(self._store)