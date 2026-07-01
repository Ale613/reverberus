"""Web server for the Command Center dashboard with real-time WebSocket updates.

Provides HTTP serving of the UI and WebSocket channels for live telemetry streaming.
"""
from flask import Flask
from flask_socketio import SocketIO, emit
from pathlib import Path
from typing import Optional

class WebServer:
    """Manages the Flask web server and WebSocket connections."""

    def __init__(self, host: str = "localhost", port: int = 8080, manager=None):
        """Initializes the Flask application and SocketIO.

        Args:
          host: The hostname to bind to.
          port: The port number for the web server.
        """
        self.app = Flask(__name__, 
                        static_folder=str(Path(__file__).parent / "static"),
                        static_url_path="/static")
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.host = host
        self.port = port
        self.manager = manager
        self.connected_clients = set()
        
        # Setup routes and WebSocket handlers
        self._setup_routes()
        self._setup_websocket()

    def attach_manager(self, manager) -> None:
        """Attaches the manager used to service RPC-like requests."""
        self.manager = manager

    def _setup_routes(self):
        """Configures HTTP routes."""
        
        @self.app.route("/")
        def serve_dashboard():
            """Serves the main dashboard HTML."""
            static_dir = Path(__file__).parent / "static"
            index_path = static_dir / "index.html"
            
            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return "<h1>Dashboard HTML not found at " + str(index_path) + "</h1>", 404
        
        @self.app.route("/static/<path:filename>")
        def serve_static(filename):
            """Serves static files (CSS, JS, etc)."""
            return self.app.send_static_file(filename)
        
        print(f"[WEB] Static folder: {self.app.static_folder}")

    def _setup_websocket(self):
        """Configures WebSocket event handlers."""
        
        @self.socketio.on("connect")
        def handle_connect():
            """Handles new WebSocket client connections."""
            print(f"[WEB] Client connected: {__import__('uuid').uuid4().hex[:8]}")
            self.connected_clients.add(__import__('uuid').uuid4().hex)
            emit("status", {"message": "Connected to Command Center"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handles WebSocket client disconnections."""
            print("[WEB] Client disconnected")

        @self.socketio.on("request_history")
        def handle_request_history(payload):
            """Handles a manual history request from the dashboard."""
            try:
                team = payload.get("team")
                operator_id = payload.get("operator_id")

                if not self.manager:
                    return {"ok": False, "error": "History service is unavailable"}

                if not team or not operator_id:
                    return {"ok": False, "error": "Missing team or operator identifier"}

                history = self.manager.request_history(team, operator_id)
                print(f"[WEB] History requested for {team}/{operator_id} ({len(history)} records)")
                return {
                    "ok": True,
                    "team": team,
                    "operator_id": operator_id,
                    "history": history,
                }
            except Exception as e:
                print(f"[WEB ERROR] Failed to fulfill history request: {e}")
                return {"ok": False, "error": str(e)}

    def broadcast_telemetry(self, operator_id: str, data: dict, team: Optional[str] = None) -> None:
        """Broadcasts telemetry update to all connected clients."""
        try:
            self.socketio.emit("telemetry", {
                "operator_id": operator_id,
                "team": team,
                "data": data,
            })
            print(f"[WEB] Broadcast telemetry for {operator_id}")
        except Exception as e:
            print(f"[WEB ERROR] Failed to broadcast telemetry: {e}")

    def broadcast_alert(self, operator_id: str, alert_type: str, team: Optional[str] = None) -> None:
        """Broadcasts an alert event to all connected clients."""
        try:
            self.socketio.emit("alert", {
                "operator_id": operator_id,
                "team": team,
                "alert_type": alert_type,
            })
            print(f"[WEB] Broadcast alert: {operator_id} - {alert_type}")
        except Exception as e:
            print(f"[WEB ERROR] Failed to broadcast alert: {e}")

    def run(self, debug: bool = False):
        """Starts the Flask web server.

        Args:
          debug: Whether to run in debug mode.
        """
        print(f"[WEB] Starting server at http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)
