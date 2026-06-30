/**
 * Client-side logic for the Reverberus Command Center Dashboard
 * Handles WebSocket communication, map updates, and alert rendering
 */

let map;
let markers = {};
let alertsList = [];
const ALERT_HISTORY_MAX = 20;
let socket;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM loaded, initializing...");
    initializeMap();
    initializeWebSocket();
});

/**
 * Initializes the Leaflet map centered on Cagliari, Sardinia
 */
function initializeMap() {
    try {
        map = L.map('map').setView([39.2238, 9.1217], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);
        
        console.log("✓ Map initialized");
    } catch (e) {
        console.error("Map initialization failed:", e);
    }
}

/**
 * Initializes WebSocket connection to the Python backend
 */
function initializeWebSocket() {
    try {
        console.log("Attempting Socket.IO connection...");
        socket = io();
        
        // Connection successful
        socket.on("connect", () => {
            console.log("✓ WebSocket connected, ID:", socket.id);
            updateConnectionStatus("Online", "connected");
        });
        
        // Connection lost
        socket.on("disconnect", () => {
            console.log("✗ WebSocket disconnected");
            updateConnectionStatus("Offline", "disconnected");
        });
        
        // Receive telemetry updates
        socket.on("telemetry", (payload) => {
            console.log("📍 Telemetry received:", payload);
            handleTelemetryUpdate(payload.operator_id, payload.data);
        });
        
        // Receive alert events
        socket.on("alert", (payload) => {
            console.log("🚨 Alert received:", payload);
            handleAlert(payload.operator_id, payload.alert_type);
        });
        
        // Status messages
        socket.on("status", (payload) => {
            console.log("Status:", payload.message);
        });
        
        // Error handling
        socket.on("error", (error) => {
            console.error("❌ WebSocket error:", error);
        });
        
        socket.on("connect_error", (error) => {
            console.error("❌ Connection error:", error);
        });
        
    } catch (e) {
        console.error("WebSocket initialization failed:", e);
    }
}

/**
 * Updates the connection status indicator
 */
function updateConnectionStatus(status, className) {
    const statusElement = document.getElementById("ws-status");
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = className;
        console.log("Status updated:", status);
    }
}

/**
 * Handles incoming telemetry updates and updates the map
 */
function handleTelemetryUpdate(operatorId, data) {
    try {
        const lat = data.lat;
        const lon = data.lon;
        const status = data.status;
        const heartRate = data.heart_rate;
        
        // Validate coordinates
        if (typeof lat !== 'number' || typeof lon !== 'number') {
            console.error("Invalid coordinates:", lat, lon);
            return;
        }
        
        // Create or update marker
        if (markers[operatorId]) {
            // Update existing marker
            markers[operatorId].setLatLng([lat, lon]);
            console.log(`Updated marker: ${operatorId}`);
        } else {
            // Create new marker
            const markerColor = status === "EMERGENCY" ? "red" : "green";
            const markerIcon = L.icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-${markerColor}.png`,
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34]
            });
            
            const marker = L.marker([lat, lon], { icon: markerIcon })
                .bindPopup(`<b>${operatorId}</b><br>HR: ${heartRate} | ${status}`)
                .addTo(map);
            
            markers[operatorId] = marker;
            console.log(`Created marker: ${operatorId} at (${lat}, ${lon})`);
        }
    } catch (e) {
        console.error("Error handling telemetry update:", e);
    }
}

/**
 * Handles alert events from the backend
 */
function handleAlert(operatorId, alertType) {
    try {
        const timestamp = new Date().toLocaleTimeString("it-IT");
        
        let alertTitle = alertType;
        let alertIcon = "⚠️";
        
        if (alertType === "MAN_DOWN") {
            alertIcon = "🚨";
            alertTitle = "MAN DOWN!";
        } else if (alertType === "SIGNAL_LOST") {
            alertIcon = "📡";
            alertTitle = "SIGNAL LOST";
        } else if (alertType === "RECONNECTED") {
            alertIcon = "✓";
            alertTitle = "RECONNECTED";
        }
        
        const alertItem = {
            operator_id: operatorId,
            alert_type: alertType,
            timestamp: timestamp,
            icon: alertIcon,
            title: alertTitle
        };
        
        // Add to front of list and limit history
        alertsList.unshift(alertItem);
        if (alertsList.length > ALERT_HISTORY_MAX) {
            alertsList.pop();
        }
        
        console.log(`Alert added: ${operatorId} - ${alertType}. Total alerts: ${alertsList.length}`);
        
        // Update UI
        renderAlerts();
        
        // Flash the status for critical alerts
        if (alertType === "MAN_DOWN") {
            flashScreen("red");
        } else if (alertType === "SIGNAL_LOST") {
            flashScreen("orange");
        }
    } catch (e) {
        console.error("Error handling alert:", e);
    }
}

/**
 * Re-renders the alerts list in the sidebar
 */
function renderAlerts() {
    try {
        const alertsList_el = document.getElementById("alerts-list");
        if (!alertsList_el) {
            console.error("alerts-list element not found!");
            return;
        }
        
        // Clear existing items
        alertsList_el.innerHTML = "";
        
        if (alertsList.length === 0) {
            alertsList_el.innerHTML = '<li class="empty-state">In attesa di dati...</li>';
            console.log("No alerts to display");
            return;
        }
        
        // Render each alert
        alertsList.forEach((alert) => {
            const li = document.createElement("li");
            li.className = `alert-${alert.alert_type.toLowerCase()}`;
            li.innerHTML = `
                <span class="icon">${alert.icon}</span>
                <span class="content">
                    <strong>${alert.operator_id}</strong><br>
                    ${alert.title}<br>
                    <small>${alert.timestamp}</small>
                </span>
            `;
            alertsList_el.appendChild(li);
        });
        
        console.log(`Rendered ${alertsList.length} alerts`);
    } catch (e) {
        console.error("Error rendering alerts:", e);
    }
}

/**
 * Flash the screen with a warning color for critical alerts
 */
function flashScreen(color) {
    try {
        const main = document.querySelector("main");
        if (!main) return;
        
        const originalBg = main.style.backgroundColor;
        const originalOpacity = main.style.opacity;
        
        main.style.backgroundColor = color;
        main.style.opacity = "0.3";
        
        setTimeout(() => {
            main.style.backgroundColor = originalBg;
            main.style.opacity = originalOpacity;
        }, 500);
        
        // Sound alert
        playBeep();
    } catch (e) {
        console.error("Error flashing screen:", e);
    }
}

/**
 * Plays a simple beep sound for alerts
 */
function playBeep() {
    try {
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = context.createOscillator();
        const gainNode = context.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(context.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, context.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.5);
        
        oscillator.start(context.currentTime);
        oscillator.stop(context.currentTime + 0.5);
    } catch (e) {
        console.log("Audio not available");
    }
}

// Log when script loads
console.log("Script.js loaded");