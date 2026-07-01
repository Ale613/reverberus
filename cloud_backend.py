"""Simulated Cloud Backend for the Zenoh emergency network."""
import zenoh
import time
import json

def main() -> None:
    print("[CLOUD] Starting National Rescue Cloud Center...")
    
    # Initialize Zenoh in client mode (typical for cloud instances)
    conf = zenoh.Config()
    conf.insert_json5("mode", '"client"')
    ROUTER_IP = "25.7.53.21"
    conf.insert_json5("connect/endpoints", f'["tcp/{ROUTER_IP}:7447"]')
    
    session = zenoh.open(conf)
    
    # The global topic for critical alerts across all teams
    global_alert_topic = "rescue/global/alerts"
    
    def alert_callback(sample):
        """Triggered ONLY when a critical emergency is forwarded by an Edge Gateway."""
        payload = sample.payload.to_bytes().decode("utf-8")
        data = json.loads(payload)
        
        print("\n" + "="*50)
        print("🚨 [CRITICAL ALERT RECEIVED IN CLOUD] 🚨")
        print(f" Team:     {data.get('team', 'UNKNOWN')}")
        print(f" Operator: {data.get('operator_id', 'UNKNOWN')}")
        print(f" Type:     {data.get('alert_type', 'UNKNOWN')}")
        print(f" Location: {data.get('last_lat')}, {data.get('last_lon')}")
        print(f" Time:     {data.get('timestamp')}")
        print("="*50 + "\n")
        
    print(f"[CLOUD] Listening for filtered emergencies on: {global_alert_topic}")
    sub = session.declare_subscriber(global_alert_topic, alert_callback)
    
    try:
        # Keep the cloud server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[CLOUD] Shutting down...")
    finally:
        sub.close()
        session.close()

if __name__ == "__main__":
    main()