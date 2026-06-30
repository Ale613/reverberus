"""Core logic for the Edge node running on the rescuer's device.

This module integrates Zenoh to handle liveliness tokens, telemetry 
publishing, and responding to historical data queries.
"""
import zenoh
import json
from typing import Dict, Any
from rescuer.local_store import LocalStore

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
        self.base_path = f"telemetry/{self.team}/{self.operator_id}"
        self.pub = None
        self.queryable = None

    def start_liveliness_token(self) -> None:
        """Declares a Zenoh Liveliness Token for the operator.

        If the node disconnects or crashes, Zenoh will automatically 
        notify subscribers (Command Center) of the token drop.
        """
        key = f"liveliness/{self.team}/{self.operator_id}"
        self.session.liveliness.declare_token(key)

    def start_telemetry_publisher(self) -> None:
        """Declares a Zenoh publisher for real-time GPS coordinates."""
        self.pub = self.session.declare_publisher(f"{self.base_path}/pos")

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
        def callback(query):
            # Reply with the content of our local store as JSON
            data = json.dumps(self.store.get_all())
            query.reply(query.key_expr, data)

        self.queryable = self.session.declare_queryable(
            f"{self.base_path}/history", callback
        )