"""Provides utility functions to bootstrap the Zenoh P2P network.

Handles the configuration and initialization of Zenoh sessions
for both the Edge nodes (Rescuer) and the Command Center.
"""
import zenoh

def create_zenoh_session(is_peer: bool = True, connect_ip: str = None) -> zenoh.Session:
    """Initializes and returns a connected Zenoh session.

    Args:
      is_peer: If True, configures the session to act as a P2P node.
               Defaults to True.

    Returns:
      An active Zenoh Session object ready for pub/sub and queries.

    Raises:
      RuntimeError: If the Zenoh subsystem fails to initialize or connect.
    """
    try:
        # Initialize a default Zenoh configuration
        conf = zenoh.Config()
        
        # Explicitly set the networking mode
        if is_peer:
            conf.insert_json5("mode", '"peer"')
        else:
            conf.insert_json5("mode", '"client"')
            
        # Open and return the Zenoh session
        session = zenoh.open(conf)
        return session
        
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Zenoh session: {e}")