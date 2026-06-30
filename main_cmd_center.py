"""Entry point for the Command Center application.

Initializes the Zenoh session, sets up the CommandCenterManager, 
binds the UI callbacks, and starts the dashboard loop.
"""
import json
from common.zenoh_utils import create_zenoh_session
from command_center.manager import CommandCenterManager
from command_center.dashboard import display_alert, render_telemetry_update, start_ui_loop

def main() -> None:
    """Bootstraps and runs the command center lifecycle.

    Raises:
      RuntimeError: If the application cannot bind to the Zenoh network.
    """
    try:
        # Initialize the Zenoh P2P session
        session = create_zenoh_session(is_peer=True)
        manager = CommandCenterManager(session)
        
        # Track active operators and signal loss timeouts
        active_operators = {}
        
        # Callback for liveliness events
        def on_liveliness_event(sample):
            """Handles liveliness token events (operator connect/disconnect)."""
            key = str(sample.key_expr)
            is_alive = sample.kind == "Put"  # Put = token created, Delete = token dropped
            
            # Extract operator_id from key: soccorso/TEAM/OPERATOR_ID/liveliness
            parts = key.split("/")
            if len(parts) >= 3:
                operator_id = parts[2]
                team = parts[1]
                
                if is_alive:
                    if operator_id not in active_operators:
                        display_alert(operator_id, "RECONNECTED")
                    active_operators[operator_id] = True
                else:
                    # Token dropped = signal lost
                    if operator_id in active_operators:
                        display_alert(operator_id, "SIGNAL_LOST")
                    active_operators[operator_id] = False
        
        # Callback for position/telemetry updates
        def on_position_update(sample):
            """Handles incoming telemetry from operators."""
            try:
                key = str(sample.key_expr)
                payload = sample.payload.to_bytes().decode("utf-8")
                data = json.loads(payload)
                
                # Extract operator_id from key
                parts = key.split("/")
                if len(parts) >= 3:
                    operator_id = parts[2]
                    
                    # Check for emergency status
                    if data.get("status") == "EMERGENCY":
                        display_alert(operator_id, "MAN_DOWN")
                    
                    # Render normal telemetry update
                    render_telemetry_update(operator_id, data)
                    
            except Exception as e:
                print(f"[ERROR] Failed to process position update: {e}")
        
        # Establish Zenoh subscriptions
        print("[INFO] Connecting to Zenoh network...")
        manager.monitor_liveliness("alpha", on_liveliness_event)
        manager.subscribe_positions("alpha", on_position_update)
        
        print("[INFO] Subscriptions established. Starting UI loop...")
        
        # Start the main dashboard loop
        start_ui_loop()
        
    except Exception as e:
        print(f"[FATAL] Command Center failed to initialize: {e}")
        raise RuntimeError(f"Cannot bind to Zenoh network: {e}")
    finally:
        # Cleanup
        try:
            manager.close()
            session.close()
            print("[INFO] Command Center shutdown complete.")
        except Exception as e:
            print(f"[ERROR] Cleanup failed: {e}")

if __name__ == "__main__":
    main()