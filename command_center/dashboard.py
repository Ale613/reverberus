"""Provides a text-based User Interface for the Command Center.

Renders real-time telemetry updates and triggers visual/auditory 
alerts in the terminal when an emergency event is detected.
"""
from typing import Dict, Any
from datetime import datetime

def display_alert(operator_id: str, alert_type: str) -> None:
    """Displays a high-visibility alert message in the terminal.

    Args:
      operator_id: The ID of the operator experiencing the emergency.
      alert_type: The nature of the emergency (e.g., 'MAN_DOWN', 'SIGNAL_LOST').
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if alert_type == "MAN_DOWN":
        print(f"\n🚨 [ALERT] {timestamp} - OPERATOR {operator_id} MAN DOWN! 🚨")
        print("⚠️  IMMEDIATE ASSISTANCE REQUIRED ⚠️")
    elif alert_type == "SIGNAL_LOST":
        print(f"\n⚠️  [ALERT] {timestamp} - SIGNAL LOST FROM OPERATOR {operator_id}")
    elif alert_type == "RECONNECTED":
        print(f"\n✓ [INFO] {timestamp} - OPERATOR {operator_id} RECONNECTED")
    else:
        print(f"\n[ALERT] {timestamp} - {alert_type} from {operator_id}")

def render_telemetry_update(operator_id: str, data: Dict[str, Any]) -> None:
    """Prints a formatted telemetry update to the standard output.

    Args:
      operator_id: The ID of the operator sending the telemetry.
      data: The parsed dictionary containing latitude, longitude, and timestamp.
    """
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        lat = data.get("lat", "N/A")
        lon = data.get("lon", "N/A")
        heart_rate = data.get("heart_rate", "N/A")
        status = data.get("status", "UNKNOWN")
        
        status_icon = "🟢" if status == "OK" else "🔴"
        
        print(
            f"{status_icon} [{timestamp}] {operator_id}: "
            f"GPS({lat:.4f}, {lon:.4f}) | HR={heart_rate} | {status}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to render telemetry: {e}")

def start_ui_loop() -> None:
    """Starts the main asynchronous loop for the terminal dashboard.

    Captures user input (e.g., keyboard interrupts or manual query triggers) 
    while keeping the application alive to receive Zenoh callbacks.
    """
    import time
    
    print("\n" + "="*70)
    print("🛟 MAN DOWN RESCUE SYSTEM - COMMAND CENTER 🛟")
    print("="*70)
    print("Monitoring team operators in real-time...")
    print("Press CTRL+C to exit.\n")
    
    try:
        # Keep the main thread alive to receive Zenoh callbacks
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Shutting down Command Center...")
        return