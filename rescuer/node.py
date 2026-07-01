"""Core logic for the Edge node running on the rescuer's device.

This module integrates Zenoh to handle telemetry publishing and responding 
to historical data queries via the Store & Forward mechanism.
"""
import zenoh
import json
from typing import Dict, Any
from rescuer.local_store import LocalStore
from common.config import get_key_expr

class RescuerNode:
    """Manages all Zenoh network interactions for a single operator."""

    def __init__(self, session: zenoh.Session, team: str, operator_id: str):
        """Initializes the RescuerNode with its identity and network session.

        Args:
          session: The active Zenoh session for peer-to-peer communication.
          team: The identifier of the team (e.g., 'alpha').
          operator_id: The unique identifier for this operator.
        """
        self.session = session
        self.team = team
        self.operator_id = operator_id
        self.store = LocalStore(max_size=100)
        self.pub = None
        self.queryable = None
        self.liveliness_token = None

    def setup_liveliness(self) -> None:
        """Declares a Liveliness token for this specific operator."""
        # We create a specific path for liveliness, e.g., 'team/alpha/op_123/liveliness'
        key = get_key_expr(self.team, self.operator_id, "liveliness")
        
        self.liveliness_token = self.session.liveliness().declare_token(key)
        print(f"[ZENOH] Liveliness token declared on: {key}")

    def start_telemetry_publisher(self) -> None:
        """Declares a Zenoh publisher for real-time telemetry."""
        key = get_key_expr(self.team, self.operator_id, "position")
        self.pub = self.session.declare_publisher(key)

    def publish_position(self, data: Dict[str, Any]) -> None:
        """Publishes the position payload to the telemetry topic.

        Args:
          data: The dictionary payload containing position and timestamp.

        Raises:
          RuntimeError: If the publisher has not been declared yet.
        """
        if self.pub is None:
            raise RuntimeError("Publisher not initialized. Call start_telemetry_publisher first.")
        
        # Store locally and publish
        self.store.add_record(data)
        self.pub.put(json.dumps(data))

    def setup_queryable_store(self) -> None:
        """Sets up a Zenoh Queryable to handle historical data requests.

        Registers a callback that retrieves data from the LocalStore 
        and replies to the incoming query via the Zenoh session.
        """
        key = get_key_expr(self.team, self.operator_id, "history")
        
        def callback(query):
            """Internal queryable callback to serve historical data."""
            try:
                # Reply with the content of our local store as JSON
                data = json.dumps(self.store.get_all())
                query.reply(query.key_expr, data)
            except Exception as e:
                print(f"[ERROR] Queryable callback failed: {e}")

        self.queryable = self.session.declare_queryable(key, callback)

    def close(self) -> None:
        """Cleanly closes all Zenoh resources.

        Sets references to None to allow garbage collection.
        Call this method before shutting down the node.
        """
        # In Zenoh, basta eliminare il riferimento all'oggetto.
        # Non esiste il metodo .close() per publisher e queryable.
        if self.pub is not None:
            self.pub = None
        
        if self.queryable is not None:
            self.queryable = None

        if self.liveliness_token is not None:
            self.liveliness_token = None