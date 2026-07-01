"""Entry point for the Rescuer Edge Node application.

Initializes the Zenoh session, sets up the RescuerNode, starts the 
dummy sensors, and enters the main publishing loop.
"""
import time
import random
from datetime import datetime
from common.zenoh_utils import create_zenoh_session
from rescuer.node import RescuerNode
from rescuer import sensors

def main() -> None:
    """Bootstraps and runs the rescuer node lifecycle.

    Raises:
      RuntimeError: If the initialization sequence fails at any point.
    """
    # Base configuration
    TEAM = "alpha"
    OPERATOR_ID = f"op_{random.randint(100, 999)}"
    
    print(f"Inizializzation Rescuer Node: {OPERATOR_ID} (Team: {TEAM})")
    
    # Inizializzation Zenoh session using the shared peer configuration
    session = create_zenoh_session(is_peer=True)
    node = RescuerNode(session, TEAM, OPERATOR_ID)
    
    # Start Zenoh services
    node.setup_liveliness()
    node.start_telemetry_publisher()
    node.setup_queryable_store()
    
    print("Rescuer Node active. Sending telemetry...")
    
    try:
        # Loop of pubblication (Sensor simulation)
        while True:
            # mock data for hackaton
            lat, lon = sensors.read_gps()
            is_man_down = sensors.check_man_down_event()
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "lat": lat,
                "lon": lon,
                "heart_rate": random.randint(60, 100),
                "status": "EMERGENCY" if is_man_down else "OK"
            }
            
            node.publish_position(data)
            
            if is_man_down:
                print(f"!!! ALERT: Man-down detected for {OPERATOR_ID} !!!")
            else:
                print(f"Posizione: {lat:.4f}, {lon:.4f} | Status: {data['status']}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nNode stop requested...")
    finally:
        node.close()
        session.close()
        print("Session Zenoh closed.")

if __name__ == "__main__":
    main()