const DASHBOARD_STATE = {
    map: null,
    socket: null,
    operators: new Map(),
    alerts: [],
    filters: { query: "", team: "all", status: "all" },
    selectedOperatorId: null
};

const ALERT_LIMIT = 40;
const HISTORY_LIMIT = 12;

const SVG_OPERATOR = `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 2a4.25 4.25 0 0 0-4.25 4.25A4.25 4.25 0 0 0 12 10.5a4.25 4.25 0 0 0 4.25-4.25A4.25 4.25 0 0 0 12 2Zm0 10.5c-4.4 0-8 2.67-8 5.97V21h16v-2.53c0-3.3-3.6-5.97-8-5.97Z"/>
    </svg>
`;

document.addEventListener("DOMContentLoaded", () => {
    bindControls();
    initializeMap();
    initializeSocket();
    renderDashboard();
});

function bindControls() {
    const searchInput = document.getElementById("operator-search");
    const teamFilter = document.getElementById("team-filter");
    const statusFilter = document.getElementById("status-filter");

    if (searchInput) searchInput.addEventListener("input", (e) => { DASHBOARD_STATE.filters.query = e.target.value.trim().toLowerCase(); renderDashboard(); });
    if (teamFilter) teamFilter.addEventListener("change", (e) => { DASHBOARD_STATE.filters.team = e.target.value; renderDashboard(); });
    if (statusFilter) statusFilter.addEventListener("change", (e) => { DASHBOARD_STATE.filters.status = e.target.value; renderDashboard(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeContextMenu(); });
}

function initializeMap() {
    try {
        DASHBOARD_STATE.map = new maplibregl.Map({
            container: 'map',
            style: {
                version: 8,
                sources: {
                    'osm': { type: 'raster', tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' }
                },
                layers: [{ id: 'osm-tiles', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19 }]
            },
            center: [9.1217, 39.2238],
            zoom: 13
        });
        DASHBOARD_STATE.map.on("click", closeContextMenu);
    } catch (error) {
        console.error("Map initialization failed:", error);
    }
}

function initializeSocket() {
    try {
        DASHBOARD_STATE.socket = io();
        DASHBOARD_STATE.socket.on("connect", () => updateConnectionStatus("Online", "status-pill--online"));
        DASHBOARD_STATE.socket.on("disconnect", () => updateConnectionStatus("Offline", "status-pill--disconnected"));
        DASHBOARD_STATE.socket.on("telemetry", handleTelemetry);
        DASHBOARD_STATE.socket.on("alert", handleAlert);
        DASHBOARD_STATE.socket.on("status", (p) => { if (p && p.message) console.info(p.message); });
        DASHBOARD_STATE.socket.on("connect_error", () => updateConnectionStatus("Offline", "status-pill--disconnected"));
    } catch (error) {
        console.error("WebSocket initialization failed:", error);
    }
}

function updateConnectionStatus(text, className) {
    const el = document.getElementById("ws-status");
    if (el) { el.textContent = text; el.className = `status-pill ${className}`; }
}

function updateOperatorMarker(operator) {
    if (!DASHBOARD_STATE.map || operator.latitude === null || operator.longitude === null) return;

    const className = `operator-marker ${getMarkerClass(operator)}`;
    const color = getMarkerColor(operator);

    if (!operator.marker) {
        const el = document.createElement('div');
        el.className = className;
        el.style.color = color;
        el.innerHTML = `${SVG_OPERATOR}<span class="operator-marker__badge"></span>`;
        
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            openContextMenu(operator.operatorId, operator.team, [operator.longitude, operator.latitude]);
        });

        operator.marker = new maplibregl.Marker({ element: el })
            .setLngLat([operator.longitude, operator.latitude])
            .addTo(DASHBOARD_STATE.map);
    } else {
        const el = operator.marker.getElement();
        el.className = className;
        el.style.color = color;
        operator.marker.setLngLat([operator.longitude, operator.latitude]);
    }
}

function handleTelemetry(payload) {
    try {
        const operatorId = payload.operator_id;
        const team = payload.team || "unknown";
        const data = payload.data || {};
        const latitude = Number(data.lat);
        const longitude = Number(data.lon);
        const heartRate = Number(data.heart_rate);

        if (!operatorId || !Number.isFinite(latitude) || !Number.isFinite(longitude)) return;

        const operator = ensureOperator(operatorId, team);
        operator.latitude = latitude;
        operator.longitude = longitude;
        operator.lastSeenAt = new Date();
        operator.lastSeenLabel = operator.lastSeenAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

        if (Number.isFinite(heartRate)) {
            operator.heartRate = heartRate;
            operator.trend = pushTrend(operator.trend, heartRate);
        }

        const normalizedStatus = normalizeTelemetryStatus(data.status);

        // Se riceve telemetria, significa che è connesso
        if (operator.connectionState === "disconnected") {
            operator.connectionState = "online";
        }
        operator.telemetryState = normalizedStatus;

        if (normalizedStatus === "man_down") {
            operator.alertState = "man_down";
        } else if (operator.alertState === "man_down" && normalizedStatus === "online") {
            operator.alertState = "idle"; // L'uomo si rialza e riprende a muoversi
        }

        if (normalizedStatus === "online") resolveOpenAlertForOperator(operatorId);

        updateOperatorMarker(operator);
        renderDashboard();
    } catch (error) { console.error("Telemetry error:", error); }
}

function handleAlert(payload) {
    try {
        const operatorId = payload.operator_id;
        const team = payload.team || inferTeam(operatorId);
        const alertType = String(payload.alert_type || "").toUpperCase();

        if (!operatorId || !alertType) return;

        const operator = ensureOperator(operatorId, team);
        const timestamp = new Date();

        if (alertType === "SIGNAL_LOST") {
            operator.connectionState = "disconnected";
            operator.telemetryState = "offline";
            operator.alertState = "signal_lost";
        } else if (alertType === "RECONNECTED") {
            operator.connectionState = "online";
            operator.telemetryState = "online";
            operator.alertState = "idle";
        }

        if (alertType === "OK" || alertType === "RECONNECTED") {
            resolveOpenAlertForOperator(operatorId);
        } else {
            const activeAlert = {
                id: buildId("alert"),
                operatorId,
                team,
                type: alertType,
                title: getAlertTitle(alertType),
                createdAt: timestamp,
                createdLabel: timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
            };
            DASHBOARD_STATE.alerts.unshift(activeAlert);
            DASHBOARD_STATE.alerts = DASHBOARD_STATE.alerts.slice(0, ALERT_LIMIT);
            
            if (alertType === "MAN_DOWN") {
                operator.alertState = "man_down";
                flashWorkspace(); 
                playBeep();
            }
        }

        updateOperatorMarker(operator);
        renderDashboard();
    } catch (error) { console.error("Alert error:", error); }
}

function ensureOperator(operatorId, team) {
    if (!DASHBOARD_STATE.operators.has(operatorId)) {
        DASHBOARD_STATE.operators.set(operatorId, {
            operatorId, team, latitude: null, longitude: null, heartRate: null,
            telemetryState: "offline", connectionState: "offline", alertState: "idle",
            trend: [], lastSeenLabel: "--:--:--", marker: null
        });
    }
    const operator = DASHBOARD_STATE.operators.get(operatorId);
    operator.team = team || operator.team || "unknown";
    return operator;
}

function inferTeam(operatorId) { return DASHBOARD_STATE.operators.get(operatorId)?.team || "unknown"; }

function normalizeTelemetryStatus(status) {
    const n = String(status || "").toUpperCase();
    if (n === "EMERGENCY") return "man_down";
    if (n === "OK" || n === "ACTIVE" || n === "RESOLVED" || n === "RECONNECTED") return "online";
    if (n === "SIGNAL_LOST") return "disconnected";
    return n ? n.toLowerCase() : "offline";
}

function getMarkerClass(operator) {
    if (operator.alertState === "man_down") return "operator-marker--man_down";
    if (operator.connectionState === "disconnected") return "operator-marker--disconnected";
    return "operator-marker--online";
}

function getMarkerColor(operator) {
    if (operator.alertState === "man_down") return "var(--danger)";
    if (operator.connectionState === "disconnected") return "var(--archive)";
    return "var(--online)";
}

function pushTrend(series, value) { return [...series, value].slice(-HISTORY_LIMIT); }

function renderDashboard() {
    renderFilterOptions();
    renderOperators();
    renderAlerts();
    updateCounters();
}

function renderFilterOptions() {
    const teamFilter = document.getElementById("team-filter");
    if (!teamFilter) return;
    const selected = teamFilter.value || "all";
    const teams = Array.from(new Set(Array.from(DASHBOARD_STATE.operators.values()).map((op) => op.team).filter(Boolean))).sort();
    teamFilter.innerHTML = '<option value="all">All teams</option>';
    teams.forEach((t) => { const opt = document.createElement("option"); opt.value = t; opt.textContent = t; teamFilter.appendChild(opt); });
    teamFilter.value = teams.includes(selected) ? selected : "all";
}

function getUiStatus(operator) {
    if (operator.alertState === "man_down") return "man_down";
    if (operator.connectionState === "disconnected") return "signal_lost";
    if (operator.telemetryState === "online" || operator.connectionState === "online") return "online";
    return "offline";
}

function getFilteredOperators() {
    return Array.from(DASHBOARD_STATE.operators.values()).filter((op) => {
        const q = !DASHBOARD_STATE.filters.query || op.operatorId.toLowerCase().includes(DASHBOARD_STATE.filters.query);
        const t = DASHBOARD_STATE.filters.team === "all" || op.team === DASHBOARD_STATE.filters.team;
        const s = DASHBOARD_STATE.filters.status === "all" || getUiStatus(op) === DASHBOARD_STATE.filters.status;
        return q && t && s;
    }).sort((a, b) => a.operatorId.localeCompare(b.operatorId));
}

function renderOperators() {
    const list = document.getElementById("operators-list");
    if (!list) return;
    const operators = getFilteredOperators();
    if (operators.length === 0) { list.innerHTML = '<li class="empty-state">No operators match the selected filters.</li>'; return; }
    list.innerHTML = operators.map(renderOperatorCard).join("");
}

function renderOperatorCard(op) {
    const st = getUiStatus(op);
    const loc = op.latitude !== null ? `${op.latitude.toFixed(4)}, ${op.longitude.toFixed(4)}` : "Awaiting GPS fix";
    const hr = Number.isFinite(op.heartRate) ? `${op.heartRate} bpm` : "No heart-rate data";
    const sel = DASHBOARD_STATE.selectedOperatorId === op.operatorId ? "operator-card--selected" : "";

    return `
        <li class="operator-card ${sel}" data-operator-id="${escapeHtml(op.operatorId)}">
            <div class="operator-card__meta">
                <div class="operator-card__topline">
                    <span class="operator-card__id">${escapeHtml(op.operatorId)}</span>
                    <span class="operator-card__status operator-card__status--${st}">${escapeHtml(st.replace(/_/g, " "))}</span>
                </div>
                <div class="operator-card__team">Team ${escapeHtml(op.team || "unknown")}</div>
                <div class="operator-card__details">
                    <span>${escapeHtml(hr)}</span>
                    <span>${escapeHtml(loc)}</span>
                    <span>Updated ${escapeHtml(op.lastSeenLabel || "--:--:--")}</span>
                </div>
                <div class="operator-card__sparkline">${renderSparkline(op.trend, op.connectionState)}</div>
            </div>
            <div class="operator-card__actions">
                <div class="operator-marker ${getMarkerClass(op)}" style="color: ${getMarkerColor(op)};">${SVG_OPERATOR}<span class="operator-marker__badge"></span></div>
            </div>
        </li>
    `;
}

function renderSparkline(series, connectionState) {
    const vals = Array.isArray(series) && series.length ? series : [0, 0, 0, 0];
    const width = 120, height = 28, padding = 2;
    const min = Math.min(...vals), max = Math.max(...vals), span = Math.max(max - min, 1);
    const gradientId = `spark-${Math.random().toString(16).slice(2, 8)}`;
    const stroke = connectionState === "disconnected" ? "var(--archive)" : "var(--online)";

    const pts = vals.map((val, i) => `${(padding + (i * (width - padding * 2)) / Math.max(vals.length - 1, 1)).toFixed(1)},${(height - padding - ((val - min) / span) * (height - padding * 2)).toFixed(1)}`).join(" ");

    return `
        <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true" focusable="false">
            <defs>
                <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(45, 213, 138, 0.42)" /><stop offset="100%" stop-color="rgba(45, 213, 138, 0.03)" /></linearGradient>
            </defs>
            <polyline points="${pts}" fill="none" stroke="${stroke}" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round" />
            <polygon points="${pts} ${width - padding},${height - padding} ${padding},${height - padding}" fill="url(#${gradientId})" opacity="0.5"></polygon>
        </svg>
    `;
}

function renderAlerts() {
    const list = document.getElementById("alerts-list");
    if (!list) return;
    list.innerHTML = DASHBOARD_STATE.alerts.length
        ? DASHBOARD_STATE.alerts.map(renderAlertCard).join("")
        : '<li class="empty-state">No active alerts.</li>';
    attachAlertActions(list);
}

function renderAlertCard(alert) {
    const cdClass = alert.type === "MAN_DOWN" ? "alert-card--man_down" : "alert-card--signal_lost";
    return `
        <li class="alert-card ${cdClass}" data-alert-id="${escapeHtml(alert.id)}">
            <div class="alert-card__row">
                <div>
                    <div class="alert-card__title">${escapeHtml(alert.operatorId)} · ${escapeHtml(alert.title)}</div>
                    <div class="alert-card__meta">Team ${escapeHtml(alert.team || "unknown")} · ${escapeHtml(alert.createdLabel)}</div>
                </div>
                <span class="alert-card__status alert-card__status--active">ACTIVE</span>
            </div>
            <div class="alert-card__actions">
                <button class="action-button action-button--danger" data-action="clear" data-alert-id="${escapeHtml(alert.id)}">Dismiss</button>
            </div>
        </li>
    `;
}

function attachAlertActions(container) {
    container.querySelectorAll("button[data-action]").forEach((btn) => {
        btn.addEventListener("click", () => handleAlertAction(btn.dataset.action, btn.dataset.alertId));
    });
}

function handleAlertAction(action, alertId) {
    if (action === "clear") {
        const idx = DASHBOARD_STATE.alerts.findIndex((item) => item.id === alertId);
        if (idx !== -1) {
            const alert = DASHBOARD_STATE.alerts[idx];
            DASHBOARD_STATE.alerts.splice(idx, 1);
            
            // Pulisce lo stato se l'allarme eliminato manualmente è l'ultimo
            const operator = DASHBOARD_STATE.operators.get(alert.operatorId);
            if (operator) {
                if (operator.alertState === "man_down" && alert.type === "MAN_DOWN") operator.alertState = "idle";
                if (operator.alertState === "signal_lost" && alert.type === "SIGNAL_LOST") operator.alertState = "idle";
                updateOperatorMarker(operator);
            }
        }
    }
    renderDashboard();
}

function resolveOpenAlertForOperator(operatorId) {
    // Rimuove tutti gli allarmi legati a questo operatore
    DASHBOARD_STATE.alerts = DASHBOARD_STATE.alerts.filter((item) => item.operatorId !== operatorId);

    const operator = DASHBOARD_STATE.operators.get(operatorId);
    if (operator) {
        operator.alertState = "idle";
        operator.connectionState = "online";
        updateOperatorMarker(operator);
    }
}

function openContextMenu(operatorId, team, lngLat) {
    const menu = document.getElementById("context-menu");
    const wrapper = document.getElementById("map-wrapper");
    if (!menu || !wrapper || !DASHBOARD_STATE.map || !lngLat) return;

    const point = DASHBOARD_STATE.map.project(lngLat);
    DASHBOARD_STATE.selectedOperatorId = operatorId;

    menu.hidden = false;
    menu.style.left = `${Math.min(point.x + 12, Math.max(wrapper.clientWidth - 270, 12))}px`;
    menu.style.top = `${Math.min(point.y + 12, Math.max(wrapper.clientHeight - 180, 12))}px`;
    menu.innerHTML = `
        <h3 class="context-menu__title">${escapeHtml(operatorId)}</h3>
        <p class="context-menu__meta">Team ${escapeHtml(team || "unknown")} · ${escapeHtml(getUiStatus(DASHBOARD_STATE.operators.get(operatorId) || {}).replace(/_/g, " "))}</p>
        <div class="context-menu__actions">
            <button class="context-menu__button" data-action="history">Request historical data</button>
        </div>
    `;

    menu.querySelectorAll("button[data-action]").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.dataset.action === "history") requestHistory(operatorId, team);
            closeContextMenu();
        });
    });
}

function closeContextMenu() {
    const menu = document.getElementById("context-menu");
    if (menu) { menu.hidden = true; menu.innerHTML = ""; }
    DASHBOARD_STATE.selectedOperatorId = null;
}

function requestHistory(operatorId, team) {
    if (!DASHBOARD_STATE.socket) return;
    DASHBOARD_STATE.socket.emit("request_history", { operator_id: operatorId, team }, (res) => {
        const op = DASHBOARD_STATE.operators.get(operatorId);
        if (res && res.ok && op) {
            const vals = normalizeHistory(res.history);
            if (vals.length) {
                op.trend = vals.slice(-HISTORY_LIMIT);
                const last = vals[vals.length - 1];
                if (Number.isFinite(last)) op.heartRate = last;
            }
        }
        renderDashboard();
    });
}

function normalizeHistory(history) {
    if (!Array.isArray(history)) return [];
    return history.map((e) => {
        if (typeof e === "number") return e;
        if (e && typeof e === "object") {
            const v = e.heart_rate ?? e.heartRate ?? e.hr ?? e.value;
            return Number.isFinite(Number(v)) ? Number(v) : null;
        }
        return null;
    }).filter(Number.isFinite);
}

function updateCounters() {
    const opCount = document.getElementById("operator-count");
    const alCount = document.getElementById("alert-count");
    if (opCount) opCount.textContent = String(DASHBOARD_STATE.operators.size);
    if (alCount) alCount.textContent = String(DASHBOARD_STATE.alerts.length);
}

function flashWorkspace() {
    const ws = document.querySelector(".workspace");
    if (ws && typeof ws.animate === "function") {
        ws.animate([{ filter: "brightness(1) saturate(1)" }, { filter: "brightness(1.08) saturate(1.15)" }, { filter: "brightness(1) saturate(1)" }], { duration: 420, easing: "ease-out" });
    }
}

function playBeep() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.type = "sine"; osc.frequency.value = 760;
        gain.gain.setValueAtTime(0.25, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.45);
        osc.start(); osc.stop(ctx.currentTime + 0.45);
    } catch (e) { console.debug("Audio unavailable"); }
}

function getAlertTitle(type) {
    switch (type) {
        case "MAN_DOWN": return "Man down";
        case "SIGNAL_LOST": return "Signal lost";
        case "RECONNECTED": return "Reconnected";
        case "OK": return "Operation resumed";
        default: return type.replace(/_/g, " ");
    }
}

function buildId(prefix) { return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`; }
function escapeHtml(val) { return String(val).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;"); }

console.log("Reverberus mission control ready");