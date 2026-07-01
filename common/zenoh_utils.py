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
        conf = zenoh.Config()
    
        if is_peer:
            conf.insert_json5("mode", '"peer"')
        else:
            conf.insert_json5("mode", '"client"')
            
        # Optional: Even if it's a peer, you can tell it to look for a cloud router
        if connect_ip:
            endpoints = f'["tcp/{connect_ip}:7447"]'
            conf.insert_json5("connect/endpoints", endpoints)
                
        return zenoh.open(conf)
        
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Zenoh session: {e}")