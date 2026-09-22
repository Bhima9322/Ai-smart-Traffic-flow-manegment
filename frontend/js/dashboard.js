(() => {
  const API_URL = window.TRAFFIC_API_URL || "/api/status";
  const $ = (id) => document.getElementById(id);
  const seconds = (value) => Number.isFinite(Number(value)) ? `${value} sec` : "—";
  const text = (id, value) => { $(id).textContent = value ?? "—"; };

  function renderSignal(road, signal) {
    const lower = road.toLowerCase();
    text(`${lower}-state`, signal.state);
    text(`${lower}-count`, signal.vehicle_count);
    text(`${lower}-density`, signal.density);
    text(`${lower}-green`, seconds(signal.green_time));
    text(`${lower}-remaining`, seconds(signal.remaining_time));
    text(`${lower}-waiting`, seconds(signal.waiting_time));
    text(`${lower}-clearance`, seconds(signal.actual_clearance_time));
    text(road === "A" ? "a-unused" : "b-transferred", seconds(road === "A" ? signal.unused_green_time : signal.transferred_time));
  }

  function drawChart(canvasId, series, labels) {
    const canvas = $(canvasId); const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.clientWidth * devicePixelRatio;
    const height = canvas.height = canvas.clientHeight * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio); const w = canvas.clientWidth, h = canvas.clientHeight;
    ctx.clearRect(0, 0, w, h); ctx.strokeStyle = "#203945"; ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) { const y = (h / 4) * i; ctx.beginPath(); ctx.moveTo(34, y); ctx.lineTo(w - 8, y); ctx.stroke(); }
    const values = series.flatMap((s) => s.values); if (!values.length) return;
    const max = Math.max(1, ...values); const points = Math.max(1, labels.length - 1);
    series.forEach((line) => { ctx.strokeStyle = line.color; ctx.lineWidth = 2.5; ctx.beginPath(); line.values.forEach((value, index) => { const x = 34 + index * ((w - 44) / points); const y = h - 22 - (value / max) * (h - 38); index ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.stroke(); });
  }

  function renderEvents(events = []) {
    const log = $("event-log"); log.replaceChildren(); text("event-count", `${events.length} events`);
    if (!events.length) { log.innerHTML = '<li class="empty-event">No events returned by backend.</li>'; return; }
    events.slice(0, 20).forEach((event) => { const item = document.createElement("li"); item.textContent = event.message || event.type || "System event"; const time = document.createElement("time"); time.textContent = event.timestamp || "Timestamp unavailable"; item.append(time); log.append(item); });
  }

  function render(data) {
    const system = data.system || {}; const signals = data.signals || {}; const transfer = data.transfer || {};
    text("system-status", system.online ? "System online" : "System offline"); $("connection-dot").className = `status-dot ${system.online ? "online" : "offline"}`; text("mode", system.mode);
    renderSignal("A", signals.A || {}); renderSignal("B", signals.B || {});
    text("transfer-from", transfer.from); text("transfer-to", transfer.to);
    text("transfer-seconds", Number.isFinite(Number(transfer.seconds)) ? `${transfer.seconds} sec` : "No transfer recorded"); text("transfer-reason", transfer.reason);
    const emergency = data.emergency || {}; const incident = data.incident || {};
    text("emergency-status", emergency.active ? `ACTIVE${emergency.direction ? ` · ${emergency.direction}` : ""}` : "Clear"); text("incident-status", incident.active ? "ACTIVE" : "Clear");
    $("emergency-indicator").className = `indicator ${emergency.active ? "alert" : "active"}`; $("incident-indicator").className = `indicator ${incident.active ? "alert" : "active"}`;
    const camera = system.camera || {}; text("camera-mode", camera.mode || "No camera mode"); if (camera.stream_url) { $("camera-feed").src = camera.stream_url; $("camera-feed").hidden = false; $("camera-empty").hidden = true; }
    const history = data.history || {}; const traffic = history.traffic || []; const timing = history.timing || [];
    drawChart("traffic-chart", [{ values: traffic.map((x) => x.a), color: "#50e3a4" }, { values: traffic.map((x) => x.b), color: "#5ca8ff" }], traffic.map((x) => x.timestamp));
    drawChart("timing-chart", [{ values: timing.map((x) => x.a_green), color: "#50e3a4" }, { values: timing.map((x) => x.b_green), color: "#5ca8ff" }], timing.map((x) => x.timestamp)); renderEvents(data.events);
  }

  async function refresh() {
    try { const response = await fetch(API_URL, { headers: { Accept: "application/json" } }); if (!response.ok) throw new Error(`HTTP ${response.status}`); render(await response.json()); }
    catch { text("system-status", "Backend unavailable"); $("connection-dot").className = "status-dot offline"; }
  }
  window.addEventListener("resize", refresh); refresh(); setInterval(refresh, 5000);
})();
