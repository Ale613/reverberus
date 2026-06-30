"""Provides a text-based User Interface for the Command Center.

Renders real-time telemetry updates and triggers visual/auditory 
alerts in the terminal when an emergency event is detected.
"""
from typing import Dict, Any

def display_alert(operator_id: str, alert_type: str) -> None:
    """Displays a high-visibility alert message in the terminal.

    Args:
      operator_id: The ID of the operator experiencing the emergency.
      alert_type: The nature of the emergency (e.g., 'MAN_DOWN', 'SIGNAL_LOST').
    """
    pass

def render_telemetry_update(operator_id: str, data: Dict[str, Any]) -> None:
    """Prints a formatted telemetry update to the standard output.

    Args:
      operator_id: The ID of the operator sending the telemetry.
      data: The parsed dictionary containing latitude, longitude, and timestamp.
    """
    pass

def start_ui_loop() -> None:
    """Starts the main asynchronous loop for the terminal dashboard.

    Captures user input (e.g., keyboard interrupts or manual query triggers) 
    while keeping the application alive to receive Zenoh callbacks.
    """
    pass