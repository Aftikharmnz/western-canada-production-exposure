// ============================================================
// DATA PATHS
// ============================================================

const DATA_PATHS = {
  manifest: "public/data/manifest.json",
  assets: "public/data/assets.json",
  production: "public/data/monthly_production.json",
  schemeApprovals: "public/data/aer_scheme_approvals.geojson",
  st102Facilities: "public/data/aer_st102_oil_sands_facilities.geojson",
};

// ============================================================
// PRODUCTION SYSTEM METADATA  (map marker colour + label)
// ============================================================

const SYSTEM_META = {
  in_situ:           { label: "In-situ Bitumen",        color: "#008b8b", className: "in-situ" },
  mined:             { label: "Mined Bitumen",           color: "#d29b18", className: "mined" },
  conventional:      { label: "Conventional Crude",      color: "#4f8f45", className: "conventional" },
  heavy_conventional:{ label: "Heavy Crude (Conv.)",     color: "#c2720a", className: "heavy-conv" },
  synthetic:         { label: "Synthetic Crude Oil",     color: "#2980b9", className: "synthetic" },
  condensate:        { label: "Condensate",              color: "#6374a6", className: "condensate" },
  provincial_light:  { label: "Light Crude (Prov.)",     color: "#7bb53a", className: "conventional" },
  refinery_input:    { label: "Refinery Input",          color: "#9a5546", className: "refinery" },
};

// ============================================================
// STREAM → COLOUR MAP  (for breakdown bars & sparklines)
// ============================================================

const STREAM_COLORS = {
  "In-situ bitumen":             "#008b8b",
  "Mined bitumen gross":         "#d29b18",
  "Synthetic crude oil":         "#2980b9",
  "Conventional crude oil":      "#4f8f45",
  "Dilbit equivalent":           "#005f5f",
  "Ultra-Heavy":                 "#8b1a1a",
  "Ultra-H Dilbit":              "#c0392b",
  "Heavy Dilbit":                "#c74c0a",
  "Heavy crude oil":             "#c2720a",
  "Light & medium crude oil":    "#27ae60",
  "Light crude production":      "#7bb53a",
  "Other lights Excluding AB":   "#9dc63b",
  "Synthetic crude oil":         "#2980b9",
  "Condensate Production":       "#7d5fa5",
  "Total Condensate Supply":     "#9b59b6",
  "Condensate Imports":          "#b39ddb",
  "Condensate production":       "#7d5fa5",
  "Total WC crude":              "#7f8c8d",
  "Total Oil Sands Dilbit + SCO":"#2c3e50",
  "Blend Ratio":                 "#95a5a6",
  "Medium":                      "#e08c3a",
  "Heavy":                       "#c2720a",
  "Light":                       "#8bc34a",
};

// ============================================================
// SOURCE LABELS
// ============================================================

const SOURCE_SHORT = {
  aer_st53:             "AER ST53",
  aer_st39:             "AER ST39",
  petrinex_ab_conventional_vol: "Petrinex AB",
  petrinex_bc_facility_ids: "Petrinex BC ref",
  petrinex_bc_formation_codes: "Petrinex BC ref",
  petrinex_bc_activity_codes: "Petrinex BC ref",
};

// Streams shown by default on first load
const PRIMARY_STREAMS = [
  "In-situ bitumen",
  "Mined bitumen gross",
  "Synthetic crude oil",
  "Conventional crude oil",
];

// ============================================================
// APPLICATION STATE
// ============================================================

const state = {
  manifest: null,
  assets: [],
  assetById: new Map(),
  records: [],
  baseRecords: [],
  dateRecordCache: new Map(),
  dateRecordLoading: new Set(),
  dateRecordErrors: new Map(),
  geojson: null,
  schemeApprovals: null,
  st102Facilities: null,
  dates: [],
  selectedDate: null,
  selectedAssetId: null,
  selectedSources: new Set(),
  selectedStreams: new Set(),
  company: "All",
  search: "",
  map: null,
  markerLayer: null,
  fallbackReady: false,
  // Wildfire state — CWFIS hotspots (NRCan)
  wildfires: null,
  wildfireEnabled: false,
  wildfireLoading: false,
  wildfireError: null,
  fireLayer: null,
  riskBufferLayer: null,
  // Wildfire state — Alberta provincial active fires (ArcGIS)
  albertaFires: null,
  albertaFireLoading: false,
  albertaFireError: null,
  albertaFireLayer: null,
  // Wildfire state — BC Wildfire Service active fires (ArcGIS)
  bcFires: null,
  bcFireLoading: false,
  bcFireError: null,
  bcFireLayer: null,
  // Formation overlay state
  formationEnabled: false,
  formationLayer: null,
  // Seasonality index (lazy-loaded from asset_seasonality.json)
  seasonalityIndex: null,
  seasonalityIndexLoading: false,
  // Multi-asset rubber-band selection
  selectedAssets: [],
  rubberBandActive: false,
  facilityLayer: null,
};

// ============================================================
// DOM REFERENCES
// ============================================================

const els = {
  freshness:        document.querySelector("#freshness"),
  dateSlider:       document.querySelector("#dateSlider"),
  selectedDate:     document.querySelector("#selectedDate"),
  dateScenario:     document.querySelector("#dateScenario"),
  sourceFilters:    document.querySelector("#sourceFilters"),
  streamFilters:    document.querySelector("#streamFilters"),
  searchInput:      document.querySelector("#searchInput"),
  totalShown:       document.querySelector("#totalShown"),
  mappedCount:      document.querySelector("#mappedCount"),
  largestPoint:     document.querySelector("#largestPoint"),
  fireExposureRow:  document.querySelector("#fireExposureRow"),
  fireExposure:     document.querySelector("#fireExposure"),
  detailTitle:      document.querySelector("#detailTitle"),
  detailSubtitle:   document.querySelector("#detailSubtitle"),
  detailVolume:     document.querySelector("#detailVolume"),
  detailSource:     document.querySelector("#detailSource"),
  detailStatus:     document.querySelector("#detailStatus"),
  topAssetsList:    document.querySelector("#topAssetsList"),
  topAssetsLabel:   document.querySelector("#topAssetsLabel"),
  sourceBreakdown:  document.querySelector("#sourceBreakdown"),
  streamBreakdown:  document.querySelector("#streamBreakdown"),
  fireRiskSection:  document.querySelector("#fireRiskSection"),
  fireRiskBadge:    document.querySelector("#fireRiskBadge"),
  fireDistDisplay:  document.querySelector("#fireDistDisplay"),
  fireVolAtRisk:    document.querySelector("#fireVolAtRisk"),
  timelineBars:     document.querySelector("#timelineBars"),
  timelineLabel:    document.querySelector("#timelineLabel"),
  etlButton:        document.querySelector("#etlButton"),
  etlPanel:         document.querySelector("#etlPanel"),
  closeEtl:         document.querySelector("#closeEtl"),
  etlCommand:       document.querySelector("#etlCommand"),
  wildfireToggle:   document.querySelector("#wildfireToggle"),
  wildfireStatus:   document.querySelector("#wildfireStatus"),
  formationToggle:  document.querySelector("#formationToggle"),
  map:              document.querySelector("#map"),
  mapFallback:      document.querySelector("#mapFallback"),
};

// ============================================================
// FORMAT HELPERS
// ============================================================

function formatNumber(value, digits = 0) {
  if (!Number.isFinite(value)) return "--";
  return new Intl.NumberFormat("en-CA", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function kbbl(value) {
  if (!Number.isFinite(value)) return "--";
  const abs = Math.abs(value);
  if (abs > 0 && abs < 1) {
    const bbl = value * 1000;
    if (Math.abs(bbl) < 0.1) return "<0.1 bbl/d";
    return `${formatNumber(bbl, Math.abs(bbl) < 10 ? 1 : 0)} bbl/d`;
  }
  return `${formatNumber(value, abs >= 10 ? 0 : 1)} kbbl/d`;
}

function dateLabel(value) {
  if (!value) return "--";
  const date = new Date(`${value}T00:00:00`);
  return date.toLocaleDateString("en-CA", { year: "numeric", month: "short", day: "2-digit" });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));
}

function systemMeta(system) {
  return SYSTEM_META[system] || { label: system || "Unknown", color: "#60717a", className: "conventional" };
}

function streamColor(stream) {
  return STREAM_COLORS[stream] || "#60717a";
}

// ============================================================
// DATA LOADING
// ============================================================

async function loadData() {
  const [manifest, assets, records, schemeApprovals, st102Facilities] = await Promise.all(
    Object.values(DATA_PATHS).map((path) =>
      fetch(path).then((r) => {
        if (!r.ok) throw new Error(`Could not load ${path}`);
        return r.json();
      })
    )
  );
  state.manifest = manifest;
  state.assets = assets;
  state.assetById = new Map(assets.map((a) => [a.asset_id, a]));
  state.baseRecords = records;
  state.records = records;
  state.geojson = null;
  state.schemeApprovals = schemeApprovals;
  state.st102Facilities = st102Facilities;
  state.dates = manifest.periods || [...new Set(records.map((r) => r.date))].sort();
  state.selectedDate = manifest.latest_actual_date || state.dates.at(-1);
  if (!state.dates.includes(state.selectedDate)) state.selectedDate = state.dates.at(-1);
  await ensureDateRecords(state.selectedDate);
  state.records = recordsForDate(state.selectedDate);

  const sourceIds = [...new Set(records.map((r) => r.source_id))].sort();
  recordsForDate(state.selectedDate).forEach((r) => sourceIds.push(r.source_id));
  [...new Set(sourceIds)].sort().forEach((s) => state.selectedSources.add(s));

  const initialRecords = recordsForDate(state.selectedDate);
  PRIMARY_STREAMS.slice(0, 5).forEach((stream) => {
    if (initialRecords.some((r) => r.stream === stream)) state.selectedStreams.add(stream);
  });
  if (!state.selectedStreams.size) {
    [...new Set(initialRecords.map((r) => r.stream))].slice(0, 6).forEach((s) => state.selectedStreams.add(s));
  }
}

function recordsForDate(date = state.selectedDate) {
  return [
    ...state.baseRecords.filter((record) => record.date === date),
    ...(state.dateRecordCache.get(date) || []),
  ];
}

// Handles both file formats:
//   Legacy : array of full record objects [{date, asset_id, source_id, stream, volume_kbbl_d, scenario}, ...]
//   Compact: {date, source_id, stream, scenario, rows: [[asset_id, volume_kbbl_d], ...]}
//            OR an array of such compact group objects (rare multi-source files)
function expandMonthlyRecords(raw) {
  if (Array.isArray(raw)) {
    // Could be legacy full objects or array of compact groups
    if (!raw.length) return [];
    if ("rows" in raw[0]) {
      // Array of compact group objects
      return raw.flatMap(group =>
        (group.rows || []).map(([asset_id, volume_kbbl_d]) => ({
          date:           group.date,
          asset_id,
          source_id:      group.source_id,
          stream:         group.stream,
          volume_kbbl_d,
          scenario:       group.scenario ?? "actual",
        }))
      );
    }
    // Legacy array of full record objects — return as-is
    return raw;
  }
  // Single compact group object
  if (raw && "rows" in raw) {
    return (raw.rows || []).map(([asset_id, volume_kbbl_d]) => ({
      date:           raw.date,
      asset_id,
      source_id:      raw.source_id,
      stream:         raw.stream,
      volume_kbbl_d,
      scenario:       raw.scenario ?? "actual",
    }));
  }
  return [];
}

async function ensureDateRecords(date) {
  const file = state.manifest?.monthly_record_files?.[date];
  if (!file || state.dateRecordCache.has(date) || state.dateRecordLoading.has(date)) return;
  state.dateRecordLoading.add(date);
  state.dateRecordErrors.delete(date);
  try {
    // Keep the path relative so it resolves correctly both locally and on
    // GitHub Pages (where the app lives under a /repo-name/ subdirectory).
    const path = file.startsWith("/") ? file.slice(1) : file;
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Could not load ${path}`);
    const raw = await response.json();
    state.dateRecordCache.set(date, expandMonthlyRecords(raw));
  } catch (error) {
    state.dateRecordCache.set(date, []);
    state.dateRecordErrors.set(date, error.message || String(error));
  } finally {
    state.dateRecordLoading.delete(date);
  }
}

function requestDateRecords(date) {
  if (!state.manifest?.monthly_record_files?.[date]) return;
  if (state.dateRecordCache.has(date) || state.dateRecordLoading.has(date)) return;
  ensureDateRecords(date).then(() => {
    if (state.selectedDate === date) {
      state.records = recordsForDate(date);
      render();
    }
  });
}

// ============================================================
// CONTROLS INIT
// ============================================================

function initControls() {
  els.freshness.textContent = `ETL: ${new Date(state.manifest.generated_at).toLocaleString("en-CA")} · latest actual: ${dateLabel(state.manifest.latest_actual_date)} · ${formatNumber(state.manifest.record_count)} records`;

  els.dateSlider.max = String(Math.max(0, state.dates.length - 1));
  els.dateSlider.value = String(state.dates.indexOf(state.selectedDate));
  els.dateSlider.addEventListener("input", () => {
    state.selectedDate = state.dates[Number(els.dateSlider.value)];
    requestDateRecords(state.selectedDate);
    render();
  });

  const sourceIds = [...new Set(state.records.map((r) => r.source_id))].sort();
  els.sourceFilters.innerHTML = sourceIds
    .map((s) => toggleMarkup("source", s, SOURCE_SHORT[s] || s))
    .join("");
  els.sourceFilters.addEventListener("change", (e) => updateSetFromToggle(e, "source", state.selectedSources));

  const streamNames = [...new Set(state.records.map((r) => r.stream))].sort((a, b) => {
    const aRank = PRIMARY_STREAMS.includes(a) ? PRIMARY_STREAMS.indexOf(a) : 99;
    const bRank = PRIMARY_STREAMS.includes(b) ? PRIMARY_STREAMS.indexOf(b) : 99;
    return aRank === bRank ? a.localeCompare(b) : aRank - bRank;
  });
  els.streamFilters.innerHTML = streamNames
    .map((s) => toggleMarkupStream(s))
    .join("");
  els.streamFilters.addEventListener("change", (e) => updateSetFromToggle(e, "stream", state.selectedStreams));

  // company select removed

  els.searchInput.addEventListener("input", () => {
    state.search = els.searchInput.value.trim().toLowerCase();
    render();
  });

  els.etlCommand.textContent = "python scripts/run_etl.py --download";
  els.etlButton.addEventListener("click", () => { els.etlPanel.hidden = false; });
  els.closeEtl.addEventListener("click", () => { els.etlPanel.hidden = true; });

  if (els.wildfireToggle) {
    els.wildfireToggle.addEventListener("click", toggleWildfires);
  }
  if (els.formationToggle) {
    els.formationToggle.addEventListener("click", toggleFormations);
  }
}

function toggleMarkup(group, value, label) {
  const checked = group === "source" ? state.selectedSources.has(value) : state.selectedStreams.has(value);
  return `
    <label class="toggle-item" title="${escapeHtml(label)}">
      <input type="checkbox" data-group="${group}" value="${escapeHtml(value)}" ${checked ? "checked" : ""} />
      <span>${escapeHtml(label)}</span>
    </label>`;
}

function toggleMarkupStream(stream) {
  const checked = state.selectedStreams.has(stream);
  const color = streamColor(stream);
  return `
    <label class="toggle-item" title="${escapeHtml(stream)}">
      <input type="checkbox" data-group="stream" value="${escapeHtml(stream)}" ${checked ? "checked" : ""} />
      <span class="stream-swatch-label">
        <i class="stream-swatch" style="background:${color}"></i>
        ${escapeHtml(stream)}
      </span>
    </label>`;
}

function updateSetFromToggle(event, group, targetSet) {
  const input = event.target.closest(`input[data-group="${group}"]`);
  if (!input) return;
  if (input.checked) targetSet.add(input.value);
  else targetSet.delete(input.value);
  state.selectedAssetId = null;
  render();
}

// ============================================================
// MAP INIT
// ============================================================

function initMap() {
  if (!window.L) {
    els.map.hidden = true;
    els.mapFallback.hidden = false;
    state.fallbackReady = true;
    return;
  }
  state.map = L.map("map", {
    zoomControl: false,
    attributionControl: true,
    preferCanvas: true,
  }).setView([55.7, -112.0], 5);

  L.control.zoom({ position: "bottomright" }).addTo(state.map);
  L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    { maxZoom: 13, attribution: "Tiles: Esri World Topographic Map" }
  ).addTo(state.map);
  state.markerLayer = L.layerGroup().addTo(state.map);
  drawPipelines();
  initRubberBand();
}

function drawPipelines() {
  if (!state.map || !window.L) return;
  const lines = [
    { name: "Mainline corridor",     color: "#4a6f88", coords: [[57.1,-111.4],[53.9,-110.0],[52.1,-106.7],[50.4,-104.6]] },
    { name: "Keystone corridor",     color: "#7b6b58", coords: [[56.2,-111.2],[53.3,-110.0],[50.7,-108.3],[49.0,-104.8]] },
    { name: "Trans Mountain corridor",color: "#6a7f59", coords: [[53.5,-113.5],[52.9,-118.1],[50.7,-121.3],[49.3,-123.1]] },
  ];
  lines.forEach(({ name, color, coords }) => {
    L.polyline(coords, { color, weight: 2, opacity: 0.45, dashArray: "6 8" })
      .bindTooltip(name)
      .addTo(state.map);
  });
}

// ============================================================
// DATA FILTERING
// ============================================================

function filteredRecords(date = state.selectedDate) {
  return recordsForDate(date).filter((record) => {
    if (record.date !== date) return false;
    if (!state.selectedSources.has(record.source_id)) return false;
    if (!state.selectedStreams.has(record.stream)) return false;
    if (!Number.isFinite(record.volume_kbbl_d) || record.volume_kbbl_d <= 0) return false;
    const asset = state.assetById.get(record.asset_id);
    if (!asset) return false;
    // company filter removed — exposure panel now shows breakdown instead
    if (state.search) {
      const hay = `${asset.display_name} ${asset.company} ${asset.province} ${record.stream}`.toLowerCase();
      if (!hay.includes(state.search)) return false;
    }
    return true;
  });
}

function aggregateForDate(date = state.selectedDate) {
  const records = filteredRecords(date);
  const byAsset = new Map();
  const sourceTotals = new Map();
  for (const record of records) {
    const asset = state.assetById.get(record.asset_id);
    if (!asset) continue;
    // Map only location-specific assets/sites. Provincial/regional totals are deliberately excluded.
    if (asset.is_rollup || ["province", "province_refinery", "region"].includes(asset.asset_kind)) continue;
    if (!Number.isFinite(record.volume_kbbl_d) || record.volume_kbbl_d <= 0) continue;
    const existing = byAsset.get(record.asset_id) || {
      asset,
      kbbl: 0,
      streams: new Map(),
      sources: new Set(),
      scenarios: new Set(),
      records: [],
    };
    existing.kbbl += record.volume_kbbl_d;
    existing.streams.set(record.stream, (existing.streams.get(record.stream) || 0) + record.volume_kbbl_d);
    existing.sources.add(record.source_id);
    existing.scenarios.add(record.scenario);
    existing.records.push(record);
    byAsset.set(record.asset_id, existing);
    sourceTotals.set(record.source_id, (sourceTotals.get(record.source_id) || 0) + record.volume_kbbl_d);
  }
  return { byAsset, sourceTotals };
}

// ============================================================
// MAIN RENDER ORCHESTRATOR
// ============================================================

function render() {
  requestDateRecords(state.selectedDate);
  els.selectedDate.textContent = dateLabel(state.selectedDate);
  const actualCutoff = state.manifest.latest_actual_date;
  if (state.dateRecordLoading.has(state.selectedDate)) {
    els.dateScenario.textContent = "loading Petrinex";
  } else if (state.dateRecordErrors.has(state.selectedDate)) {
    els.dateScenario.textContent = "Petrinex unavailable";
  } else {
    els.dateScenario.textContent =
      actualCutoff && state.selectedDate > actualCutoff ? "forecast/model" : "actual/source";
  }
  renderMap();
  renderMetrics();
  renderDetails();
  renderTimeline();
}

// ============================================================
// MAP RENDER
// ============================================================

function renderMap() {
  const { byAsset } = aggregateForDate();
  const points = [...byAsset.values()].filter(
    ({ asset, kbbl: v }) => asset.latitude != null && asset.longitude != null && v > 0
  );

  if (state.map && state.markerLayer && window.L) {
    state.markerLayer.clearLayers();
    points.forEach((point) => {
      const meta = systemMeta(point.asset.production_system);
      const color = meta.color;
      const isSelected = point.asset.asset_id === state.selectedAssetId;
      const radius = Math.max(5, Math.min(34, Math.sqrt(point.kbbl) * 1.9));
      const topStream = [...point.streams.entries()].sort((a, b) => b[1] - a[1])[0];
      const markerColor = topStream ? streamColor(topStream[0]) : color;

      const marker = L.circleMarker(
        [point.asset.latitude, point.asset.longitude],
        {
          radius,
          fillColor: markerColor,
          fillOpacity: isSelected ? 0.9 : 0.65,
          color: isSelected ? "#101820" : "#ffffff",
          opacity: 1,
          weight: isSelected ? 3 : 1.4,
        }
      );
      const ttLines = [
        `<strong>${escapeHtml(point.asset.display_name)}</strong>`,
        escapeHtml(point.asset.company || point.asset.province),
        kbbl(point.kbbl),
        `<em>${escapeHtml(meta.label)}</em>`,
      ];
      if (topStream) ttLines.push(`Top stream: ${escapeHtml(topStream[0])}`);
      marker.bindTooltip(ttLines.join("<br>"), { direction: "top", opacity: 0.96 });
      marker.on("click", () => { state.selectedAssetId = point.asset.asset_id; render(); });
      marker.addTo(state.markerLayer);
    });

    renderFormationLayer();
    renderFireLayer();
  } else {
    renderFallbackMap(points);
  }
}

function renderFallbackMap(points) {
  els.mapFallback.hidden = false;
  const lonMin = -126, lonMax = -101, latMin = 48.5, latMax = 65.5;
  const width = 960, height = 620;
  const project = (lat, lon) => [
    ((lon - lonMin) / (lonMax - lonMin)) * width,
    height - ((lat - latMin) / (latMax - latMin)) * height,
  ];
  const circles = points.map(({ asset, kbbl: value }) => {
    const [x, y] = project(asset.latitude, asset.longitude);
    const color = streamColor(
      [...(aggregateForDate().byAsset.get(asset.asset_id)?.streams.entries() || [])].sort((a, b) => b[1] - a[1])[0]?.[0]
      || ""
    );
    const r = Math.max(5, Math.min(34, Math.sqrt(value) * 1.9));
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}" fill-opacity="0.64" stroke="#fff" stroke-width="1.3">
      <title>${escapeHtml(asset.display_name)} ${kbbl(value)}</title>
    </circle>`;
  }).join("");
  els.mapFallback.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="fallback-svg" aria-label="Offline production map">
      <rect width="${width}" height="${height}" fill="#e9eee8"></rect>
      <path d="M80,80 C220,60 320,140 430,110 C560,70 670,130 850,90 L910,560 L70,560 Z" fill="#d6e2d2"></path>
      ${circles}
    </svg>`;
}

// ============================================================
// METRICS PANEL
// ============================================================

function renderMetrics() {
  const { byAsset, sourceTotals } = aggregateForDate();
  const points = [...byAsset.values()].filter(
    ({ asset, kbbl: v }) => !asset.is_rollup && asset.latitude != null && v > 0
  );
  const total = points.reduce((s, p) => s + p.kbbl, 0);
  const largest = points.reduce((best, p) => (!best || p.kbbl > best.kbbl ? p : best), null);
  els.totalShown.textContent = kbbl(total);
  els.mappedCount.textContent = formatNumber(points.length);
  els.largestPoint.textContent = largest ? kbbl(largest.kbbl) : "--";

  // Source breakdown (sidebar)
  const totalBySource = [...sourceTotals.entries()].sort((a, b) => b[1] - a[1]);
  els.sourceBreakdown.innerHTML = totalBySource.slice(0, 6).map(([src, val]) => {
    const pct = total > 0 ? Math.min(100, (val / total) * 100) : 0;
    return `<div class="breakdown-row">
      <span>${escapeHtml(SOURCE_SHORT[src] || src)}</span>
      <strong>${kbbl(val)}</strong>
      <i style="width:${pct}%"></i>
    </div>`;
  }).join("") || `<p class="empty">No records match the active filters.</p>`;

  // Province breakdown
  const provEl = document.getElementById("provinceBreakdown");
  if (provEl) {
    const byProv = {};
    for (const { asset, kbbl: v } of byAsset.values()) {
      if (!asset.is_rollup && asset.latitude != null && v > 0)
        byProv[asset.province] = (byProv[asset.province] || 0) + v;
    }
    const provEntries = Object.entries(byProv).sort((a,b) => b[1]-a[1]);
    const provMax = Math.max(...provEntries.map(e=>e[1]), 1);
    provEl.innerHTML = provEntries.length
      ? `<p class="exp-label">By Province</p>` + provEntries.map(([prov, val]) =>
          `<div class="exp-bar-row"><span class="exp-bar-name">${escapeHtml(prov)}</span>` +
          `<div class="exp-bar-track"><div class="exp-bar-fill prov" style="width:${(val/provMax*100).toFixed(1)}%"></div></div>` +
          `<span class="exp-bar-val">${kbbl(val)}</span></div>`).join("")
      : "";
  }

  // System breakdown
  const sysEl = document.getElementById("systemBreakdown");
  if (sysEl) {
    const bySys = {};
    for (const { asset, kbbl: v } of byAsset.values()) {
      if (!asset.is_rollup && asset.latitude != null && v > 0) {
        const label = systemMeta(asset.production_system).label;
        bySys[label] = (bySys[label] || 0) + v;
      }
    }
    const sysEntries = Object.entries(bySys).sort((a,b) => b[1]-a[1]);
    const sysMax = Math.max(...sysEntries.map(e=>e[1]), 1);
    sysEl.innerHTML = sysEntries.length
      ? `<p class="exp-label">By System</p>` + sysEntries.map(([sys, val]) =>
          `<div class="exp-bar-row"><span class="exp-bar-name">${escapeHtml(sys)}</span>` +
          `<div class="exp-bar-track"><div class="exp-bar-fill sys" style="width:${(val/sysMax*100).toFixed(1)}%"></div></div>` +
          `<span class="exp-bar-val">${kbbl(val)}</span></div>`).join("")
      : "";
  }

  // Fire exposure
  if (els.fireExposureRow) {
    if (state.wildfireEnabled && state.wildfires) {
      let atRiskKbbl = 0;
      for (const { asset, kbbl: v } of byAsset.values()) {
        if (asset.latitude == null) continue;
        if (getFireRisk(asset.latitude, asset.longitude).level !== "none") atRiskKbbl += v;
      }
      els.fireExposureRow.hidden = false;
      els.fireExposure.textContent = kbbl(atRiskKbbl);
    } else {
      els.fireExposureRow.hidden = true;
    }
  }
}

// ============================================================
// DETAIL PANEL
// ============================================================

function renderDetails() {
  const { byAsset } = aggregateForDate();
  let selected = state.selectedAssetId ? byAsset.get(state.selectedAssetId) : null;
  if (!selected) selected = [...byAsset.values()].sort((a, b) => b.kbbl - a.kbbl)[0] || null;

  if (!selected) {
    els.detailTitle.textContent = "No matching production";
    els.detailSubtitle.textContent = "Adjust filters or date.";
    els.detailVolume.textContent = "--";
    els.detailSource.textContent = "--";
    els.detailStatus.textContent = "--";
    renderTopAssets();
    if (els.streamBreakdown) els.streamBreakdown.innerHTML = "";
    if (els.fireRiskSection) els.fireRiskSection.hidden = true;
    return;
  }

  const asset = selected.asset;
  els.detailTitle.textContent = asset.display_name;
  els.detailSubtitle.textContent = [
    asset.company,
    asset.province,
    systemMeta(asset.production_system).label,
  ].filter(Boolean).join(" · ");
  els.detailVolume.textContent = kbbl(selected.kbbl);
  els.detailSource.textContent = [...selected.sources].map((s) => SOURCE_SHORT[s] || s).join(", ");
  els.detailStatus.textContent = [...selected.scenarios].join(", ");

  renderTopAssets();
  renderStreamBreakdown(asset.asset_id, selected.streams);
  renderFireRisk(asset);
}

// ============================================================
// TOP ASSETS TABLE  (replaces sparkline)
// ============================================================

function renderTopAssets() {
  const el = document.getElementById("topAssetsList");
  const labelEl = document.getElementById("topAssetsLabel");
  if (!el) return;

  const { byAsset } = aggregateForDate();
  // Rank all mapped assets by volume descending
  const ranked = [...byAsset.values()]
    .filter(({ asset, kbbl: v }) => asset.latitude != null && v > 0)
    .sort((a, b) => b.kbbl - a.kbbl)
    .slice(0, 10);

  if (labelEl) labelEl.textContent = `Top ${ranked.length} of ${byAsset.size} assets`;

  if (!ranked.length) {
    el.innerHTML = `<p class="empty">No mapped assets at this date.</p>`;
    return;
  }

  el.innerHTML = ranked.map(({ asset, kbbl: vol, streams }, i) => {
    const meta = systemMeta(asset.production_system);
    const topStream = [...streams.entries()].sort((a, b) => b[1] - a[1])[0];
    const color = topStream ? streamColor(topStream[0]) : meta.color;
    const isSelected = asset.asset_id === state.selectedAssetId;

    const riskBadge = "";

    return `<div class="top-asset-row${isSelected ? " selected" : ""}" data-id="${escapeHtml(String(asset.asset_id))}">
      <span class="top-rank">${i + 1}</span>
      <i class="top-swatch" style="background:${color}"></i>
      <span class="top-name">${escapeHtml(asset.display_name)}</span>
      ${riskBadge}
      <strong class="top-vol">${kbbl(vol)}</strong>
    </div>`;
  }).join("");

  // Click to select asset
  el.querySelectorAll(".top-asset-row").forEach(row => {
    row.addEventListener("click", () => {
      state.selectedAssetId = row.dataset.id;
      render();
    });
  });
}

// ============================================================
// STREAM BREAKDOWN CHART  (coloured progress bars per stream)
// ============================================================

function renderStreamBreakdown(assetId, streamMap) {
  if (!els.streamBreakdown) return;
  const total = [...streamMap.values()].reduce((s, v) => s + v, 0);
  const sorted = [...streamMap.entries()].sort((a, b) => b[1] - a[1]);
  if (!sorted.length) {
    els.streamBreakdown.innerHTML = `<p class="empty">No stream detail at this date.</p>`;
    return;
  }
  els.streamBreakdown.innerHTML = sorted.map(([stream, vol]) => {
    const pct = total > 0 ? Math.min(100, (vol / total) * 100) : 0;
    const color = streamColor(stream);
    return `<div class="breakdown-row">
      <span><i class="stream-swatch" style="background:${color}"></i>${escapeHtml(stream)}</span>
      <strong>${kbbl(vol)}</strong>
      <i style="width:${pct}%;background:${color}"></i>
    </div>`;
  }).join("");
}

// ============================================================
// FIRE RISK DETAIL (inside detail panel)
// ============================================================

function renderFireRisk(asset) {
  if (!els.fireRiskSection) return;
  els.fireRiskSection.hidden = true;
  return;
  if (!state.wildfireEnabled || asset.latitude == null) {
    els.fireRiskSection.hidden = true;
    return;
  }
  els.fireRiskSection.hidden = false;

  if (state.wildfireLoading) {
    els.fireRiskBadge.textContent = "Loading…";
    els.fireRiskBadge.className = "risk-badge loading";
    els.fireDistDisplay.textContent = "--";
    els.fireVolAtRisk.textContent = "--";
    return;
  }

  if (!state.wildfires || state.wildfireError) {
    els.fireRiskBadge.textContent = "Data unavailable";
    els.fireRiskBadge.className = "risk-badge";
    els.fireDistDisplay.textContent = state.wildfireError || "--";
    els.fireVolAtRisk.textContent = "--";
    return;
  }

  const risk = getFireRisk(asset.latitude, asset.longitude);
  const labelMap = { high: "🔴 HIGH RISK", moderate: "🟠 MODERATE", none: "🟢 Clear" };
  const classMap = { high: "risk-badge high", moderate: "risk-badge moderate", none: "risk-badge clear" };

  els.fireRiskBadge.textContent = labelMap[risk.level];
  els.fireRiskBadge.className = classMap[risk.level];
  els.fireDistDisplay.textContent = risk.level !== "none"
    ? `${risk.distanceKm.toLocaleString()} km to nearest fire`
    : "No active fires within 200 km";

  // Estimate at-risk production from all streams for this asset at selected date
  const atRiskVol = recordsForDate(state.selectedDate)
    .filter((r) => r.asset_id === asset.asset_id && r.date === state.selectedDate && state.selectedStreams.has(r.stream))
    .reduce((s, r) => s + r.volume_kbbl_d, 0);
  els.fireVolAtRisk.textContent = risk.level !== "none"
    ? `${kbbl(atRiskVol)} potentially at risk`
    : "--";
}

// ============================================================
// TIMELINE
// ============================================================

function renderTimeline() {
  const rows = state.dates.map((date) => {
    let total;
    const hasOnDemandFile = Boolean(state.manifest?.monthly_record_files?.[date]);
    if (hasOnDemandFile && !state.dateRecordCache.has(date)) {
      total = state.manifest?.date_totals_kbbl_d?.[date];
    }
    if (!Number.isFinite(total)) {
      const { byAsset } = aggregateForDate(date);
      total = [...byAsset.values()].reduce((s, p) => s + p.kbbl, 0);
    }
    return { date, total };
  });
  const max = Math.max(...rows.map((r) => r.total), 1);
  const selectedIndex = rows.findIndex((r) => r.date === state.selectedDate);
  const windowStart = Math.max(0, selectedIndex - 30);
  const visible = rows.slice(windowStart, Math.min(rows.length, windowStart + 72));
  els.timelineLabel.textContent = `${visible.length} monthly observations in view`;
  els.timelineBars.innerHTML = visible.map((row) => {
    const height = Math.max(3, (row.total / max) * 72);
    const sel = row.date === state.selectedDate;
    return `<button class="timeline-bar ${sel ? "selected" : ""}" style="height:${height}px" title="${dateLabel(row.date)} ${kbbl(row.total)}" data-date="${row.date}" aria-label="${dateLabel(row.date)} ${kbbl(row.total)}"></button>`;
  }).join("");
  els.timelineBars.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedDate = btn.dataset.date;
      els.dateSlider.value = String(state.dates.indexOf(state.selectedDate));
      render();
    });
  });
}

// ============================================================
// ============================================================
// AER SCHEME FOOTPRINT OVERLAY
// Uses AER Scheme Approval Spatial Data converted from the cached GCS_NAD83
// shapefiles. This replaces the earlier broad hand-drawn basin polygons.
// ============================================================

// Style per kind
const FORMATION_KIND_STYLE = {
  in_situ_scheme:   { color: "#0f8b8d", fillColor: "#2dd4bf", fillOpacity: 0.16, weight: 1.1, opacity: 0.78, dashArray: "4 3" },
  mineable_scheme:  { color: "#b7791f", fillColor: "#f59e0b", fillOpacity: 0.20, weight: 1.3, opacity: 0.86, dashArray: null },
  oil_sands:        { color: "#b45309", fillColor: "#f59e0b", fillOpacity: 0.14, weight: 1.2, opacity: 0.4, dashArray: null },
  tight_play:       { color: "#3d6b00", fillColor: "#84cc16", fillOpacity: 0.13, weight: 1.2, opacity: 0.38, dashArray: "5 4" },
};

function renderFormationLayer() {
  if (!state.map || !window.L) return;
  // Only clear+redraw when toggled (not every render tick) — skip if
  // the layer already exists and enabled state hasn't changed.
  if (!state.formationEnabled) {
    if (state.formationLayer) {
      state.map.removeLayer(state.formationLayer);
      state.formationLayer = null;
    }
    if (state.facilityLayer) {
      state.map.removeLayer(state.facilityLayer);
      state.facilityLayer = null;
    }
    return;
  }

  const source = state.schemeApprovals;
  if (source?.features?.length && !state.formationLayer) {
    state.formationLayer = L.geoJSON(source, {
      style(feature) {
        return FORMATION_KIND_STYLE[feature.properties?.kind] || FORMATION_KIND_STYLE.in_situ_scheme;
      },
      onEachFeature(feature, layer) {
        const p = feature.properties || {};
        const name = p.name || p.scheme_no || "AER scheme approval";
        layer.bindTooltip(
          `<strong style="font-size:12px">${escapeHtml(name)}</strong><br>` +
            `${escapeHtml(p.layer || "AER scheme approval")}<br>` +
            `${p.holder ? escapeHtml(p.holder) + "<br>" : ""}` +
            `${p.scheme_no ? "Scheme " + escapeHtml(p.scheme_no) : ""}`,
          { sticky: true, opacity: 0.92, className: "formation-tip" }
        );
      },
    }).addTo(state.map);

    // Push project footprints behind production markers and fire hotspots.
    state.formationLayer.bringToBack();
  }

  const facilities = state.st102Facilities;
  if (facilities?.features?.length && !state.facilityLayer) {
    state.facilityLayer = L.geoJSON(facilities, {
      pointToLayer(_feature, latlng) {
        return L.circleMarker(latlng, {
          radius: 4,
          color: "#172326",
          weight: 1,
          fillColor: "#ffffff",
          fillOpacity: 0.88,
          opacity: 0.78,
        });
      },
      onEachFeature(feature, layer) {
        const p = feature.properties || {};
        layer.bindTooltip(
          `<strong style="font-size:12px">${escapeHtml(p.name || "ST102 facility")}</strong><br>` +
            `${escapeHtml(p.subtype || "Facility")}<br>` +
            `${p.operator ? escapeHtml(p.operator) + "<br>" : ""}` +
            `${p.facility_id ? escapeHtml(p.facility_id) + " · " : ""}${escapeHtml(p.status || "")}`,
          { sticky: true, opacity: 0.92, className: "formation-tip" }
        );
      },
    }).addTo(state.map);
  }
}

function toggleFormations() {
  state.formationEnabled = !state.formationEnabled;
  if (state.formationEnabled) {
    renderFormationLayer();
  } else if (state.formationLayer) {
    state.map.removeLayer(state.formationLayer);
    state.formationLayer = null;
  }
  if (!state.formationEnabled && state.facilityLayer) {
    state.map.removeLayer(state.facilityLayer);
    state.facilityLayer = null;
  }
  updateFormationToggleUI();
}

function updateFormationToggleUI() {
  const btn = els.formationToggle;
  if (!btn) return;
  if (state.formationEnabled) {
    btn.textContent = "AER Sites ON";
    btn.className = "formation-toggle-btn active";
  } else {
    btn.textContent = "AER Sites";
    btn.className = "formation-toggle-btn";
  }
}

// WILDFIRE  —  CWFIS live feed (WFS hotspots_24h, Western Canada bbox)
// ============================================================

// CWFIS GeoServer WFS — hotspots updated every 10 min; CQL filter keeps only
// points inside Western Canada (lat 49–72, lon –141 to –94).
// The WFS geometry is in a projected CRS; real coords are in properties.lat/lon.
const CWFIS_URL =
  "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wfs" +
  "?service=WFS&version=1.1.0&request=GetFeature" +
  "&typeName=public:hotspots_24h" +
  "&outputFormat=application%2Fjson" +
  "&CQL_FILTER=lat%3E49%20AND%20lat%3C72%20AND%20lon%3E-141%20AND%20lon%3C-94" +
  "&maxFeatures=2000";

// Alberta provincial active wildfire locations — ArcGIS public FeatureServer.
// Returns point features with Agency, Fire_Name, Latitude, Longitude,
// Hectares__Ha_, Stage_of_Control, and Start_Date.
// Filter: Agency = 'Alberta'  (catches AB fires; server also holds BC/other agencies)
// BC Wildfire Service — BCWS_ActiveFires_PublicView, all fires except status 'Out'.
// Status values: 'Out of Control', 'Being Held', 'Under Control', 'Fire of Note', 'New'.
// Geometry is proper WGS84 — no coordinate normalization needed.
const BC_FIRES_URL =
  "https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/BCWS_ActiveFires_PublicView/FeatureServer/0/query" +
  "?where=FIRE_STATUS%20%3C%3E%20%27Out%27" +
  "&outFields=FIRE_NUMBER%2CINCIDENT_NAME%2CFIRE_STATUS%2CCURRENT_SIZE%2CLATITUDE%2CLONGITUDE%2CIGNITION_DATE%2CGEOGRAPHIC_DESCRIPTION%2CFIRE_OF_NOTE_IND%2CRESPONSE_TYPE_DESC" +
  "&returnGeometry=true" +
  "&f=geojson";

// Full Alberta active fire inventory — wjcPoefzjpzCgffS 'activefires' layer.
// This is the comprehensive source used by the Alberta Wildfire Status Dashboard.
// Returns 20+ fires including all carryover fires; Agency uses uppercase 'AB'.
// Fire_Name format: "YYYY_AB_FireCode-YYYY" e.g. "2025_AB_SWF-085-2025"
const ALBERTA_FIRES_URL =
  "https://services.arcgis.com/wjcPoefzjpzCgffS/ArcGIS/rest/services/activefires/FeatureServer/0/query" +
  "?where=Agency%3D%27AB%27" +
  "&outFields=Agency%2CFire_Name%2CLatitude%2CLongitude%2CHectares__Ha_%2CStage_of_Control%2CStart_Date" +
  "&returnGeometry=true" +
  "&f=geojson";

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const d2r = Math.PI / 180;
  const dLat = (lat2 - lat1) * d2r;
  const dLon = (lon2 - lon1) * d2r;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * d2r) * Math.cos(lat2 * d2r) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function geojsonCentroid(feature) {
  const geom = feature.geometry;
  if (!geom) return null;
  if (geom.type === "Point") return { lat: geom.coordinates[1], lon: geom.coordinates[0] };
  let ring;
  if (geom.type === "Polygon") ring = geom.coordinates[0];
  else if (geom.type === "MultiPolygon") ring = geom.coordinates[0][0];
  else return null;
  const lon = ring.reduce((s, p) => s + p[0], 0) / ring.length;
  const lat = ring.reduce((s, p) => s + p[1], 0) / ring.length;
  return { lat, lon };
}

function getFireRisk(assetLat, assetLon) {
  let minDist = Infinity;
  let nearestFire = null;

  // Check CWFIS hotspots
  for (const feature of state.wildfires?.features || []) {
    const c = geojsonCentroid(feature);
    if (!c) continue;
    const dist = haversineKm(assetLat, assetLon, c.lat, c.lon);
    if (dist < minDist) { minDist = dist; nearestFire = feature; }
  }

  // Check Alberta provincial fires
  for (const feature of state.albertaFires?.features || []) {
    const c = geojsonCentroid(feature);
    if (!c) continue;
    const dist = haversineKm(assetLat, assetLon, c.lat, c.lon);
    if (dist < minDist) { minDist = dist; nearestFire = feature; }
  }

  // Check BC provincial fires
  for (const feature of state.bcFires?.features || []) {
    const c = geojsonCentroid(feature);
    if (!c) continue;
    const dist = haversineKm(assetLat, assetLon, c.lat, c.lon);
    if (dist < minDist) { minDist = dist; nearestFire = feature; }
  }

  if (!Number.isFinite(minDist) || minDist === Infinity) return { level: "none", distanceKm: Infinity, nearestFire: null };
  const level = minDist < 75 ? "high" : minDist < 200 ? "moderate" : "none";
  return { level, distanceKm: Math.round(minDist), nearestFire };
}

async function fetchWildfires() {
  if (state.wildfireLoading) return;
  state.wildfireLoading = true;
  state.wildfireError = null;
  updateFireToggleUI();
  updateWildfireStatus("Fetching active fire hotspots from NRCan CWFIS…");
  try {
    const response = await fetch(CWFIS_URL, { mode: "cors" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const raw = await response.json();

    // The WFS geometry is in a projected CRS (not WGS84).
    // Swap each feature's geometry to a proper WGS84 Point using
    // the lat/lon stored in feature.properties.
    const normalized = {
      type: "FeatureCollection",
      features: (raw.features || [])
        .filter(f => f.properties?.lat != null && f.properties?.lon != null)
        .map(f => ({
          ...f,
          geometry: {
            type: "Point",
            coordinates: [Number(f.properties.lon), Number(f.properties.lat)],
          },
        })),
    };

    if (normalized.features.length === 0) {
      state.wildfireError = "No active fire hotspots in Western Canada right now.";
    }
    state.wildfires = normalized;
  } catch (err) {
    state.wildfireError = `NRCan CWFIS unavailable (${err.message}).`;
    state.wildfires = null;
  } finally {
    state.wildfireLoading = false;
    updateFireToggleUI();
    updateWildfireStatus(buildFireStatusMsg());
    render();
  }
}

// ============================================================
// ALBERTA PROVINCIAL ACTIVE WILDFIRES  — ArcGIS FeatureServer
// Loaded automatically on boot and refreshed alongside CWFIS.
// Stage_of_Control short codes used by this layer:
//   "OC" = Out of Control, "BH" = Being Held, "UC" = Under Control
// ============================================================

const ALBERTA_STAGE_STYLE = {
  "OC": { color: "#7f1d1d", fill: "#ef4444", weight: 2.5, opacity: 0.95, label: "Out of Control" },
  "BH": { color: "#7c2d12", fill: "#f97316", weight: 2,   opacity: 0.90, label: "Being Held"     },
  "UC": { color: "#78350f", fill: "#fbbf24", weight: 2,   opacity: 0.85, label: "Under Control"  },
  default: { color: "#1e293b", fill: "#94a3b8", weight: 1.5, opacity: 0.75, label: "Unknown" },
};

// BC uses full English status strings; Fire of Note gets a distinct purple marker.
const BC_STATUS_STYLE = {
  "Out of Control": { color: "#7f1d1d", fill: "#dc2626", weight: 2.5, opacity: 0.95, label: "Out of Control" },
  "Being Held":     { color: "#9a3412", fill: "#ea580c", weight: 2,   opacity: 0.90, label: "Being Held"     },
  "Under Control":  { color: "#3f6212", fill: "#84cc16", weight: 2,   opacity: 0.85, label: "Under Control"  },
  "Fire of Note":   { color: "#6b21a8", fill: "#a855f7", weight: 2.5, opacity: 0.95, label: "Fire of Note"   },
  "New":            { color: "#9a3412", fill: "#fb923c", weight: 2,   opacity: 0.88, label: "New"             },
  default:          { color: "#1e293b", fill: "#94a3b8", weight: 1.5, opacity: 0.75, label: "Unknown"         },
};

async function fetchAlbertaFires() {
  if (state.albertaFireLoading) return;
  state.albertaFireLoading = true;
  state.albertaFireError = null;
  try {
    const response = await fetch(ALBERTA_FIRES_URL, { mode: "cors" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const raw = await response.json();

    // Normalize: prefer the explicit Latitude/Longitude props over geometry
    // (geometry may be in a projected CRS on some ArcGIS exports).
    const features = (raw.features || []).map(f => {
      const p = f.properties || {};
      const lat = Number(p.Latitude  ?? p.latitude);
      const lon = Number(p.Longitude ?? p.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
      return {
        ...f,
        geometry: { type: "Point", coordinates: [lon, lat] },
      };
    }).filter(Boolean);

    state.albertaFires = { type: "FeatureCollection", features };
  } catch (err) {
    state.albertaFireError = `Alberta fire data unavailable (${err.message}).`;
    state.albertaFires = null;
  } finally {
    state.albertaFireLoading = false;
    updateWildfireStatus(buildFireStatusMsg());
    render();
  }
}

function renderAlbertaFireLayer() {
  if (!state.map || !window.L) return;
  if (state.albertaFireLayer) {
    state.map.removeLayer(state.albertaFireLayer);
    state.albertaFireLayer = null;
  }
  if (!state.wildfireEnabled || !state.albertaFires?.features?.length) return;

  const currentYear = new Date().getFullYear();

  state.albertaFireLayer = L.geoJSON(state.albertaFires, {
    pointToLayer(feature, latlng) {
      const p = feature.properties || {};
      const stage = p.Stage_of_Control || "";
      const style = ALBERTA_STAGE_STYLE[stage] || ALBERTA_STAGE_STYLE.default;
      const ha = Number(p.Hectares__Ha_);
      const r = Number.isFinite(ha) && ha > 0
        ? Math.min(22, 8 + Math.log10(ha + 1) * 4)
        : 8;
      // Name format is "YYYY_AB_FireCode" — year prefix tells us if it's a carryover
      const nameYear = Number((p.Fire_Name || "").match(/^(\d{4})_/)?.[1]);
      const isCarryover = Number.isFinite(nameYear) && nameYear < currentYear;
      return L.circleMarker(latlng, {
        radius: r,
        color: style.color,
        weight: style.weight,
        fillColor: style.fill,
        fillOpacity: style.opacity,
        opacity: 1,
        dashArray: isCarryover ? "5 4" : null,
      });
    },
    onEachFeature(feature, layer) {
      const p = feature.properties || {};
      // Strip the "YYYY_AB_" prefix for display — show just the fire code e.g. "SWF-085-2025"
      const rawName = p.Fire_Name || "Unnamed Alberta fire";
      const displayName = rawName.replace(/^\d{4}_[A-Z]{2}_/, "");
      const ha = Number(p.Hectares__Ha_);
      const haStr = Number.isFinite(ha) && ha > 0 ? `${ha.toLocaleString("en-CA")} ha` : "size unknown";
      const startMs = Number(p.Start_Date);
      const startDate = Number.isFinite(startMs) && startMs > 0 ? new Date(startMs) : null;
      const startStr = startDate ? startDate.toLocaleDateString("en-CA") : "—";
      const startYear = startDate ? startDate.getFullYear() : null;
      const nameYear = Number(rawName.match(/^(\d{4})_/)?.[1]);
      const isCarryover = Number.isFinite(nameYear) && nameYear < currentYear;
      const stageCode = p.Stage_of_Control || "";
      const stageStyle = ALBERTA_STAGE_STYLE[stageCode] || ALBERTA_STAGE_STYLE.default;
      const carryoverNote = isCarryover
        ? `<span style="color:#b45309">⚠️ Carryover — burning since ${nameYear}</span><br>`
        : `<span style="color:#166534">🔥 New fire (${startYear ?? currentYear})</span><br>`;
      layer.bindTooltip(
        `<strong>${escapeHtml(displayName)}</strong><br>` +
        carryoverNote +
        `Status: ${escapeHtml(stageStyle.label)}<br>` +
        `Size: ${haStr}<br>` +
        `Started: ${startStr}<br>` +
        `<em>Alberta Wildfire (official)</em>`,
        { opacity: 0.96, className: "alberta-fire-tip" }
      );
    },
  }).addTo(state.map);

  // Alberta official fires sit above CWFIS hotspot dots
  state.albertaFireLayer.bringToFront();
}

// ============================================================
// BC WILDFIRE SERVICE — BCWS_ActiveFires_PublicView
// ============================================================

async function fetchBCFires() {
  if (state.bcFireLoading) return;
  state.bcFireLoading = true;
  state.bcFireError = null;
  try {
    const response = await fetch(BC_FIRES_URL, { mode: "cors" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const raw = await response.json();
    // Geometry is already valid WGS84 — use as-is, but fall back to
    // LATITUDE/LONGITUDE props if geometry is null for any feature.
    const features = (raw.features || []).map(f => {
      if (f.geometry) return f;
      const lat = Number(f.properties?.LATITUDE);
      const lon = Number(f.properties?.LONGITUDE);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
      return { ...f, geometry: { type: "Point", coordinates: [lon, lat] } };
    }).filter(Boolean);
    state.bcFires = { type: "FeatureCollection", features };
  } catch (err) {
    state.bcFireError = `BC fire data unavailable (${err.message}).`;
    state.bcFires = null;
  } finally {
    state.bcFireLoading = false;
    updateWildfireStatus(buildFireStatusMsg());
    render();
  }
}

function renderBCFireLayer() {
  if (!state.map || !window.L) return;
  if (state.bcFireLayer) { state.map.removeLayer(state.bcFireLayer); state.bcFireLayer = null; }
  if (!state.wildfireEnabled || !state.bcFires?.features?.length) return;

  const currentYear = new Date().getFullYear();

  state.bcFireLayer = L.geoJSON(state.bcFires, {
    pointToLayer(feature, latlng) {
      const p = feature.properties || {};
      const isFON = p.FIRE_OF_NOTE_IND === "Y";
      const status = isFON ? "Fire of Note" : (p.FIRE_STATUS || "");
      const style = BC_STATUS_STYLE[status] || BC_STATUS_STYLE.default;
      const ha = Number(p.CURRENT_SIZE);
      const r = Number.isFinite(ha) && ha > 0
        ? Math.min(20, 6 + Math.log10(ha + 1) * 4)
        : 6;
      // Carryover: ignition year before current year
      const ignMs = Number(p.IGNITION_DATE);
      const ignYear = Number.isFinite(ignMs) && ignMs > 0
        ? new Date(ignMs).getFullYear() : null;
      const isCarryover = ignYear != null && ignYear < currentYear;
      return L.circleMarker(latlng, {
        radius: r,
        color: style.color,
        weight: style.weight,
        fillColor: style.fill,
        fillOpacity: style.opacity,
        opacity: 1,
        dashArray: isCarryover ? "5 4" : null,
      });
    },
    onEachFeature(feature, layer) {
      const p = feature.properties || {};
      const isFON = p.FIRE_OF_NOTE_IND === "Y";
      const status = isFON ? "Fire of Note" : (p.FIRE_STATUS || "");
      const stageStyle = BC_STATUS_STYLE[status] || BC_STATUS_STYLE.default;
      const ha = Number(p.CURRENT_SIZE);
      const haStr = Number.isFinite(ha) && ha > 0 ? `${ha.toLocaleString("en-CA")} ha` : "size unknown";
      const ignMs = Number(p.IGNITION_DATE);
      const ignDate = Number.isFinite(ignMs) && ignMs > 0 ? new Date(ignMs) : null;
      const ignStr = ignDate ? ignDate.toLocaleDateString("en-CA") : "—";
      const ignYear = ignDate ? ignDate.getFullYear() : null;
      const currentYear = new Date().getFullYear();
      const isCarryover = ignYear != null && ignYear < currentYear;
      const name = p.INCIDENT_NAME && p.INCIDENT_NAME !== p.FIRE_NUMBER
        ? `${escapeHtml(p.FIRE_NUMBER)} — ${escapeHtml(p.INCIDENT_NAME)}`
        : escapeHtml(p.FIRE_NUMBER || "Unknown BC fire");
      const carryoverNote = isCarryover
        ? `<span style="color:#b45309">⚠️ Carryover — burning since ${ignYear}</span><br>`
        : `<span style="color:#166534">🔥 New fire (${ignYear ?? currentYear})</span><br>`;
      const fonBadge = isFON
        ? `<span style="color:#7e22ce;font-weight:700">★ Fire of Note</span><br>`
        : "";
      const desc = p.GEOGRAPHIC_DESCRIPTION ? `📍 ${escapeHtml(p.GEOGRAPHIC_DESCRIPTION)}<br>` : "";
      layer.bindTooltip(
        `<strong>${name}</strong><br>` +
        fonBadge +
        carryoverNote +
        `Status: ${escapeHtml(stageStyle.label)}<br>` +
        `Size: ${haStr}<br>` +
        desc +
        `Started: ${ignStr}<br>` +
        `<em>BC Wildfire Service (official)</em>`,
        { opacity: 0.96, className: "bc-fire-tip" }
      );
    },
  }).addTo(state.map);

  // BC fires sit above CWFIS dots but Alberta official fires stay on top
  if (state.albertaFireLayer) state.albertaFireLayer.bringToFront();
}

function buildFireStatusMsg() {
  const parts = [];
  if (state.wildfireLoading || state.albertaFireLoading || state.bcFireLoading) {
    parts.push("Fetching fire data…");
    return parts.join(" · ");
  }

  // CWFIS satellite hotspots
  const cwfisCount = state.wildfires?.features?.length ?? 0;
  if (state.wildfireError && !cwfisCount) {
    parts.push(`NRCan CWFIS: ${state.wildfireError}`);
  } else if (cwfisCount > 0) {
    const sev = summarizeFireSeverity(state.wildfires.features);
    parts.push(`${cwfisCount} NRCan hotspot${cwfisCount !== 1 ? "s" : ""}${sev ? ` (${sev})` : ""}`);
  }

  // Alberta official fires
  const abCount = state.albertaFires?.features?.length ?? 0;
  if (state.albertaFireError && !abCount) {
    parts.push(`AB: ${state.albertaFireError}`);
  } else if (abCount > 0) {
    const ooc = state.albertaFires.features.filter(f => f.properties?.Stage_of_Control === "OC").length;
    const bh  = state.albertaFires.features.filter(f => f.properties?.Stage_of_Control === "BH").length;
    const stageSummary = [ooc > 0 ? `${ooc} OC` : "", bh > 0 ? `${bh} BH` : ""].filter(Boolean).join(", ");
    parts.push(`${abCount} AB fire${abCount !== 1 ? "s" : ""}${stageSummary ? ` (${stageSummary})` : ""}`);
  }

  // BC official fires
  const bcCount = state.bcFires?.features?.length ?? 0;
  if (state.bcFireError && !bcCount) {
    parts.push(`BC: ${state.bcFireError}`);
  } else if (bcCount > 0) {
    const ooc = state.bcFires.features.filter(f => f.properties?.FIRE_STATUS === "Out of Control").length;
    const fon = state.bcFires.features.filter(f => f.properties?.FIRE_OF_NOTE_IND === "Y").length;
    const stageSummary = [ooc > 0 ? `${ooc} OC` : "", fon > 0 ? `${fon} FON` : ""].filter(Boolean).join(", ");
    parts.push(`${bcCount} BC fire${bcCount !== 1 ? "s" : ""}${stageSummary ? ` (${stageSummary})` : ""}`);
  }

  return parts.join(" · ");
}

function toggleWildfires() {
  state.wildfireEnabled = !state.wildfireEnabled;
  if (state.wildfireEnabled) {
    let needRender = false;
    if (!state.wildfires      && !state.wildfireLoading)     { fetchWildfires();    } else { needRender = true; }
    if (!state.albertaFires   && !state.albertaFireLoading)  { fetchAlbertaFires(); } else { needRender = true; }
    if (!state.bcFires        && !state.bcFireLoading)       { fetchBCFires();      } else { needRender = true; }
    if (needRender) render();
    return;
  }
  clearFireLayers();
  updateWildfireStatus("");
  updateFireToggleUI();
  render();
}

function clearFireLayers() {
  if (state.fireLayer        && state.map) { state.map.removeLayer(state.fireLayer);        state.fireLayer        = null; }
  if (state.albertaFireLayer && state.map) { state.map.removeLayer(state.albertaFireLayer); state.albertaFireLayer = null; }
  if (state.bcFireLayer      && state.map) { state.map.removeLayer(state.bcFireLayer);      state.bcFireLayer      = null; }
  if (state.riskBufferLayer  && state.map) { state.map.removeLayer(state.riskBufferLayer);  state.riskBufferLayer  = null; }
}

function updateFireToggleUI() {
  if (!els.wildfireToggle) return;
  if (state.wildfireLoading) {
    els.wildfireToggle.textContent = "Loading fires...";
    els.wildfireToggle.className = "fire-toggle-btn loading";
  } else if (state.wildfireEnabled) {
    els.wildfireToggle.textContent = "Fires ON";
    els.wildfireToggle.className = "fire-toggle-btn active";
  } else {
    els.wildfireToggle.textContent = "Fire Layer";
    els.wildfireToggle.className = "fire-toggle-btn";
  }
}

function updateWildfireStatus(msg) {
  if (!els.wildfireStatus) return;
  els.wildfireStatus.textContent = msg;
  els.wildfireStatus.hidden = !msg;
}

function fireScore(feature) {
  const fwi = Number(feature?.properties?.fwi);
  return Number.isFinite(fwi) ? fwi : null;
}

function fireSeverity(score) {
  if (!Number.isFinite(score)) return { label: "Unscored", className: "unknown" };
  if (score >= 30) return { label: "Extreme", className: "extreme" };
  if (score >= 15) return { label: "High", className: "high" };
  if (score >= 5) return { label: "Moderate", className: "moderate" };
  return { label: "Low", className: "low" };
}

function summarizeFireSeverity(features) {
  const counts = { Extreme: 0, High: 0, Moderate: 0, Low: 0, Unscored: 0 };
  for (const feature of features || []) {
    const severity = fireSeverity(fireScore(feature));
    counts[severity.label] = (counts[severity.label] || 0) + 1;
  }
  return ["Extreme", "High", "Moderate", "Low", "Unscored"]
    .filter((label) => counts[label] > 0)
    .map((label) => `${counts[label]} ${label.toLowerCase()}`)
    .join(", ");
}

function renderRiskBuffers(byAsset) {
  if (!state.map || !window.L) return;
  if (state.riskBufferLayer) { state.map.removeLayer(state.riskBufferLayer); state.riskBufferLayer = null; }
  if (!state.wildfireEnabled || !state.wildfires?.features?.length) return;

  const group = L.layerGroup();
  for (const { asset, kbbl } of byAsset.values()) {
    if (asset.latitude == null || asset.longitude == null) continue;
    const risk = getFireRisk(asset.latitude, asset.longitude);
    if (risk.level === "none") continue;
    const isHigh = risk.level === "high";
    // Pixel-space halo: circleMarker radius in px, no fill
    const baseMarker = state.markerLayer.getLayers().find(
      (m) => m.getLatLng && m.getLatLng().lat === asset.latitude && m.getLatLng().lng === asset.longitude
    );
    // Derive a reasonable halo radius from production volume
    const vol = kbbl || 0;
    const volR = Math.min(20, 6 + Math.sqrt(vol / 50));
    const haloR = Math.round(volR + 7);
    L.circleMarker([asset.latitude, asset.longitude], {
      radius: haloR,
      color: isHigh ? "#ef4444" : "#f97316",
      weight: 1.5,
      fillOpacity: 0,
      opacity: isHigh ? 0.7 : 0.45,
      dashArray: "4 3",
    }).addTo(group);
  }
  state.riskBufferLayer = group;
  group.addTo(state.map);
  // Keep risk buffers below markers but above formations
  if (state.formationLayer) state.formationLayer.bringToBack();
}

function renderFireLayer() {
  if (!state.map || !window.L) return;
  if (state.fireLayer) { state.map.removeLayer(state.fireLayer); state.fireLayer = null; }

  // Always (re)render provincial layers alongside CWFIS
  renderAlbertaFireLayer();
  renderBCFireLayer();

  if (!state.wildfireEnabled || !state.wildfires?.features?.length) return;

  const SEVERITY_COLOR = { extreme: "#b91c1c", high: "#ef4444", moderate: "#f97316", low: "#f6ad55", unknown: "#64748b" };

  state.fireLayer = L.geoJSON(state.wildfires, {
    pointToLayer(feature, latlng) {
      const score = fireScore(feature);
      const sev = fireSeverity(score);
      const color = SEVERITY_COLOR[sev.className] || "#f97316";
      const r = sev.className === "extreme" ? 7 : sev.className === "high" ? 6 : sev.className === "moderate" ? 5 : 4;
      return L.circleMarker(latlng, {
        radius: r,
        color: "#fff",
        weight: 1,
        fillColor: color,
        fillOpacity: 0.88,
        opacity: 0.9,
      });
    },
    onEachFeature(feature, layer) {
      const p = feature.properties || {};
      const score = fireScore(feature);
      const sev = fireSeverity(score);
      const fwi = score != null ? `FWI ${score.toFixed(1)} – ${sev.label}` : sev.label;
      const fuel = p.fuel && p.fuel !== "-1" ? ` · ${escapeHtml(String(p.fuel))}` : "";
      const date = p.rep_date ? p.rep_date.slice(0, 10) : "";
      layer.bindTooltip(
        `<strong>Fire hotspot</strong> (${escapeHtml(p.agency || "?")})<br>` +
        `${escapeHtml(fwi)}${fuel}<br>` +
        `${escapeHtml(p.sensor || "")}${date ? " · " + date : ""}`,
        { opacity: 0.95 }
      );
    },
  }).addTo(state.map);
}

async function boot() {
  try {
    await loadData();
    initControls();
    initMap();
    // Auto-enable fire layers on every open — fetches run in parallel,
    // map updates as each source resolves.
    state.wildfireEnabled = true;
    updateFireToggleUI();
    updateFormationToggleUI();
    updateWildfireStatus("Fetching live wildfire data…");
    render();
    // Kick off both fire sources in parallel (non-blocking)
    fetchWildfires();
    fetchAlbertaFires();
    fetchBCFires();
  } catch (error) {
    console.error(error);
    if (els.freshness) {
      els.freshness.textContent = "Data export failed to load. Run: python scripts/run_etl.py";
    }
    if (els.map) {
      els.map.innerHTML = `
        <div class="load-error">
          <h2>Production data did not load</h2>
          <p>${escapeHtml(error.message || error)}</p>
          <code>python scripts/run_etl.py</code>
        </div>`;
    }
  }
}

boot();

// ============================================================
// RUBBER-BAND MULTI-ASSET SELECTION
// Right-click + drag to draw a selection rectangle.
// All visible production markers inside are selected.
// ============================================================

function initRubberBand() {
  const mapEl = document.getElementById("map");
  const btn   = document.getElementById("selectModeBtn");
  if (!mapEl) return;

  let selectMode = false;
  let startX, startY, box, active = false;

  function setSelectMode(on) {
    selectMode = on;
    if (btn) {
      btn.classList.toggle("active", on);
      btn.title = on ? "Click to exit select mode (or press Esc)" : "Click to select multiple assets";
    }
    mapEl.style.cursor = on ? "crosshair" : "";
  }

  if (btn) {
    btn.addEventListener("click", () => setSelectMode(!selectMode));
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && selectMode) setSelectMode(false);
  });

  function getBox() {
    if (!box) {
      box = document.createElement("div");
      box.id = "rubberBand";
      box.style.cssText =
        "position:absolute;border:2px dashed #2980b9;background:rgba(41,128,185,0.10);" +
        "pointer-events:none;z-index:2000;display:none;";
      mapEl.appendChild(box);
    }
    return box;
  }

  mapEl.addEventListener("mousedown", (e) => {
    if (!selectMode || e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const rect = mapEl.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;
    const b = getBox();
    b.style.left = startX + "px";
    b.style.top  = startY + "px";
    b.style.width  = "0";
    b.style.height = "0";
    b.style.display = "block";
    active = true;
    state.rubberBandActive = true;
    state.map.dragging.disable();
    state.map.off("click");   // prevent single-click asset select while dragging
  }, true);

  document.addEventListener("mousemove", (e) => {
    if (!active || !box) return;
    const rect = mapEl.getBoundingClientRect();
    const curX = e.clientX - rect.left;
    const curY = e.clientY - rect.top;
    box.style.left   = Math.min(startX, curX) + "px";
    box.style.top    = Math.min(startY, curY) + "px";
    box.style.width  = Math.abs(curX - startX) + "px";
    box.style.height = Math.abs(curY - startY) + "px";
  });

  document.addEventListener("mouseup", (e) => {
    if (!active) return;
    active = false;
    state.rubberBandActive = false;
    state.map.dragging.enable();
    if (!box) return;

    const bLeft   = parseFloat(box.style.left)   || 0;
    const bTop    = parseFloat(box.style.top)    || 0;
    const bRight  = bLeft + (parseFloat(box.style.width)  || 0);
    const bBottom = bTop  + (parseFloat(box.style.height) || 0);
    box.style.display = "none";

    // Ignore tiny drags (accidental clicks)
    if (bRight - bLeft < 6 || bBottom - bTop < 6) return;

    const { byAsset } = aggregateForDate();
    const hits = [];
    for (const { asset } of byAsset.values()) {
      if (asset.latitude == null) continue;
      // latLngToContainerPoint returns px relative to map container — same as our box coords
      const pt = state.map.latLngToContainerPoint([asset.latitude, asset.longitude]);
      if (pt.x >= bLeft && pt.x <= bRight && pt.y >= bTop && pt.y <= bBottom) {
        hits.push(asset.asset_id);
      }
    }

    if (hits.length > 0) {
      state.selectedAssets = hits;
      showSeasonalityPanel(hits);
    }

    // Exit select mode after each selection
    setSelectMode(false);
  });
}

// ============================================================
// SEASONALITY CHART PANEL
// Shows 12-month production profile for selected assets with:
//   - 5-year min/max envelope (light grey band)
//   - 2 full past years (coloured lines)
//   - Most recent partial year (dots only for known months)
// ============================================================

const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const SEA_COLORS   = { band: "#d1d5db", y0: "#2563eb", y1: "#16a34a", yCur: "#dc2626" };

function computeSeasonality(assetIds) {
  // Returns { ym: { year: { month(1-12): kbbl } }, years, currentYear, latestFull }
  const ym = {};

  // --- AER / base records (already in memory, all dates) ---
  const allBase = state.baseRecords;
  for (const r of allBase) {
    if (!assetIds.includes(r.asset_id)) continue;
    const year  = Number(r.date.slice(0, 4));
    const month = Number(r.date.slice(5, 7));
    if (!ym[year]) ym[year] = {};
    ym[year][month] = (ym[year][month] || 0) + r.volume_kbbl_d;
  }

  // --- Petrinex / seasonality index (pre-aggregated compact lookup) ---
  if (state.seasonalityIndex) {
    for (const aid of assetIds) {
      const entry = state.seasonalityIndex[aid];
      if (!entry) continue;
      for (const [ym_str, vol] of Object.entries(entry)) {
        const year  = Number(ym_str.slice(0, 4));
        const month = Number(ym_str.slice(5, 7));
        if (!ym[year]) ym[year] = {};
        ym[year][month] = (ym[year][month] || 0) + vol;
      }
    }
  }

  const years = Object.keys(ym).map(Number).sort();
  if (!years.length) return null;

  const currentYear = years[years.length - 1];
  let latestFull = null;
  for (let i = years.length - 1; i >= 0; i--) {
    if (Object.keys(ym[years[i]]).length === 12) { latestFull = years[i]; break; }
  }

  return { ym, years, currentYear, latestFull };
}

async function showSeasonalityPanel(assetIds) {
  // Remove any existing panel
  const existing = document.getElementById("seasonalityPanel");
  if (existing) existing.remove();

  // Lazy-load the Petrinex seasonality index (47 MB, loaded once)
  if (!state.seasonalityIndex && !state.seasonalityIndexLoading) {
    state.seasonalityIndexLoading = true;
    // Show loading panel immediately
    const loadingPanel = document.createElement("div");
    loadingPanel.id = "seasonalityPanel";
    loadingPanel.innerHTML = `
      <div class="sea-header">
        <div><strong class="sea-title">Loading historical data…</strong>
        <span class="sea-sub">Fetching Petrinex production index (first time only)</span></div>
      </div>
      <div style="padding:24px;text-align:center;color:#6b7280;font-size:13px;">
        <div style="margin-bottom:8px">⏳ Building seasonality from full Petrinex history…</div>
      </div>`;
    document.getElementById("map").appendChild(loadingPanel);
    try {
      const resp = await fetch("public/data/asset_seasonality.json");
      state.seasonalityIndex = await resp.json();
    } catch(e) {
      console.warn("Could not load asset_seasonality.json:", e);
      state.seasonalityIndex = {};
    }
    state.seasonalityIndexLoading = false;
    // Remove loading panel and re-run
    loadingPanel.remove();
  } else if (state.seasonalityIndexLoading) {
    // Already loading — retry after a moment
    setTimeout(() => showSeasonalityPanel(assetIds), 300);
    return;
  }

  const data = computeSeasonality(assetIds);
  const { byAsset } = aggregateForDate();

  // Build title from selected asset names
  const names = assetIds.slice(0, 3).map(id => {
    const hit = byAsset.get(id);
    return hit ? hit.asset.display_name : id;
  });
  const titleStr = names.join(", ") + (assetIds.length > 3 ? ` +${assetIds.length - 3} more` : "");

  // Create panel
  const panel = document.createElement("div");
  panel.id = "seasonalityPanel";
  panel.innerHTML = `
    <div class="sea-header">
      <div>
        <strong class="sea-title">${escapeHtml(titleStr)}</strong>
        <span class="sea-sub">${assetIds.length} asset${assetIds.length > 1 ? "s" : ""} · 12-month seasonality</span>
      </div>
      <button id="closeSeasonality" class="sea-close" title="Close">&#x2715;</button>
    </div>
    <canvas id="seasonalityCanvas" width="580" height="240"></canvas>
    <div class="sea-legend" id="seaLegend"></div>
  `;
  document.getElementById("map").appendChild(panel);

  document.getElementById("closeSeasonality").addEventListener("click", () => {
    panel.remove();
    state.selectedAssets = [];
  });

  if (!data) {
    panel.querySelector("canvas").insertAdjacentHTML("afterend",
      '<p style="padding:12px;color:#6b7280">No production data for selected assets.</p>');
    return;
  }

  drawSeasonalityChart(data, assetIds.length);
}

function drawSeasonalityChart(data, assetCount) {
  const canvas = document.getElementById("seasonalityCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const pad = { top: 16, right: 20, bottom: 36, left: 58 };
  const cW = W - pad.left - pad.right;
  const cH = H - pad.top - pad.bottom;

  const { ym, years, currentYear, latestFull } = data;

  // Pick years to show: envelope from up to 5 full years, 2 past full, current
  const fullYears = years.filter(y => y !== currentYear && Object.keys(ym[y] || {}).length === 12);
  const envYears  = fullYears.slice(-5);
  const lineYears = fullYears.slice(-2);  // 2 most recent full years

  // Build per-month envelope (min/max) across envYears
  const envMin = new Array(12).fill(Infinity);
  const envMax = new Array(12).fill(-Infinity);
  for (const y of envYears) {
    for (let m = 1; m <= 12; m++) {
      const v = ym[y]?.[m] ?? 0;
      if (v < envMin[m-1]) envMin[m-1] = v;
      if (v > envMax[m-1]) envMax[m-1] = v;
    }
  }
  // Replace Infinity with 0 if no env data
  for (let i = 0; i < 12; i++) {
    if (envMin[i] === Infinity)  envMin[i] = 0;
    if (envMax[i] === -Infinity) envMax[i] = 0;
  }

  // Global max for Y scale
  let globalMax = 0;
  for (const y of [...envYears, ...lineYears, currentYear]) {
    for (let m = 1; m <= 12; m++) {
      const v = ym[y]?.[m] ?? 0;
      if (v > globalMax) globalMax = v;
    }
  }
  if (globalMax === 0) globalMax = 1;

  const xPos = (m) => pad.left + ((m - 0.5) / 12) * cW;  // m = 1..12
  const yPos = (v) => pad.top + cH - (v / globalMax) * cH;

  // Clear
  ctx.clearRect(0, 0, W, H);

  // Background
  ctx.fillStyle = "#f9fafb";
  ctx.fillRect(0, 0, W, H);

  // Draw Y gridlines
  ctx.strokeStyle = "#e5e7eb";
  ctx.lineWidth = 1;
  const ticks = 4;
  for (let t = 0; t <= ticks; t++) {
    const v = (globalMax / ticks) * t;
    const y = yPos(v);
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(Math.round(v).toLocaleString(), pad.left - 5, y + 3);
  }

  // Y axis label
  ctx.save();
  ctx.translate(12, pad.top + cH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillStyle = "#6b7280";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("kbbl/d", 0, 0);
  ctx.restore();

  // X axis labels
  ctx.fillStyle = "#6b7280";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "center";
  for (let m = 1; m <= 12; m++) {
    ctx.fillText(MONTH_LABELS[m-1], xPos(m), H - pad.bottom + 14);
  }

  // Draw envelope band (5yr min-max)
  if (envYears.length > 0) {
    ctx.beginPath();
    for (let m = 1; m <= 12; m++) ctx.lineTo(xPos(m), yPos(envMax[m-1]));
    for (let m = 12; m >= 1; m--) ctx.lineTo(xPos(m), yPos(envMin[m-1]));
    ctx.closePath();
    ctx.fillStyle = "rgba(156,163,175,0.28)";
    ctx.fill();
    // Envelope outline
    ctx.beginPath();
    for (let m = 1; m <= 12; m++) {
      m === 1 ? ctx.moveTo(xPos(m), yPos(envMax[m-1])) : ctx.lineTo(xPos(m), yPos(envMax[m-1]));
    }
    ctx.strokeStyle = "rgba(156,163,175,0.5)";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.stroke();
    ctx.beginPath();
    for (let m = 1; m <= 12; m++) {
      m === 1 ? ctx.moveTo(xPos(m), yPos(envMin[m-1])) : ctx.lineTo(xPos(m), yPos(envMin[m-1]));
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Draw 2 full past years
  const lineColors = [SEA_COLORS.y0, SEA_COLORS.y1];
  lineYears.forEach((yr, i) => {
    ctx.beginPath();
    for (let m = 1; m <= 12; m++) {
      const v = ym[yr]?.[m] ?? 0;
      m === 1 ? ctx.moveTo(xPos(m), yPos(v)) : ctx.lineTo(xPos(m), yPos(v));
    }
    ctx.strokeStyle = lineColors[i % 2];
    ctx.lineWidth = 1.8;
    ctx.stroke();
  });

  // Draw current (partial) year — dots only for known months
  const curMonths = Object.keys(ym[currentYear] || {}).map(Number);
  if (curMonths.length) {
    ctx.strokeStyle = SEA_COLORS.yCur;
    ctx.fillStyle = SEA_COLORS.yCur;
    ctx.lineWidth = 2;
    // Connect known months with a line
    const sorted = curMonths.sort((a,b) => a-b);
    ctx.beginPath();
    sorted.forEach((m, i) => {
      const v = ym[currentYear][m] ?? 0;
      i === 0 ? ctx.moveTo(xPos(m), yPos(v)) : ctx.lineTo(xPos(m), yPos(v));
    });
    ctx.stroke();
    // Dots on each known month
    sorted.forEach(m => {
      const v = ym[currentYear][m] ?? 0;
      ctx.beginPath();
      ctx.arc(xPos(m), yPos(v), 3.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // Legend
  const legEl = document.getElementById("seaLegend");
  if (legEl) {
    const enStr = envYears.length ? `${envYears[0]}–${envYears[envYears.length-1]} range` : "";
    legEl.innerHTML = [
      envYears.length ? `<span><i style="background:rgba(156,163,175,0.45)"></i>${enStr}</span>` : "",
      ...lineYears.map((y, i) => `<span><i style="background:${lineColors[i]}"></i>${y}</span>`),
      curMonths.length ? `<span><i style="background:${SEA_COLORS.yCur};border-radius:50%"></i>${currentYear} (known months)</span>` : "",
    ].filter(Boolean).join("");
  }
}
