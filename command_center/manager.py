"""Manages the Command Center's interactions with the Zenoh network.

Responsible for subscribing to telemetry streams, monitoring liveliness 
tokens to detect operator emergencies, and initiating distributed queries 
(Store & Forward) to retrieve missing historical data.
"""
import zenoh
import json
from typing import Callable, Any
from common.config import get_key_expr

class CommandCenterManager:
    """Aggregates and supervises the state of all operators in the field."""

    def __init__(self, session: zenoh.Session):
        """Initializes the manager with a Zenoh network session.

        Args:
          session: The active Zenoh session for peer-to-peer communication.
        """
        self.session = session
        self.subscribers = []
        self.queryables = []

    def monitor_liveliness(self, team: str, callback: Callable[[Any], None]) -> None:
        """Subscribes to liveliness events to detect 'Man Down' emergencies.

        Uses a wildcard key to monitor all operators within a team. The callback 
        will receive events when tokens are created (put) or dropped (delete).

        Args:
          team: The identifier of the team to monitor (e.g., 'alpha').
          callback: The function to execute when a liveliness event occurs.

        Raises:
          ConnectionError: If the subscription to the Zenoh network fails.
        """
        try:
            # Subscribe to all liveliness tokens for this team using wildcard
            key_pattern = f"soccorso/{team}/*/liveliness"
            
            def liveliness_callback(sample):
                """Internal callback wrapper to parse and relay liveliness events."""
                try:
                    callback(sample)
                except Exception as e:
                    print(f"[ERROR] Liveliness callback failed: {e}")
            
            sub = self.session.declare_subscriber(key_pattern, liveliness_callback)
            self.subscribers.append(sub)
            
        except Exception as e:
            raise ConnectionError(f"Failed to subscribe to liveliness events: {e}")

    def subscribe_positions(self, team: str, callback: Callable[[Any], None]) -> None:
        """Subscribes to continuous real-time position updates for a team.

        Args:
          team: The identifier of the team to monitor.
          callback: The function to execute for every incoming telemetry payload.
        """
        try:
            # Subscribe to all position updates for this team using wildcard
            key_pattern = f"soccorso/{team}/*/position"
            
            def position_callback(sample):
                """Internal callback wrapper to parse and relay position data."""
                try:
                    callback(sample)
                except Exception as e:
                    print(f"[ERROR] Position callback failed: {e}")
            
            sub = self.session.declare_subscriber(key_pattern, position_callback)
            self.subscribers.append(sub)
            
        except Exception as e:
            print(f"[ERROR] Failed to subscribe to positions: {e}")

    def request_history(self, team: str, operator_id: str) -> list:
        """Executes a distributed query to retrieve historical data.

        Triggers a Z_GET request to the specific operator's Queryable node.

        Args:
          team: The identifier of the operator's team.
          operator_id: The unique identifier of the operator to query.

        Returns:
          A list of historical records from the operator's LocalStore.

        Raises:
          TimeoutError: If the operator's node does not respond to the query.
        """
        try:
            # Build the query key for this specific operator's history
            key = get_key_expr(team, operator_id, "history")
            
            # Execute the Z_GET (distributed query) with 5-second timeout
            replies = self.session.get(key, zenoh.GetOptions(timeout_ms=5000))
            
            history_data = []
            for reply in replies:
                try:
                    # Parse the JSON response from the Queryable
                    payload = reply.ok().payload.to_bytes().decode("utf-8")
                    data = json.loads(payload)
                    if isinstance(data, list):
                        history_data.extend(data)
                    else:
                        history_data.append(data)
                except Exception as e:
                    print(f"[ERROR] Failed to parse history response: {e}")
            
            return history_data
            
        except Exception as e:
            raise TimeoutError(f"Failed to retrieve history for {operator_id}: {e}")

    def close(self) -> None:
        """Cleanly closes all subscriptions and resources.

        Call this method before shutting down the Command Center.
        """
        for sub in self.subscribers:
            try:
                sub.close()
            except Exception as e:
                print(f"[ERROR] Failed to close subscriber: {e}")
        
        self.subscribers.clear()