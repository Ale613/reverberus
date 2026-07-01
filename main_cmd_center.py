"""Entry point for the Command Center application.

Initializes the Zenoh session, sets up the CommandCenterManager, 
binds the UI callbacks, and starts the dashboard loop.
"""
import zenoh
import json
import threading
import time
from common.zenoh_utils import create_zenoh_session
from command_center.manager import CommandCenterManager
from command_center.dashboard import display_alert, render_telemetry_update
from command_center.web_server import WebServer

def main() -> None:
    """Bootstraps and runs the command center lifecycle.

    Raises:
      RuntimeError: If the application cannot bind to the Zenoh network.
    """
    try:
        ROUTER_IP = "25.7.53.21"
        # Initialize the web server (runs on separate thread)
        print("[INFO] Starting web server...")
        web_server = WebServer(host="0.0.0.0", port=8080)
        web_thread = threading.Thread(target=lambda: web_server.run(debug=False), daemon=True)
        web_thread.start()
        time.sleep(1)  # Give Flask time to start
        
        # Initialize the Zenoh P2P session
        print("[INFO] Initializing Zenoh session...")
        #session = create_zenoh_session(is_peer=True)
        session = create_zenoh_session(is_peer=False, connect_ip= ROUTER_IP)
        manager = CommandCenterManager(session)
        
        cloud_publisher = session.declare_publisher("rescue/global/alerts")
        print("[INFO] Cloud Gateway active. Ready to forward critical data.")

        # Track active operators and signal loss timeouts
        active_operators = {}
        operator_emergency_states = {}

        # Callback for liveliness events
        def on_liveliness_event(sample):
            """Handles liveliness token events (operator connect/disconnect)."""
            try:
                key = str(sample.key_expr)
                is_alive = sample.kind == zenoh.SampleKind.PUT
                
                # Extract operator_id from key: soccorso/TEAM/OPERATOR_ID/liveliness
                parts = key.split("/")
                if len(parts) >= 3:
                    operator_id = parts[2]
                    team = parts[1]
                    
                    if is_alive:
                        if operator_id not in active_operators:
                            alert_msg = f"Operator {operator_id} RECONNECTED"
                            display_alert(operator_id, "RECONNECTED")
                            web_server.broadcast_alert(operator_id, "RECONNECTED")
                        active_operators[operator_id] = True
                    else:
                        # Token dropped = signal lost
                        if operator_id in active_operators:
                            alert_msg = f"Operator {operator_id} SIGNAL LOST"
                            display_alert(operator_id, "SIGNAL_LOST")
                            web_server.broadcast_alert(operator_id, "SIGNAL_LOST")
                        active_operators[operator_id] = False
            except Exception as e:
                print(f"[ERROR] Liveliness callback failed: {e}")
        
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
                    current_status = data.get("status")
                    
                    print(f"[TELEMETRY] Received from {operator_id}: {data}")
                    
                    # Logica di transizione degli stati di emergenza
                    if current_status == "EMERGENCY":
                        # Se non era già in emergenza, lancia l'allarme
                        if operator_emergency_states.get(operator_id) != "EMERGENCY":
                            operator_emergency_states[operator_id] = "EMERGENCY"
                            display_alert(operator_id, "MAN_DOWN")
                            web_server.broadcast_alert(operator_id, "MAN_DOWN")

                            print(f"[GATEWAY] Forwarding MAN_DOWN alert for {operator_id} to the Cloud!")
                            cloud_payload = json.dumps({
                                "operator_id": operator_id,
                                "team": "alpha",
                                "alert_type": "MAN_DOWN",
                                "timestamp": data.get("timestamp"),
                                "last_lat": data.get("lat"),
                                "last_lon": data.get("lon")
                            })
                            cloud_publisher.put(cloud_payload)
                            
                    elif current_status == "OK":
                        # Se era in emergenza e ora è OK, significa che ha ripreso a muoversi
                        if operator_emergency_states.get(operator_id) == "EMERGENCY":
                            operator_emergency_states[operator_id] = "OK"
                            display_alert(operator_id, "RESUMED MOVING")
                            web_server.broadcast_alert(operator_id, "OK")
                    
                    # Render normal telemetry update (terminal)
                    render_telemetry_update(operator_id, data)
                    
                    # Broadcast to web clients
                    print(f"[WEB] Broadcasting telemetry for {operator_id} to web clients...")
                    web_server.broadcast_telemetry(operator_id, data)
                    
            except Exception as e:
                print(f"[ERROR] Failed to process position update: {e}")
                import traceback
                traceback.print_exc()

        # Establish Zenoh subscriptions
        print("[INFO] Connecting to Zenoh network...")
        manager.monitor_liveliness("alpha", on_liveliness_event)
        manager.subscribe_positions("alpha", on_position_update)
        
        print("[INFO] Subscriptions established.")
        print("[INFO] Dashboard available at http://localhost:8080")
        
        # Keep the main thread alive to receive Zenoh callbacks
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutdown requested...")
        
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