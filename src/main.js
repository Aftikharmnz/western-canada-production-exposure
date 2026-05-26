// ============================================================
// DATA PATHS
// ============================================================

window.__PRODUCTION_APP_MODULE_LOADED__ = true;

const DATA_PATHS = {
  manifest: "public/data/manifest.json",
  assets: "public/data/assets.json",
  production: "public/data/monthly_production.json",
  schemeApprovals: "public/data/aer_scheme_approvals.geojson",
  st102Facilities: "public/data/aer_st102_oil_sands_facilities.geojson",
  assetGeometries: "public/data/asset_geometries.geojson",
  refineries: "public/data/refineries.geojson",
  marketPipelines: "public/data/market_access_pipelines.geojson",
  marketTariffs: "public/data/market_access_tariffs.json",
  pipelineIndex: "public/data/aer_pipeline_index.json",
};

// ============================================================
// PRODUCTION SYSTEM METADATA  (map marker colour + label)
// ============================================================

const SYSTEM_META = {
  in_situ:           { label: "In-situ Bitumen",        color: "#008b8b", className: "in-situ" },
  mined:             { label: "Mined Bitumen",           color: "#d29b18", className: "mined" },
  conventional:      { label: "Conventional Crude",      color: "#4f8f45", className: "conventional" },
  pentanes_plus:     { label: "Pentanes Plus",            color: "#7c3aed", className: "pentanes-plus" },
  heavy_conventional:{ label: "Heavy Crude (Conv.)",     color: "#c2720a", className: "heavy-conv" },
  synthetic:         { label: "Synthetic Crude Oil",     color: "#2980b9", className: "synthetic" },
  condensate:        { label: "Condensate",              color: "#6374a6", className: "condensate" },
  gas_plant:         { label: "Gas Plant (NGL extraction)",  color: "#e07b39", className: "gas-plant",         useSystemColor: true },
  integrated_plant:  { label: "Integrated Plant (NGL+frac)", color: "#7c3aed", className: "integrated-plant",  useSystemColor: true },
  spec_plant:        { label: "Spec Plant (fractionation)",  color: "#c9a227", className: "spec-plant",        useSystemColor: true },
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
  "Pentanes plus total":         "#7c3aed",
  "Dilbit equivalent":           "#005f5f",
  "Ultra-Heavy":                 "#8b1a1a",
  "Ultra-H Dilbit":              "#c0392b",
  "Heavy Dilbit":                "#c74c0a",
  "Heavy crude oil":             "#c2720a",
  "Light & medium crude oil":    "#27ae60",
  "Light crude production":      "#7bb53a",
  "Other lights Excluding AB":   "#9dc63b",
  "Condensate Production":       "#7d5fa5",
  "Total Condensate Supply":     "#9b59b6",
  "Condensate Imports":          "#b39ddb",
  "Condensate production":       "#7d5fa5",
  "Propane mix":                 "#e07b39",
  "Propane spec":                "#f4a261",
  "Butane mix":                  "#c9a227",
  "Butane spec":                 "#e9c46a",
  "Total WC crude":              "#7f8c8d",
  "Total Oil Sands Dilbit + SCO":"#2c3e50",
  "Blend Ratio":                 "#95a5a6",
  "Medium":                      "#e08c3a",
  "Heavy":                       "#c2720a",
  "Light":                       "#8bc34a",
};

// ============================================================
// STREAM DESCRIPTIONS  (shown as tooltip on stream toggles)
// ============================================================

const STREAM_DESCRIPTIONS = {
  "Propane mix":  "C3-MX · Raw propane mix extracted at gas processing plants — not yet fractionated to sales grade",
  "Propane spec": "C3-SP · Sales-grade propane produced at fractionation or integrated gas plants",
  "Butane mix":   "C4-MX · Raw butane mix extracted at gas processing plants — not yet fractionated to sales grade",
  "Butane spec":  "C4-SP · Sales-grade butane produced at fractionation or integrated gas plants",
};

// ============================================================
// SOURCE LABELS
// ============================================================

const SOURCE_SHORT = {
  aer_st53:             "AER ST53",
  aer_st39:             "AER ST39",
  petrinex_ab_conventional_vol: "Petrinex AB",
  petrinex_ab_pentanes_plus_vol: "Petrinex AB C5+",
  petrinex_ab_condensate_vol:    "Petrinex AB COND",
  petrinex_ab_ngl_vol:           "Petrinex AB NGL",
  bcer_well_production:          "BCER wells",
  petrinex_bc_facility_ids: "Petrinex BC ref",
  petrinex_bc_formation_codes: "Petrinex BC ref",
  petrinex_bc_activity_codes: "Petrinex BC ref",
};

// Streams shown by default on first load
const PRIMARY_STREAMS = [
  "In-situ bitumen",
  "Mined bitumen gross",
  "Synthetic crude oil",
];

const STREAM_LEGEND_KEYS = {
  "In-situ bitumen": "in-situ",
  "Mined bitumen gross": "mined",
  "Synthetic crude oil": "synthetic",
  "Conventional crude oil": "conventional",
  "Pentanes plus total": "pentanes-plus",
  "Heavy crude oil": "heavy-conv",
  "Condensate Production": "condensate",
  "Condensate production": "condensate",
  "Total Condensate Supply": "condensate",
  // Propane mix / spec / Butane mix / spec intentionally omitted —
  // pointLegendKey falls back to production_system className (gas-plant /
  // integrated-plant / spec-plant) which is set per facility in the ETL.
};

const LOCATION_CONFIDENCE_META = {
  exact:     { label: "Exact point",       short: "Exact",     className: "quality-exact" },
  high:      { label: "Project polygon",   short: "Polygon",   className: "quality-high" },
  medium:    { label: "Official centroid", short: "Centroid",  className: "quality-medium" },
  low:       { label: "Approximate",       short: "Approx.",   className: "quality-low" },
  aggregate: { label: "Aggregate",         short: "Aggregate", className: "quality-aggregate" },
  unmapped:  { label: "Unmapped",          short: "Unmapped",  className: "quality-unmapped" },
  unknown:   { label: "Unknown",           short: "Unknown",   className: "quality-unknown" },
};

const DEFAULT_LOCATION_CONFIDENCE = ["exact", "high", "medium", "low", "aggregate", "unmapped", "unknown"];

const DEFAULT_HIDDEN_LEGEND_KEYS = [
  "fire-zone",
  "pipe-hvp",
  "pipe-diluent",
  "inst-pump",
  "inst-compressor",
  "inst-terminal",
  "inst-meter",
];

const DEFAULT_REFINERY_GROUP_KEYS = [
  "canada-western",
  "canada-central",
  "canada-eastern",
  "us-padd-ii",
  "us-padd-v",
];

const POINT_LEGEND_KEYS = new Set([
  "in-situ",
  "mined",
  "synthetic",
  "conventional",
  "pentanes-plus",
  "condensate",
  "gas-plant",
  "integrated-plant",
  "spec-plant",
  "heavy-conv",
]);

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
  baseRecordsByDate: new Map(),   // pre-indexed for O(1) date lookup
  timelineCache: null,            // cached bar totals; null = dirty
  dateRecordLoading: new Set(),
  dateRecordErrors: new Map(),
  geojson: null,
  schemeApprovals: null,
  st102Facilities: null,
  assetGeometries: null,
  refineries: null,
  assetGeometryById: new Map(),
  dates: [],
  selectedDate: null,
  selectedAssetId: null,
  selectedSources: new Set(),
  selectedStreams: new Set(),
  selectedLocationConfidence: new Set(DEFAULT_LOCATION_CONFIDENCE),
  company: "All",
  search: "",
  map: null,
  markerLayer: null,
  assetMarkerLayersByLegendKey: new Map(),
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
  fireMenuOpen: false,
  // Formation overlay state
  formationEnabled: false,
  formationLayer: null,
  assetFootprintLayer: null,
  formationMenuOpen: false,
  refineryEnabled: false,
  refineryLayer: null,
  refineryMenuOpen: false,
  selectedRefineryGroups: new Set(DEFAULT_REFINERY_GROUP_KEYS),
  marketPipelineEnabled: false,
  marketPipelineData: null,
  marketTariffData: null,
  marketPipelineLoading: false,
  marketPipelineError: null,
  marketPipelineLineLayer: null,
  marketHubLayer: null,
  selectedMarketPipelineIds: new Set(),
  marketHubsEnabled: true,
  marketPipelineMenuOpen: false,
  // Seasonality index (lazy-loaded from asset_seasonality.json)
  seasonalityIndex: null,
  seasonalityIndexLoading: false,
  // Multi-asset rubber-band selection
  selectedAssets: [],
  rubberBandActive: false,
  selectMode: false,
  setSelectMode: null,
  hiddenLegendKeys: new Set(DEFAULT_HIDDEN_LEGEND_KEYS),
  distanceMode: false,
  distancePoints: [],
  distanceLayer: null,
  facilityLayer: null,
};

// ============================================================
// DOM REFERENCES
// ============================================================

const els = {
  freshness:        document.querySelector("#freshness"),
  dateSelect:       document.querySelector("#dateSelect"),
  selectedDate:     document.querySelector("#selectedDate"),
  dateScenario:     document.querySelector("#dateScenario"),
  coverageNotice:   document.querySelector("#coverageNotice"),
  sourceFilters:    document.querySelector("#sourceFilters"),
  streamFilters:    document.querySelector("#streamFilters"),
  locationQualityFilters: document.querySelector("#locationQualityFilters"),
  searchInput:      document.querySelector("#searchInput"),
  totalShown:       document.querySelector("#totalShown"),
  mappedCount:      document.querySelector("#mappedCount"),
  unmappedVolume:   document.querySelector("#unmappedVolume"),
  largestPoint:     document.querySelector("#largestPoint"),
  fireExposureRow:  document.querySelector("#fireExposureRow"),
  fireExposure:     document.querySelector("#fireExposure"),
  detailTitle:      document.querySelector("#detailTitle"),
  detailSubtitle:   document.querySelector("#detailSubtitle"),
  detailVolume:     document.querySelector("#detailVolume"),
  detailSource:     document.querySelector("#detailSource"),
  detailStatus:     document.querySelector("#detailStatus"),
  detailLocationQuality: document.querySelector("#detailLocationQuality"),
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
  docsBtn:          document.querySelector("#docsBtn"),
  docsPanel:        document.querySelector("#docsPanel"),
  closeDocs:        document.querySelector("#closeDocs"),
  wildfireToggle:   document.querySelector("#wildfireToggle"),
  wildfireStatus:   document.querySelector("#wildfireStatus"),
  formationToggle:  document.querySelector("#formationToggle"),
  refineryToggle:   document.querySelector("#refineryToggle"),
  distanceToggle:   document.querySelector("#distanceToggle"),
  distanceStatus:   document.querySelector("#distanceStatus"),
  mapLegend:        document.querySelector("#mapLegend"),
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

function legendVisible(key) {
  return !key || !state.hiddenLegendKeys.has(key);
}

function pointLegendKey(point) {
  const topStream = [...point.streams.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
  return STREAM_LEGEND_KEYS[topStream] || systemMeta(point.asset.production_system).className;
}

function formationLegendKey(feature) {
  const kind = feature?.properties?.kind;
  if (kind === "in_situ_scheme") return "formation-os";
  if (kind === "mineable_scheme" || kind === "oil_sands") return "formation-tp";
  return "";
}

function albertaFireLegendKey(feature) {
  const p = feature?.properties || {};
  if (p.FIRE_TYPE === "Municipal")  return "ab-fire-mun";
  if (p.FIRE_TYPE === "Mutual Aid") return "ab-fire-ma";
  if (p.CO_FLAG === "Y") return "ab-fire-carryover";
  if (p.FIRE_STATUS === "Out of Control") return "ab-fire-oc";
  if (p.FIRE_STATUS === "Being Held") return "ab-fire-bh";
  if (p.FIRE_STATUS === "Under Control") return "ab-fire-uc";
  return "ab-fire-uc";
}

function bcFireLegendKey(feature) {
  const p = feature?.properties || {};
  if (p.FIRE_OF_NOTE_IND === "Y") return "bc-fire-fon";
  if (p.FIRE_STATUS === "Out of Control") return "bc-fire-oc";
  if (p.FIRE_STATUS === "Being Held") return "bc-fire-bh";
  if (p.FIRE_STATUS === "Under Control") return "bc-fire-uc";
  return "bc-fire-uc";
}

function locationConfidenceKey(asset) {
  const key = asset?.location_confidence || "unknown";
  return LOCATION_CONFIDENCE_META[key] ? key : "unknown";
}

function locationConfidenceMeta(assetOrKey) {
  const key = typeof assetOrKey === "string" ? assetOrKey : locationConfidenceKey(assetOrKey);
  return LOCATION_CONFIDENCE_META[key] || LOCATION_CONFIDENCE_META.unknown;
}

function locationQualityText(asset) {
  const meta = locationConfidenceMeta(asset);
  const method = asset?.coordinate_method ? ` · ${asset.coordinate_method.replaceAll("_", " ")}` : "";
  return `${meta.short}${method}`;
}

// ============================================================
// DATA LOADING
// ============================================================

async function loadData() {
  const appDataPaths = [
    DATA_PATHS.manifest,
    DATA_PATHS.assets,
    DATA_PATHS.production,
    DATA_PATHS.schemeApprovals,
    DATA_PATHS.st102Facilities,
    DATA_PATHS.assetGeometries,
    DATA_PATHS.refineries,
  ];
  const [manifest, assets, records, schemeApprovals, st102Facilities, assetGeometries, refineries] = await Promise.all(
    appDataPaths.map((path) =>
      fetch(path).then((r) => {
        if (!r.ok) throw new Error(`Could not load ${path}`);
        return r.json();
      })
    )
  );
  const assetRows = expandAssetRecords(assets);
  state.manifest = manifest;
  state.assets = assetRows;
  state.assetById = new Map(assetRows.map((a) => [a.asset_id, a]));
  state.baseRecords = records;
  state.records = records;
  // Build O(1) date index so recordsForDate never scans the full array
  const _byDate = new Map();
  for (const r of records) {
    let bucket = _byDate.get(r.date);
    if (!bucket) { bucket = []; _byDate.set(r.date, bucket); }
    bucket.push(r);
  }
  state.baseRecordsByDate = _byDate;
  state.geojson = null;
  state.schemeApprovals = schemeApprovals;
  state.st102Facilities = st102Facilities;
  state.assetGeometries = assetGeometries;
  state.refineries = refineries;
  state.assetGeometryById = new Map();
  for (const feature of assetGeometries?.features || []) {
    const assetId = feature?.properties?.asset_id;
    if (!assetId) continue;
    const bucket = state.assetGeometryById.get(assetId) || [];
    bucket.push(feature);
    state.assetGeometryById.set(assetId, bucket);
  }
  state.dates = manifest.periods || [...new Set(records.map((r) => r.date))].sort();
  state.selectedDate = manifest.default_date || manifest.latest_actual_date || state.dates.at(-1);
  if (!state.dates.includes(state.selectedDate)) state.selectedDate = state.dates.at(-1);
  await ensureDateRecords(state.selectedDate);
  state.records = recordsForDate(state.selectedDate);

  const sourceIds = [...new Set(records.map((r) => r.source_id))].sort();
  recordsForDate(state.selectedDate).forEach((r) => sourceIds.push(r.source_id));
  [...new Set(sourceIds)].sort().forEach((s) => state.selectedSources.add(s));

  const initialRecords = recordsForDate(state.selectedDate);
  [...new Set(initialRecords.map((r) => r.stream))].forEach((s) => state.selectedStreams.add(s));
}

function expandAssetRecords(raw) {
  if (Array.isArray(raw)) return raw;
  if (!raw || !Array.isArray(raw.fields) || !Array.isArray(raw.rows)) return [];
  return raw.rows.map((row) => {
    const asset = {};
    raw.fields.forEach((field, idx) => {
      asset[field] = row[idx];
    });
    return asset;
  });
}

function recordsForDate(date = state.selectedDate) {
  // O(1) indexed lookup — no full-array scan
  const base = state.baseRecordsByDate.get(date) || [];
  const onDemand = state.dateRecordCache.get(date) || [];
  return onDemand.length ? [...base, ...onDemand] : base;
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
      // New on-demand records loaded — invalidate timeline total for this date
      if (state.timelineCache) state.timelineCache.delete(date);
      render();
    }
  });
}

// ============================================================
// CONTROLS INIT
// ============================================================

function initControls() {
  const sourceCount = new Set((state.manifest.source_coverage || []).map((item) => item.source_id)).size;
  els.freshness.textContent = `ETL: ${new Date(state.manifest.generated_at).toLocaleString("en-CA")} · default: ${dateLabel(state.manifest.default_date || state.manifest.latest_actual_date)} · ${formatNumber(state.manifest.record_count)} records · ${sourceCount || "--"} sources`;

  if (els.dateSelect) {
    els.dateSelect.innerHTML = state.dates
      .map((date) => `<option value="${escapeHtml(date)}">${escapeHtml(dateLabel(date))}</option>`)
      .join("");
    els.dateSelect.value = state.selectedDate;
    els.dateSelect.addEventListener("change", () => {
      state.selectedDate = els.dateSelect.value;
      requestDateRecords(state.selectedDate);
      scheduleRender();
    });
  }

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

  if (els.locationQualityFilters) {
    els.locationQualityFilters.innerHTML = DEFAULT_LOCATION_CONFIDENCE
      .map((key) => toggleMarkupLocationQuality(key))
      .join("");
    els.locationQualityFilters.addEventListener(
      "change",
      (e) => updateSetFromToggle(e, "confidence", state.selectedLocationConfidence)
    );
  }

  // company select removed

  els.searchInput.addEventListener("input", () => {
    state.search = els.searchInput.value.trim().toLowerCase();
    state.timelineCache = null;
    scheduleRender();
  });

  els.etlCommand.textContent = "python scripts/run_etl.py --download";
  els.etlButton.addEventListener("click", () => { els.etlPanel.hidden = false; });
  els.closeEtl.addEventListener("click", () => { els.etlPanel.hidden = true; });

  // ── Docs panel ──
  if (els.docsBtn && els.docsPanel) {
    els.docsBtn.addEventListener("click", () => {
      els.docsPanel.hidden = false;
      els.docsBtn.classList.add("active");
    });
    els.closeDocs.addEventListener("click", () => {
      els.docsPanel.hidden = true;
      els.docsBtn.classList.remove("active");
    });
    els.docsPanel.addEventListener("keydown", e => {
      if (e.key === "Escape") { els.docsPanel.hidden = true; els.docsBtn.classList.remove("active"); }
    });
    // Tab switching
    els.docsPanel.querySelectorAll(".docs-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        els.docsPanel.querySelectorAll(".docs-tab").forEach(t => t.classList.remove("active"));
        els.docsPanel.querySelectorAll(".docs-section").forEach(s => { s.hidden = true; });
        tab.classList.add("active");
        const sec = els.docsPanel.querySelector(`#tab-${tab.dataset.tab}`);
        if (sec) sec.hidden = false;
      });
    });
  }

  if (els.wildfireToggle) {
    els.wildfireToggle.addEventListener("click", toggleWildfires);
  }
  const fireMenu = document.getElementById("fireMenu");
  if (fireMenu) {
    fireMenu.addEventListener("change", handleFireMenuChange);
    fireMenu.addEventListener("click", handleFireMenuClick);
    buildFireMenu();
  }
  if (els.formationToggle) {
    els.formationToggle.addEventListener("click", toggleFormations);
  }
  const formationMenu = document.getElementById("formationMenu");
  if (formationMenu) {
    formationMenu.addEventListener("change", handleFormationMenuChange);
    formationMenu.addEventListener("click", handleFormationMenuClick);
    buildFormationMenu();
  }
  if (els.refineryToggle) {
    els.refineryToggle.addEventListener("click", toggleRefineries);
  }
  const refineryMenu = document.getElementById("refineryMenu");
  if (refineryMenu) {
    refineryMenu.addEventListener("change", handleRefineryMenuChange);
    refineryMenu.addEventListener("click", handleRefineryMenuClick);
    buildRefineryMenu();
  }
  const pipelineToggleBtn = document.getElementById("pipelineToggle");
  if (pipelineToggleBtn) {
    pipelineToggleBtn.addEventListener("click", togglePipelines);
  }
  const pipelineMenu = document.getElementById("pipelineMenu");
  if (pipelineMenu) {
    pipelineMenu.addEventListener("change", handlePipelineMenuChange);
    pipelineMenu.addEventListener("click", handlePipelineMenuClick);
  }
  const marketPipelineToggleBtn = document.getElementById("marketPipelineToggle");
  if (marketPipelineToggleBtn) {
    marketPipelineToggleBtn.addEventListener("click", toggleMarketPipelines);
  }
  const marketPipelineMenu = document.getElementById("marketPipelineMenu");
  if (marketPipelineMenu) {
    marketPipelineMenu.addEventListener("change", handleMarketPipelineMenuChange);
    marketPipelineMenu.addEventListener("click", handleMarketPipelineMenuClick);
  }
  document.addEventListener("click", (event) => {
    const control = document.getElementById("marketPipelineControl");
    if (control && !control.contains(event.target)) {
      setMarketPipelineMenuOpen(false);
    }
    const pipelineControl = document.getElementById("pipelineControl");
    if (pipelineControl && !pipelineControl.contains(event.target)) {
      setPipelineMenuOpen(false);
    }
    const formationControl = document.getElementById("formationControl");
    if (formationControl && !formationControl.contains(event.target)) {
      setFormationMenuOpen(false);
    }
    const refineryControl = document.getElementById("refineryControl");
    if (refineryControl && !refineryControl.contains(event.target)) {
      setRefineryMenuOpen(false);
    }
    const fireControl = document.getElementById("fireControl");
    if (fireControl && !fireControl.contains(event.target)) {
      setFireMenuOpen(false);
    }
  });
  initLegendControls();
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
  const desc = STREAM_DESCRIPTIONS[stream] || stream;
  return `
    <label class="toggle-item" title="${escapeHtml(desc)}">
      <input type="checkbox" data-group="stream" value="${escapeHtml(stream)}" ${checked ? "checked" : ""} />
      <span class="stream-swatch-label">
        <i class="stream-swatch" style="background:${color}"></i>
        ${escapeHtml(stream)}
      </span>
    </label>`;
}

function toggleMarkupLocationQuality(key) {
  const meta = locationConfidenceMeta(key);
  const checked = state.selectedLocationConfidence.has(key);
  return `
    <label class="toggle-item location-quality-item" title="${escapeHtml(meta.label)}">
      <input type="checkbox" data-group="confidence" value="${escapeHtml(key)}" ${checked ? "checked" : ""} />
      <span><i class="quality-dot ${meta.className}"></i>${escapeHtml(meta.label)}</span>
    </label>`;
}

function updateSetFromToggle(event, group, targetSet) {
  const input = event.target.closest(`input[data-group="${group}"]`);
  if (!input) return;
  if (input.checked) targetSet.add(input.value);
  else targetSet.delete(input.value);
  state.selectedAssetId = null;
  state.timelineCache = null; // filters changed — invalidate bar chart cache
  scheduleRender();
}

function initLegendControls() {
  if (!els.mapLegend) return;
  els.mapLegend.addEventListener("click", (event) => {
    const item = event.target.closest("[data-legend-key]");
    if (!item) return;
    const key = item.getAttribute("data-legend-key");
    if (!key) return;
    if (state.hiddenLegendKeys.has(key)) state.hiddenLegendKeys.delete(key);
    else state.hiddenLegendKeys.add(key);

    let handledFast = false;
    if (["formation-os", "formation-tp", "asset-footprint", "st102-facility"].includes(key)) {
      if (state.formationLayer) { state.map.removeLayer(state.formationLayer); state.formationLayer = null; }
      if (state.facilityLayer) { state.map.removeLayer(state.facilityLayer); state.facilityLayer = null; }
      if (state.assetFootprintLayer) { state.map.removeLayer(state.assetFootprintLayer); state.assetFootprintLayer = null; }
      renderFormationLayer();
      handledFast = true;
    }
    if (key === "refinery-plant") {
      if (state.refineryLayer) {
        state.map.removeLayer(state.refineryLayer);
        state.refineryLayer = null;
      }
      renderRefineryLayer();
      handledFast = true;
    }
    if (key.startsWith("pipe-") || key.startsWith("inst-")) {
      refreshPipelineLayers();
      handledFast = true;
    }
    if (POINT_LEGEND_KEYS.has(key) && state.map && state.markerLayer) {
      applyMarkerLegendVisibility();
      handledFast = true;
    }

    updateLegendControls();
    renderCoverageNotice(state.selectedDate);
    if (els.dateScenario) els.dateScenario.textContent = scenarioLabelForDate(state.selectedDate);
    if (!handledFast) scheduleRender();
  });
  updateLegendControls();
}
function updateLegendControls() {
  if (!els.mapLegend) return;
  els.mapLegend.querySelectorAll("[data-legend-key]").forEach((item) => {
    const key = item.getAttribute("data-legend-key");
    const visible = legendVisible(key);
    item.classList.toggle("muted", !visible);
    item.setAttribute("aria-pressed", visible ? "true" : "false");
  });
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
  initRubberBand();
  initDistanceTool();
  state.map.on("moveend zoomend", schedulePipelineTileRefresh);
}

function initDistanceTool() {
  if (!state.map || !window.L) return;
  state.distanceLayer = L.layerGroup().addTo(state.map);
  if (els.distanceToggle) {
    els.distanceToggle.addEventListener("click", () => setDistanceMode(!state.distanceMode));
  }
  state.map.on("click", (event) => {
    if (!state.distanceMode || state.rubberBandActive) return;
    handleDistanceClick(event.latlng);
  });
  updateDistanceToggleUI();
}

function setDistanceMode(on) {
  state.distanceMode = Boolean(on);
  if (state.distanceMode && typeof state.setSelectMode === "function") {
    state.setSelectMode(false);
  }
  if (state.distanceMode) {
    clearDistanceMeasurement();
    updateDistanceStatus("Click first point");
  } else {
    clearDistanceMeasurement();
  }
  if (state.map) {
    state.map.getContainer().classList.toggle("distance-mode-active", state.distanceMode);
  }
  updateDistanceToggleUI();
}

function updateDistanceToggleUI() {
  if (!els.distanceToggle) return;
  els.distanceToggle.textContent = state.distanceMode ? "Distance ON" : "Distance";
  els.distanceToggle.classList.toggle("active", state.distanceMode);
}

function updateDistanceStatus(message) {
  if (!els.distanceStatus) return;
  els.distanceStatus.textContent = message || "";
  els.distanceStatus.hidden = !message;
}

function clearDistanceMeasurement() {
  state.distancePoints = [];
  if (state.distanceLayer) state.distanceLayer.clearLayers();
  updateDistanceStatus("");
}

function formatDistanceKm(km) {
  if (!Number.isFinite(km)) return "--";
  if (km < 10) return `${km.toFixed(2)} km`;
  if (km < 100) return `${km.toFixed(1)} km`;
  return `${Math.round(km).toLocaleString("en-CA")} km`;
}

// Returns intermediate lat/lng points along the great-circle arc between two coords.
// Makes the polyline follow the true geodesic path rather than a straight Mercator line.
function geodesicPoints(lat1, lon1, lat2, lon2, steps = 64) {
  const d2r = Math.PI / 180;
  const r2d = 180 / Math.PI;
  const phi1 = lat1 * d2r, lam1 = lon1 * d2r;
  const phi2 = lat2 * d2r, lam2 = lon2 * d2r;
  const dphi = phi2 - phi1, dlam = lam2 - lam1;
  const aa = Math.sin(dphi/2)**2 + Math.cos(phi1)*Math.cos(phi2)*Math.sin(dlam/2)**2;
  const angDist = 2 * Math.atan2(Math.sqrt(aa), Math.sqrt(1 - aa));
  if (angDist < 0.0001) return [[lat1, lon1], [lat2, lon2]];
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const ff = i / steps;
    const A = Math.sin((1-ff)*angDist) / Math.sin(angDist);
    const B = Math.sin(ff*angDist)    / Math.sin(angDist);
    const x = A*Math.cos(phi1)*Math.cos(lam1) + B*Math.cos(phi2)*Math.cos(lam2);
    const y = A*Math.cos(phi1)*Math.sin(lam1) + B*Math.cos(phi2)*Math.sin(lam2);
    const z = A*Math.sin(phi1)               + B*Math.sin(phi2);
    pts.push([Math.atan2(z, Math.sqrt(x*x+y*y))*r2d, Math.atan2(y, x)*r2d]);
  }
  return pts;
}

// Snaps a click to the nearest visible asset within SNAP_PX pixels.
// Returns { latlng, label } or null if nothing close enough.
function snapToNearestAsset(clickLatlng) {
  const SNAP_PX = 20;
  const { byAsset } = aggregateForDate();
  let best = null, bestDist = Infinity;
  for (const point of byAsset.values()) {
    const { asset } = point;
    if (asset.latitude == null || !legendVisible(pointLegendKey(point))) continue;
    const pt    = state.map.latLngToContainerPoint([asset.latitude, asset.longitude]);
    const click = state.map.latLngToContainerPoint(clickLatlng);
    const px = Math.hypot(pt.x - click.x, pt.y - click.y);
    if (px < SNAP_PX && px < bestDist) {
      bestDist = px;
      best = { latlng: L.latLng(asset.latitude, asset.longitude), label: asset.display_name };
    }
  }
  return best;
}

function handleDistanceClick(latlng) {
  if (!state.distanceMode || !state.distanceLayer || !latlng || !window.L) return;
  if (state.distancePoints.length >= 2) {
    clearDistanceMeasurement();
  }

  // Snap to nearest visible asset within 20 screen pixels for accuracy
  const snapped = snapToNearestAsset(latlng);
  const point   = snapped ? snapped.latlng : L.latLng(latlng.lat, latlng.lng);
  point._label  = snapped ? snapped.label : null;
  state.distancePoints.push(point);

  L.circleMarker(point, {
    radius:      snapped ? 7 : 5,
    color:       snapped ? "#2563eb" : "#0f172a",
    weight:      2,
    fillColor:   "#ffffff",
    fillOpacity: 1,
    interactive: false,
  }).addTo(state.distanceLayer);

  if (snapped) {
    L.tooltip({ permanent: true, direction: "top", className: "distance-snap-label", offset: [0, -10] })
      .setContent(snapped.label)
      .setLatLng(point)
      .addTo(state.distanceLayer);
  }

  if (state.distancePoints.length === 1) {
    updateDistanceStatus(snapped ? `From: ${snapped.label} — click second point` : "Click second point");
    return;
  }

  const [a, b] = state.distancePoints;
  const km    = haversineKm(a.lat, a.lng, b.lat, b.lng);
  const label = formatDistanceKm(km);

  // Draw geodesic arc so the line follows Earth's curvature, not Mercator distortion
  const arcPts = geodesicPoints(a.lat, a.lng, b.lat, b.lng, 64);
  L.polyline(arcPts, {
    color:     "#0f172a",
    weight:    2.5,
    opacity:   0.95,
    dashArray: "6 5",
    interactive: false,
  })
    .bindTooltip(label, {
      permanent:  true,
      direction:  "center",
      className:  "distance-tooltip",
    })
    .addTo(state.distanceLayer);

  const aName = a._label, bName = b._label;
  const statusMsg = (aName && bName)
    ? `${aName} → ${bName}: ${label}`
    : (aName || bName) ? `${aName || bName}: ${label}`
    : `Distance: ${label}`;
  updateDistanceStatus(statusMsg);
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
    if (!state.selectedLocationConfidence.has(locationConfidenceKey(asset))) return false;
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

function selectedDateSummaryRows(date = state.selectedDate) {
  const rows = state.manifest?.date_filter_totals?.[date] || [];
  return rows.filter((row) =>
    state.selectedSources.has(row.source_id) &&
    state.selectedStreams.has(row.stream) &&
    state.selectedLocationConfidence.has(row.location_confidence || "unknown") &&
    legendVisible(row.legend_key)
  );
}

function scenarioLabelForDate(date = state.selectedDate) {
  if (state.dateRecordLoading.has(date)) return "loading";
  if (state.dateRecordErrors.has(date)) return "partial load";
  const rows = selectedDateSummaryRows(date);
  const scenarios = new Set(rows.map((row) => row.scenario).filter(Boolean));
  const warnings = state.manifest?.data_quality?.date_warnings?.[date] || [];
  if (warnings.some((w) => w.severity === "high")) return "data warning";
  if (scenarios.has("actual") && scenarios.has("forecast")) return "mixed";
  if (scenarios.has("forecast")) return "forecast";
  if (scenarios.has("actual")) return "actual";
  return "no coverage";
}

function renderCoverageNotice(date = state.selectedDate) {
  if (!els.coverageNotice) return;
  const warnings = state.manifest?.data_quality?.date_warnings?.[date] || [];
  const rows = selectedDateSummaryRows(date);
  const low = rows
    .filter((row) => row.location_confidence === "low")
    .reduce((sum, row) => sum + Number(row.kbbl_d || 0), 0);
  const unmapped = rows
    .filter((row) => row.location_confidence === "unmapped")
    .reduce((sum, row) => sum + Number(row.kbbl_d || 0), 0);
  const sources = new Set(rows.map((row) => row.source_id));
  const messages = [];
  if (warnings.length) {
    messages.push(...warnings.slice(0, 2).map((w) => w.message));
  }
  if (low > 0) {
    messages.push(`${kbbl(low)} uses approximate DLS/manual coordinates; use caution for exact fire impact.`);
  }
  if (unmapped > 0) {
    messages.push(`${kbbl(unmapped)} is currently unmapped or aggregate-only for this date.`);
  }
  if (!rows.length) {
    messages.push("No mapped source coverage matches the active filters for this month.");
  }
  if (!messages.length) {
    els.coverageNotice.hidden = true;
    els.coverageNotice.innerHTML = "";
    return;
  }
  const title = warnings.length ? "Data quality warning" : `Coverage note · ${sources.size || 0} source${sources.size === 1 ? "" : "s"}`;
  els.coverageNotice.className = `coverage-notice${warnings.length ? "" : " info"}`;
  els.coverageNotice.innerHTML = `<strong>${escapeHtml(title)}</strong>${messages.map(escapeHtml).join("<br>")}`;
  els.coverageNotice.hidden = false;
}

// ============================================================
// MAIN RENDER ORCHESTRATOR
// ============================================================

// rAF-based debounce: multiple synchronous calls in the same frame
// collapse into one render at the next animation frame.
let _renderPending = false;
function scheduleRender() {
  if (_renderPending) return;
  _renderPending = true;
  requestAnimationFrame(() => { _renderPending = false; render(); });
}

function render() {
  requestDateRecords(state.selectedDate);
  if (els.dateSelect && els.dateSelect.value !== state.selectedDate) {
    els.dateSelect.value = state.selectedDate;
  }
  els.selectedDate.textContent = dateLabel(state.selectedDate);
  els.dateScenario.textContent = scenarioLabelForDate(state.selectedDate);
  renderCoverageNotice(state.selectedDate);
  // Compute once and pass to all sub-renders — avoids 3× redundant aggregation
  const aggregated = aggregateForDate();
  renderMap(aggregated);
  renderMetrics(aggregated);
  renderDetails(aggregated);
  renderTimeline();
}

// ============================================================
// MAP RENDER
// ============================================================

function markerGroupForLegend(key) {
  if (!state.assetMarkerLayersByLegendKey) state.assetMarkerLayersByLegendKey = new Map();
  if (!state.assetMarkerLayersByLegendKey.has(key)) {
    state.assetMarkerLayersByLegendKey.set(key, L.layerGroup());
  }
  return state.assetMarkerLayersByLegendKey.get(key);
}

function applyMarkerLegendVisibility() {
  if (!state.markerLayer || !state.assetMarkerLayersByLegendKey) return;
  for (const [key, group] of state.assetMarkerLayersByLegendKey.entries()) {
    const visible = legendVisible(key);
    const shown = state.markerLayer.hasLayer(group);
    if (visible && !shown) state.markerLayer.addLayer(group);
    if (!visible && shown) state.markerLayer.removeLayer(group);
  }
}

function renderMap(aggregated) {
  const { byAsset } = aggregated || aggregateForDate();
  const points = [...byAsset.values()].filter(
    ({ asset, kbbl: v }) => asset.latitude != null && asset.longitude != null && v > 0
  );
  const visiblePoints = points.filter((point) => legendVisible(pointLegendKey(point)));

  if (state.map && state.markerLayer && window.L) {
    state.markerLayer.clearLayers();
    state.assetMarkerLayersByLegendKey = new Map();
    points.forEach((point) => {
      const legendKey = pointLegendKey(point);
      const meta = systemMeta(point.asset.production_system);
      const color = meta.color;
      const isSelected = point.asset.asset_id === state.selectedAssetId;
      const radius = Math.max(5, Math.min(34, Math.sqrt(point.kbbl) * 1.9));
      const topStream = [...point.streams.entries()].sort((a, b) => b[1] - a[1])[0];
      const markerColor = (meta.useSystemColor || !topStream) ? color : streamColor(topStream[0]);

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
      const sortedStreams = [...point.streams.entries()].sort((a, b) => b[1] - a[1]);
      const ttLines = [
        `<strong>${escapeHtml(point.asset.display_name)}</strong>`,
        escapeHtml(point.asset.company || point.asset.province),
        kbbl(point.kbbl),
        `<em>${escapeHtml(meta.label)}</em>`,
        `Location: ${escapeHtml(locationQualityText(point.asset))}`,
      ];
      sortedStreams.forEach(([stream, vol]) => {
        const swatch = `<i style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${streamColor(stream)};margin-right:4px;"></i>`;
        ttLines.push(`${swatch}${escapeHtml(stream)}: ${kbbl(vol)}`);
      });
      marker.bindTooltip(ttLines.join("<br>"), { direction: "top", opacity: 0.96, className: "asset-tip" });
      marker.on("click", (event) => {
        if (state.distanceMode) {
          if (event.originalEvent && window.L) L.DomEvent.stop(event.originalEvent);
          handleDistanceClick(event.latlng);
          return;
        }
        state.selectedAssetId = point.asset.asset_id;
        render();
      });
      marker.addTo(markerGroupForLegend(legendKey));
    });
    applyMarkerLegendVisibility();

    renderFormationLayer();
    renderRefineryLayer();
    renderFireLayer();
  } else {
    renderFallbackMap(visiblePoints);
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

function renderMetrics(aggregated) {
  const { byAsset, sourceTotals } = aggregated || aggregateForDate();
  const exposureAssets = [...byAsset.values()].filter(({ asset, kbbl: v }) => !asset.is_rollup && v > 0);
  const points = exposureAssets.filter(({ asset }) => asset.latitude != null && asset.longitude != null);
  const total = points.reduce((s, p) => s + p.kbbl, 0);
  const unmappedTotal = exposureAssets
    .filter(({ asset }) => asset.latitude == null || asset.longitude == null)
    .reduce((s, p) => s + p.kbbl, 0);
  const allTotal = total + unmappedTotal;
  const largest = points.reduce((best, p) => (!best || p.kbbl > best.kbbl ? p : best), null);
  els.totalShown.textContent = kbbl(total);
  els.mappedCount.textContent = formatNumber(points.length);
  if (els.unmappedVolume) els.unmappedVolume.textContent = kbbl(unmappedTotal);
  els.largestPoint.textContent = largest ? kbbl(largest.kbbl) : "--";

  // Source breakdown (sidebar)
  const totalBySource = [...sourceTotals.entries()].sort((a, b) => b[1] - a[1]);
  els.sourceBreakdown.innerHTML = totalBySource.slice(0, 6).map(([src, val]) => {
    const pct = allTotal > 0 ? Math.min(100, (val / allTotal) * 100) : 0;
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
      if (!asset.is_rollup && v > 0)
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
      if (!asset.is_rollup && v > 0) {
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
    if (state.wildfireEnabled && activeFireFeatures(true).length) {
      let atRiskKbbl = 0;
      for (const { asset, kbbl: v } of byAsset.values()) {
        if (asset.latitude == null) continue;
        if (getAssetFireRisk(asset).level !== "none") atRiskKbbl += v;
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

function renderDetails(aggregated) {
  const { byAsset } = aggregated || aggregateForDate();
  let selected = state.selectedAssetId ? byAsset.get(state.selectedAssetId) : null;
  if (!selected) selected = [...byAsset.values()].sort((a, b) => b.kbbl - a.kbbl)[0] || null;

  if (!selected) {
    els.detailTitle.textContent = "No matching production";
    els.detailSubtitle.textContent = "Adjust filters or date.";
    els.detailVolume.textContent = "--";
    els.detailSource.textContent = "--";
    els.detailStatus.textContent = "--";
    if (els.detailLocationQuality) els.detailLocationQuality.textContent = "--";
    renderTopAssets(aggregated);
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
  if (els.detailLocationQuality) {
    const quality = locationConfidenceMeta(asset);
    els.detailLocationQuality.textContent = locationQualityText(asset);
    els.detailLocationQuality.className = `quality-value ${quality.className}`;
  }

  renderTopAssets(aggregated);
  renderStreamBreakdown(asset.asset_id, selected.streams);
  renderFireRisk(asset);
}

// ============================================================
// TOP ASSETS TABLE  (replaces sparkline)
// ============================================================

function renderTopAssets(aggregated) {
  const el = document.getElementById("topAssetsList");
  const labelEl = document.getElementById("topAssetsLabel");
  if (!el) return;

  const { byAsset } = aggregated || aggregateForDate();
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
    const quality = locationConfidenceMeta(asset);

    const riskBadge = "";

    return `<div class="top-asset-row${isSelected ? " selected" : ""}" data-id="${escapeHtml(String(asset.asset_id))}">
      <span class="top-rank">${i + 1}</span>
      <i class="top-swatch" style="background:${color}"></i>
      <span class="top-name">${escapeHtml(asset.display_name)}</span>
      <span class="quality-pill ${quality.className}">${escapeHtml(quality.short)}</span>
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
  if (!state.wildfireEnabled || asset.latitude == null) {
    els.fireRiskSection.hidden = true;
    return;
  }
  els.fireRiskSection.hidden = false;

  if (state.wildfireLoading || state.albertaFireLoading || state.bcFireLoading) {
    els.fireRiskBadge.textContent = "Loading…";
    els.fireRiskBadge.className = "risk-badge loading";
    els.fireDistDisplay.textContent = "--";
    els.fireVolAtRisk.textContent = "--";
    return;
  }

  const risk = getAssetFireRisk(asset);
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
  // Build timeline totals once per filter-state; reuse on subsequent renders.
  // state.timelineCache is set to null whenever filters change.
  if (!state.timelineCache) {
    const cache = new Map();
    for (const date of state.dates) {
      let total;
      const hasOnDemandFile = Boolean(state.manifest?.monthly_record_files?.[date]);
      // For unloaded on-demand files, combine:
      //   (a) base records (oil sands, petrinex NGL — always in memory) via aggregateForDate()
      //   (b) on-demand totals (BC, AB conventional) from pre-computed date_filter_totals.
      // This ensures timeline bars reflect all sources even before a date is navigated to.
      if (hasOnDemandFile && !state.dateRecordCache.has(date) && !state.search) {
        const { byAsset: baseByAsset } = aggregateForDate(date);
        const baseTotal = [...baseByAsset.values()].reduce((s, p) => s + p.kbbl, 0);
        const onDemandTotal = selectedDateSummaryRows(date).reduce((sum, row) => sum + Number(row.kbbl_d || 0), 0);
        total = baseTotal + onDemandTotal;
      }
      if (!Number.isFinite(total)) {
        const { byAsset } = aggregateForDate(date);
        total = [...byAsset.values()].reduce((s, p) => s + p.kbbl, 0);
      }
      cache.set(date, total || 0);
    }
    state.timelineCache = cache;
  }
  const rows = state.dates.map((date) => ({ date, total: state.timelineCache.get(date) || 0 }));
  const max = Math.max(...rows.map((r) => r.total), 1);
  const selectedIndex = rows.findIndex((r) => r.date === state.selectedDate);
  const windowStart = Math.max(0, selectedIndex - 30);
  const visible = rows.slice(windowStart, Math.min(rows.length, windowStart + 72));
  if (els.timelineLabel) {
    els.timelineLabel.textContent = `${visible.length} monthly observations in view`;
  }
  if (els.timelineBars) {
    els.timelineBars.innerHTML = visible.map((row) => {
      const height = Math.max(3, (row.total / max) * 72);
      const sel = row.date === state.selectedDate;
      return `<button class="timeline-bar ${sel ? "selected" : ""}" style="height:${height}px" title="${dateLabel(row.date)} ${kbbl(row.total)}" data-date="${row.date}" aria-label="${dateLabel(row.date)} ${kbbl(row.total)}"></button>`;
    }).join("");
    els.timelineBars.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedDate = btn.dataset.date;
        if (els.dateSelect) els.dateSelect.value = state.selectedDate;
        render();
      });
    });
  }
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

const FORMATION_MENU_ITEMS = [
  { key: "formation-os", label: "In-situ Approval", color: "#2dd4bf", type: "area" },
  { key: "formation-tp", label: "Mineable Approval", color: "#f59e0b", type: "area" },
  { key: "st102-facility", label: "ST102 Facility", color: "#ffffff", type: "dot" },
  { key: "asset-footprint", label: "Production Footprint", color: "#2980b9", type: "area" },
];

const FORMATION_CORE_KEYS = new Set(["formation-os", "formation-tp", "st102-facility", "asset-footprint"]);

function formationSelectedCount() {
  return FORMATION_MENU_ITEMS.filter((item) => !state.hiddenLegendKeys.has(item.key)).length;
}

function setFormationMenuOpen(open) {
  state.formationMenuOpen = open;
  const menu = document.getElementById("formationMenu");
  if (menu) menu.hidden = !open;
  updateFormationToggleUI();
}

function formationCounts() {
  const counts = { "formation-os": 0, "formation-tp": 0, "st102-facility": 0, "asset-footprint": 0 };
  for (const feature of state.schemeApprovals?.features || []) {
    const key = formationLegendKey(feature);
    if (key) counts[key] = (counts[key] || 0) + 1;
  }
  counts["st102-facility"] = state.st102Facilities?.features?.length || 0;
  counts["asset-footprint"] = state.assetGeometries?.features?.length || 0;
  return counts;
}

function buildFormationMenu() {
  const options = document.getElementById("formationOptions");
  if (!options) return;
  const counts = formationCounts();
  options.innerHTML = FORMATION_MENU_ITEMS.map((item) => {
    const checked = !state.hiddenLegendKeys.has(item.key);
    const swatchClass = item.type === "area" ? "formation-area-swatch" : "formation-dot-swatch";
    return `
      <label class="formation-option">
        <input type="checkbox" data-formation-key="${escapeHtml(item.key)}" ${checked ? "checked" : ""} />
        <span class="${swatchClass}" style="background:${item.color}"></span>
        <span class="formation-option-text">
          <strong>${escapeHtml(item.label)}</strong>
          <em>${(counts[item.key] || 0).toLocaleString("en-CA")} features</em>
        </span>
      </label>`;
  }).join("");
}

function handleFormationMenuChange(event) {
  const input = event.target.closest("input[data-formation-key]");
  if (!input) return;
  const key = input.dataset.formationKey;
  if (input.checked) state.hiddenLegendKeys.delete(key);
  else state.hiddenLegendKeys.add(key);
  state.formationEnabled = formationSelectedCount() > 0;
  refreshFormationLayers();
  updateFormationToggleUI();
}

function handleFormationMenuClick(event) {
  const action = event.target.closest("[data-formation-action]")?.dataset.formationAction;
  if (!action) return;
  for (const item of FORMATION_MENU_ITEMS) {
    if (action === "all") {
      state.hiddenLegendKeys.delete(item.key);
    } else if (action === "none") {
      state.hiddenLegendKeys.add(item.key);
    } else if (action === "core") {
      if (FORMATION_CORE_KEYS.has(item.key)) state.hiddenLegendKeys.delete(item.key);
      else state.hiddenLegendKeys.add(item.key);
    }
  }
  state.formationEnabled = formationSelectedCount() > 0;
  buildFormationMenu();
  refreshFormationLayers();
  updateFormationToggleUI();
}

function refreshFormationLayers() {
  if (state.formationLayer) { state.map.removeLayer(state.formationLayer); state.formationLayer = null; }
  if (state.facilityLayer) { state.map.removeLayer(state.facilityLayer); state.facilityLayer = null; }
  if (state.assetFootprintLayer) { state.map.removeLayer(state.assetFootprintLayer); state.assetFootprintLayer = null; }
  renderFormationLayer();
}

function renderFormationLayer() {
  if (!state.map || !window.L) return;
  // Only clear+redraw when toggled (not every render tick) — skip if
  // the layer already exists and enabled state hasn't changed.
  if (!state.formationEnabled) {
    if (state.formationLayer) {
      state.map.removeLayer(state.formationLayer);
      state.formationLayer = null;
    }
    if (state.assetFootprintLayer) {
      state.map.removeLayer(state.assetFootprintLayer);
      state.assetFootprintLayer = null;
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
      filter(feature) {
        return legendVisible(formationLegendKey(feature));
      },
      style(feature) {
        return FORMATION_KIND_STYLE[feature.properties?.kind] || FORMATION_KIND_STYLE.in_situ_scheme;
      },
      onEachFeature(feature, layer) {
        const p = feature.properties || {};
        const name = p.name || p.scheme_no || "AER scheme approval";
        const badgeClass = (p.layer || "").toLowerCase().includes("mineab") ? "mineable" : "insitu";
        const badgeLabel = (p.layer || "").toLowerCase().includes("mineab") ? "Mineable" : "In-situ";
        layer.bindTooltip(
          `<div>` +
          `<strong>${escapeHtml(name)}</strong>` +
          `<span class="ft-badge ${badgeClass}">${badgeLabel}</span>` +
          `${p.holder ? `<div class="ft-sub">${escapeHtml(p.holder)}</div>` : ""}` +
          `${p.scheme_no ? `<div class="ft-sub">Scheme ${escapeHtml(p.scheme_no)}</div>` : ""}` +
          `</div>`,
          { sticky: true, opacity: 0.92, className: "formation-tip" }
        );
      },
    }).addTo(state.map);

    // Push project footprints behind production markers and fire hotspots.
    state.formationLayer.bringToBack();
  }

  renderAssetFootprintLayer();

  const facilities = state.st102Facilities;
  if (facilities?.features?.length && !state.facilityLayer && legendVisible("st102-facility")) {
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
          `<div>` +
          `<strong>${escapeHtml(p.name || "ST102 facility")}</strong>` +
          `<div class="ft-sub">${escapeHtml(p.subtype || "Facility")}</div>` +
          `${p.operator ? `<div class="ft-sub">${escapeHtml(p.operator)}</div>` : ""}` +
          `${p.facility_id || p.status ? `<div class="ft-sub">${p.facility_id ? escapeHtml(p.facility_id) + " · " : ""}${escapeHtml(p.status || "")}</div>` : ""}` +
          `</div>`,
          { sticky: true, opacity: 0.92, className: "formation-tip" }
        );
      },
    }).addTo(state.map);
  }
}

function renderAssetFootprintLayer() {
  if (!state.map || !window.L) return;
  if (state.assetFootprintLayer) {
    state.map.removeLayer(state.assetFootprintLayer);
    state.assetFootprintLayer = null;
  }
  const source = state.assetGeometries;
  if (!source?.features?.length || !legendVisible("asset-footprint")) return;

  const { byAsset } = aggregateForDate();
  state.assetFootprintLayer = L.geoJSON(source, {
    filter(feature) {
      const assetId = feature.properties?.asset_id;
      const point = byAsset.get(assetId);
      if (!point || point.kbbl <= 0) return false;
      if (!legendVisible(pointLegendKey(point))) return false;
      return state.selectedLocationConfidence.has(locationConfidenceKey(point.asset));
    },
    style(feature) {
      const point = byAsset.get(feature.properties?.asset_id);
      const topStream = point ? [...point.streams.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] : null;
      const color = topStream ? streamColor(topStream) : systemMeta(feature.properties?.production_system).color;
      return {
        color,
        fillColor: color,
        fillOpacity: 0.28,
        weight: 2.2,
        opacity: 0.92,
      };
    },
    onEachFeature(feature, layer) {
      const p = feature.properties || {};
      const point = byAsset.get(p.asset_id);
      const asset = point?.asset || state.assetById.get(p.asset_id);
      layer.bindTooltip(
        `<strong style="font-size:12px">${escapeHtml(p.display_name || "Production footprint")}</strong><br>` +
          `${point ? kbbl(point.kbbl) + "<br>" : ""}` +
          `${escapeHtml(p.geometry_source || "Asset geometry")}<br>` +
          `Location: ${escapeHtml(locationQualityText(asset))}`,
        { sticky: true, opacity: 0.94, className: "formation-tip" }
      );
      layer.on("click", () => {
        if (p.asset_id) {
          state.selectedAssetId = p.asset_id;
          render();
        }
      });
    },
  }).addTo(state.map);

  if (state.formationLayer?.bringToBack) state.formationLayer.bringToBack();
  state.assetFootprintLayer.bringToBack();
  if (state.formationLayer?.bringToBack) state.formationLayer.bringToBack();
}

function toggleFormations() {
  state.formationEnabled = formationSelectedCount() > 0;
  setFormationMenuOpen(!state.formationMenuOpen);
  refreshFormationLayers();
  updateFormationToggleUI();
}

function updateFormationToggleUI() {
  const btn = els.formationToggle;
  if (!btn) return;
  const selectedCount = formationSelectedCount();
  if (state.formationEnabled && selectedCount) {
    btn.textContent = `AER Sites (${selectedCount})`;
    btn.title = `${selectedCount.toLocaleString("en-CA")} AER site overlays selected`;
    btn.className = "formation-toggle-btn active";
    btn.setAttribute("aria-expanded", state.formationMenuOpen ? "true" : "false");
  } else {
    btn.textContent = "AER Sites";
    btn.title = "AER oil sands approvals and ST102 facilities";
    btn.className = "formation-toggle-btn";
    btn.setAttribute("aria-expanded", state.formationMenuOpen ? "true" : "false");
  }
}

function refineryCapacityLabel(value, uom) {
  if (value == null || value === "") return "";
  const n = Number(value);
  const formatted = Number.isFinite(n) ? n.toLocaleString("en-CA") : String(value);
  return `${formatted}${uom ? " " + uom : ""}`;
}

function refineryCapacityRowsHtml(rows, limit = 8) {
  const capacities = Array.isArray(rows) ? rows : [];
  if (!capacities.length) return '<div class="refinery-unit-row muted">No unit capacity rows provided</div>';
  const shown = capacities.slice(0, limit).map((item) => {
    const actual = refineryCapacityLabel(item.actual_capacity, item.uom);
    const design = refineryCapacityLabel(item.design_capacity, item.uom);
    const value = actual || design || "--";
    const basis = actual ? "Actual" : (design ? "Design" : "");
    const kind = item.kind ? `${escapeHtml(item.kind)} · ` : "";
    return `<div class="refinery-unit-row">` +
      `<span>${kind}${escapeHtml(item.product_desc || item.product_id || "Capacity unit")}</span>` +
      `<strong>${escapeHtml(value)}</strong>` +
      `${basis ? `<em>${basis}</em>` : ""}` +
      `</div>`;
  }).join("");
  const extra = capacities.length > limit
    ? `<div class="refinery-unit-row muted">+ ${capacities.length - limit} more unit rows</div>`
    : "";
  return shown + extra;
}

function refineryTooltipHtml(properties) {
  const p = properties || {};
  const capacity = refineryCapacityLabel(p.crud_capacity_bbl_d, "BBL/d");
  const location = [p.city, p.state_name, p.country_name].filter(Boolean).join(", ");
  const operator = p.operator_name || p.owner_name || p.parent_company || "";
  const sector = p.plant_sectors || p.primary_sic_desc || "";
  return `<div class="refinery-tip-inner">` +
    `<strong>${escapeHtml(p.plant_name || "Refinery / upgrader")}</strong>` +
    `${operator ? `<div class="rt-sub">${escapeHtml(operator)}</div>` : ""}` +
    `${location ? `<div class="rt-sub">${escapeHtml(location)}</div>` : ""}` +
    `<div class="rt-meta">` +
      `${p.plant_status_desc ? `<span>${escapeHtml(p.plant_status_desc)}</span>` : ""}` +
      `${capacity ? `<span>${escapeHtml(capacity)}</span>` : ""}` +
    `</div>` +
    `${sector ? `<div class="rt-sub">${escapeHtml(sector)}</div>` : ""}` +
    `<div class="refinery-units">${refineryCapacityRowsHtml(p.unit_capacities)}</div>` +
  `</div>`;
}

function refineryUnitCapacityText(unit) {
  if (!unit) return "";
  const direct = refineryCapacityLabel(unit.capacity, unit.capacity_uom);
  if (direct) return direct;
  const kbbl = refineryCapacityLabel(unit.capacity_kbbl_d, "kbbl/d");
  if (kbbl) return kbbl;
  const rows = Array.isArray(unit.capacity_rows) ? unit.capacity_rows : [];
  const first = rows.find((row) => row.capacity != null || row.actual_capacity != null || row.design_capacity != null);
  if (!first) return "";
  return refineryCapacityLabel(first.capacity ?? first.actual_capacity ?? first.design_capacity, first.uom);
}

function refineryUnitProductText(unit) {
  if (!unit) return "";
  if (unit.unit_capacity_product_desc) return unit.unit_capacity_product_desc;
  const rows = Array.isArray(unit.capacity_rows) ? unit.capacity_rows : [];
  return rows.map((row) => row.product_desc).filter(Boolean).slice(0, 2).join(", ");
}

function refineryAreaNameIsUseful(area, unitName) {
  if (!area) return false;
  const a = String(area).toLowerCase();
  const u = String(unitName || "").toLowerCase();
  return a !== u && !["crude", "refinery"].includes(a);
}

function refineryUnitRowsHtml(units, limit = 10) {
  const rows = Array.isArray(units) ? units : [];
  if (!rows.length) return '<div class="refinery-unit-card muted">No detailed unit rows linked to this plant</div>';
  const shown = rows.slice(0, limit).map((unit) => {
    const cap = refineryUnitCapacityText(unit);
    const product = refineryUnitProductText(unit);
    const type = unit.unit_type_short || unit.unit_type_group || "Unit";
    const status = unit.unit_status_desc || unit.unit_status_group || "";
    const area = refineryAreaNameIsUseful(unit.area_name, unit.unit_name) ? unit.area_name : "";
    return `<div class="refinery-unit-card">` +
      `<div class="ru-head">` +
        `<span class="ru-type">${escapeHtml(type)}</span>` +
        `<strong>${escapeHtml(unit.unit_name || unit.unit_type_desc || "Refinery unit")}</strong>` +
        `${cap ? `<em>${escapeHtml(cap)}</em>` : ""}` +
      `</div>` +
      `<div class="ru-sub">${escapeHtml([unit.unit_type_desc, product, area].filter(Boolean).join(" · "))}</div>` +
      `${status ? `<div class="ru-status">${escapeHtml(status)}${unit.unit_startup_date ? " · Start " + escapeHtml(String(unit.unit_startup_date).slice(0, 10)) : ""}</div>` : ""}` +
    `</div>`;
  }).join("");
  const extra = rows.length > limit
    ? `<div class="refinery-unit-card muted">+ ${rows.length - limit} more units in click popup</div>`
    : "";
  return shown + extra;
}

function refineryUnitSummaryHtml(summary) {
  const rows = Array.isArray(summary) ? summary : [];
  if (!rows.length) return "";
  return `<div class="refinery-unit-summary">` +
    rows.slice(0, 8).map((item) =>
      `<span>${escapeHtml(item.group || "Unit")} <strong>${formatNumber(item.count || 0)}</strong></span>`
    ).join("") +
  `</div>`;
}

function refineryTooltipDetailedHtml(properties) {
  const p = properties || {};
  const capacity = refineryCapacityLabel(p.crud_capacity_bbl_d, "BBL/d");
  const location = [p.city, p.state_name, p.country_name].filter(Boolean).join(", ");
  const operator = p.operator_name || p.owner_name || p.parent_company || "";
  const sector = p.plant_sectors || p.primary_sic_desc || "";
  const units = Array.isArray(p.refinery_units) ? p.refinery_units : [];
  const plantCapacities = p.plant_capacities || p.unit_capacities || [];
  return `<div class="refinery-tip-inner">` +
    `<strong>${escapeHtml(p.plant_name || "Refinery / upgrader")}</strong>` +
    `${operator ? `<div class="rt-sub">${escapeHtml(operator)}</div>` : ""}` +
    `${location ? `<div class="rt-sub">${escapeHtml(location)}</div>` : ""}` +
    `<div class="rt-meta">` +
      `${p.plant_status_desc ? `<span>${escapeHtml(p.plant_status_desc)}</span>` : ""}` +
      `${capacity ? `<span>${escapeHtml(capacity)}</span>` : ""}` +
      `${units.length ? `<span>${formatNumber(units.length)} units</span>` : ""}` +
    `</div>` +
    `${sector ? `<div class="rt-sub">${escapeHtml(sector)}</div>` : ""}` +
    `${units.length ? refineryUnitSummaryHtml(p.refinery_unit_summary) : ""}` +
    `<div class="refinery-units">${refineryCapacityRowsHtml(plantCapacities, 5)}</div>` +
    `${units.length ? `<div class="refinery-units detailed">${refineryUnitRowsHtml(units, 5)}</div>` : ""}` +
  `</div>`;
}

function refineryPopupHtml(properties) {
  const p = properties || {};
  const capacity = refineryCapacityLabel(p.crud_capacity_bbl_d, "BBL/d");
  const location = [p.city, p.state_name, p.country_name].filter(Boolean).join(", ");
  const operator = p.operator_name || p.owner_name || p.parent_company || "";
  const units = Array.isArray(p.refinery_units) ? p.refinery_units : [];
  const plantCapacities = p.plant_capacities || p.unit_capacities || [];
  return `<div class="refinery-popup-inner">` +
    `<h2>${escapeHtml(p.plant_name || "Refinery / upgrader")}</h2>` +
    `<div class="rp-sub">${escapeHtml([operator, location].filter(Boolean).join(" · "))}</div>` +
    `<div class="rt-meta">` +
      `${p.plant_status_desc ? `<span>${escapeHtml(p.plant_status_desc)}</span>` : ""}` +
      `${capacity ? `<span>${escapeHtml(capacity)}</span>` : ""}` +
      `${units.length ? `<span>${formatNumber(units.length)} units</span>` : ""}` +
    `</div>` +
    `${p.plant_sectors ? `<p>${escapeHtml(p.plant_sectors)}</p>` : ""}` +
    `<h3>Plant Capacities</h3>` +
    `<div class="refinery-units">${refineryCapacityRowsHtml(plantCapacities, 20)}</div>` +
    `<h3>Refinery Units</h3>` +
    `${refineryUnitSummaryHtml(p.refinery_unit_summary)}` +
    `<div class="refinery-unit-list">${refineryUnitRowsHtml(units, 160)}</div>` +
  `</div>`;
}

function refineryMarkerRadius(properties) {
  const capacity = Number(properties?.crud_capacity_kbbl_d);
  if (!Number.isFinite(capacity) || capacity <= 0) return 7;
  return Math.max(7, Math.min(20, Math.sqrt(capacity) * 1.08));
}

const REFINERY_GROUP_ITEMS = [
  { section: "Canada" },
  { key: "canada-western", label: "Western Canada" },
  { key: "canada-central", label: "Central Canada" },
  { key: "canada-eastern", label: "Eastern Canada" },
  { section: "United States" },
  { key: "us-padd-i", label: "PADD I" },
  { key: "us-padd-ii", label: "PADD II" },
  { key: "us-padd-iii", label: "PADD III" },
  { key: "us-padd-iv", label: "PADD IV" },
  { key: "us-padd-v", label: "PADD V" },
  { section: "Other North America" },
  { key: "mexico", label: "Mexico" },
  { section: "Europe" },
  { key: "europe", label: "European refineries" },
];

function refineryGroupItems() {
  return REFINERY_GROUP_ITEMS.filter((item) => !item.section);
}

function refineryGroupKey(properties) {
  const p = properties || {};
  const padd = String(p.country_padd || "").trim();
  const country = String(p.country_name || "").trim();
  const paddKey = padd.toLowerCase().replace(/\s+/g, "-");

  if (country === "Canada") {
    if (padd === "Western Canada") return "canada-western";
    if (padd === "Central Canada") return "canada-central";
    if (padd === "Eastern Canada") return "canada-eastern";
  }
  if (country === "U.S.A.") {
    if (paddKey === "padd-i") return "us-padd-i";
    if (paddKey === "padd-ii") return "us-padd-ii";
    if (paddKey === "padd-iii") return "us-padd-iii";
    if (paddKey === "padd-iv") return "us-padd-iv";
    if (paddKey === "padd-v") return "us-padd-v";
  }
  if (country === "Mexico") return "mexico";
  if (country) return "europe";
  return "other";
}

function refinerySelectedCount() {
  return refineryGroupItems().filter((item) => state.selectedRefineryGroups.has(item.key)).length;
}

function refineryVisibleFeatures() {
  return (state.refineries?.features || [])
    .filter((feature) => state.selectedRefineryGroups.has(refineryGroupKey(feature.properties)));
}

function refineryGroupCounts() {
  const counts = {};
  for (const feature of state.refineries?.features || []) {
    const key = refineryGroupKey(feature.properties);
    counts[key] = (counts[key] || 0) + 1;
  }
  return counts;
}

function setRefineryMenuOpen(open) {
  state.refineryMenuOpen = open;
  const menu = document.getElementById("refineryMenu");
  if (menu) menu.hidden = !open;
  updateRefineryToggleUI();
}

function buildRefineryMenu() {
  const options = document.getElementById("refineryOptions");
  if (!options) return;
  const counts = refineryGroupCounts();
  let currentSection = "";
  let html = "";
  for (const item of REFINERY_GROUP_ITEMS) {
    if (item.section) {
      currentSection = item.section;
      html += `<div class="refinery-menu-section">${escapeHtml(item.section)}</div>`;
      continue;
    }
    const checked = state.selectedRefineryGroups.has(item.key);
    const count = counts[item.key] ? counts[item.key].toLocaleString("en-CA") : "";
    html += `
      <label class="refinery-option" title="${escapeHtml(currentSection)}">
        <input type="checkbox" data-refinery-key="${escapeHtml(item.key)}" ${checked ? "checked" : ""} />
        <span class="refinery-dot-swatch"></span>
        <span class="refinery-option-text">
          <strong>${escapeHtml(item.label)}</strong>
          <em>${count ? `${count} plants` : currentSection}</em>
        </span>
      </label>`;
  }
  options.innerHTML = html;
}

function handleRefineryMenuChange(event) {
  const input = event.target.closest("input[data-refinery-key]");
  if (!input) return;
  const key = input.dataset.refineryKey;
  if (input.checked) state.selectedRefineryGroups.add(key);
  else state.selectedRefineryGroups.delete(key);
  state.refineryEnabled = refinerySelectedCount() > 0;
  buildRefineryMenu();
  renderRefineryLayer();
  updateRefineryToggleUI();
}

function handleRefineryMenuClick(event) {
  const action = event.target.closest("[data-refinery-action]")?.dataset.refineryAction;
  if (!action) return;
  if (action === "all") {
    for (const item of refineryGroupItems()) state.selectedRefineryGroups.add(item.key);
  } else if (action === "none") {
    state.selectedRefineryGroups.clear();
  } else if (action === "defaults") {
    state.selectedRefineryGroups = new Set(DEFAULT_REFINERY_GROUP_KEYS);
  }
  state.refineryEnabled = refinerySelectedCount() > 0;
  buildRefineryMenu();
  renderRefineryLayer();
  updateRefineryToggleUI();
}

function renderRefineryLayer() {
  if (!state.map || !window.L) return;
  if (state.refineryLayer) {
    state.map.removeLayer(state.refineryLayer);
    state.refineryLayer = null;
  }
  const features = refineryVisibleFeatures();
  if (!state.refineryEnabled || !features.length) return;

  state.refineryLayer = L.geoJSON({ type: "FeatureCollection", features }, {
    pointToLayer(feature, latlng) {
      const radius = refineryMarkerRadius(feature.properties);
      return L.circleMarker(latlng, {
        radius,
        color: "#4a1f13",
        weight: 1.8,
        fillColor: "#b4532a",
        fillOpacity: 0.76,
        opacity: 0.96,
      });
    },
    onEachFeature(feature, layer) {
      layer.bindTooltip(refineryTooltipDetailedHtml(feature.properties), {
        sticky: true,
        opacity: 0.97,
        className: "refinery-tip",
      });
      layer.bindPopup(refineryPopupHtml(feature.properties), {
        className: "refinery-popup",
        maxWidth: 620,
      });
    },
  }).addTo(state.map);
}

function toggleRefineries() {
  state.refineryEnabled = refinerySelectedCount() > 0;
  setRefineryMenuOpen(!state.refineryMenuOpen);
  renderRefineryLayer();
  updateRefineryToggleUI();
}

function updateRefineryToggleUI() {
  const btn = els.refineryToggle;
  if (!btn) return;
  const groupCount = refinerySelectedCount();
  const featureCount = refineryVisibleFeatures().length;
  if (state.refineryEnabled && groupCount) {
    btn.textContent = `Refineries (${groupCount})`;
    btn.title = `${featureCount.toLocaleString("en-CA")} refinery and upgrader plants selected`;
    btn.className = "refinery-toggle-btn active";
    btn.setAttribute("aria-expanded", state.refineryMenuOpen ? "true" : "false");
  } else {
    btn.textContent = "Refineries";
    btn.title = "Refinery and upgrader plants with unit-level capacity rows";
    btn.className = "refinery-toggle-btn";
    btn.setAttribute("aria-expanded", state.refineryMenuOpen ? "true" : "false");
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

// BC Wildfire Service — BCWS_ActiveFires_PublicView, all fires except status 'Out'.
// Status values: 'Out of Control', 'Being Held', 'Under Control', 'Fire of Note', 'New'.
// Geometry is proper WGS84 — no coordinate normalization needed.
const BC_FIRES_URL =
  "https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/BCWS_ActiveFires_PublicView/FeatureServer/0/query" +
  "?where=FIRE_STATUS%20%3C%3E%20%27Out%27" +
  "&outFields=FIRE_NUMBER%2CINCIDENT_NAME%2CFIRE_STATUS%2CCURRENT_SIZE%2CLATITUDE%2CLONGITUDE%2CIGNITION_DATE%2CGEOGRAPHIC_DESCRIPTION%2CFIRE_OF_NOTE_IND%2CRESPONSE_TYPE_DESC" +
  "&returnGeometry=true" +
  "&f=geojson";

// Official Alberta Wildfire active fire inventory — Alberta Government ArcGIS (Eb8P5h4CJk8utIBz).
// This is the authoritative source powering the Alberta Wildfire Status Dashboard experience.
// Fields: LABEL (e.g. "LWF-041-2026"), FIRE_STATUS (full English strings), AREA_ESTIMATE (ha),
//   RESP_AREA (forest area name), GENERAL_CAUSE, RESPONSE_TYPE, CO_FLAG ("Y" = carryover fire).
const ALBERTA_FIRES_URL =
  "https://services.arcgis.com/Eb8P5h4CJk8utIBz/arcgis/rest/services/Active_Wildfires_(PROD)/FeatureServer/0/query" +
  "?where=1%3D1" +
  "&outFields=LABEL%2CFIRE_NUMBER%2CLATITUDE%2CLONGITUDE%2CFIRE_YEAR%2CFIRE_TYPE%2CFIRE_STATUS%2CFIRE_STATUS_DATE%2CAREA_ESTIMATE%2CSIZE_CLASS%2CRESP_AREA%2CGENERAL_CAUSE%2CRESPONSE_TYPE%2CASSESSMENT_ASSISTANCE_DATE%2CCO_FLAG" +
  "&returnGeometry=true" +
  "&f=geojson";

// Purely municipal fires (RMR, etc.) — reported by municipalities with no provincial mutual aid yet.
// Completely different schema: DDM coordinates, FireIncidentStatus, Hectares, LocalGovernment.
// Normalized to the common LABEL/FIRE_STATUS/AREA_ESTIMATE schema before merging.
const ALBERTA_MUNICIPAL_URL =
  "https://services.arcgis.com/Eb8P5h4CJk8utIBz/arcgis/rest/services/Active_Municipal_Wildfire_Prod/FeatureServer/4/query" +
  "?where=FireIncidentStatus%20%3C%3E%20%27Inactive%27" +
  "&outFields=MRFireNumber%2CFireIncidentStatus%2CHectares%2CEstimatedStartDate%2CLatitudeDDM%2CLongitudeDDM%2CLocalGovernment%2CMutualAidContactZone" +
  "&returnGeometry=false" +
  "&f=geojson";

// Mutual Aid fires — provincial assistance to municipal/county fires (RCU, CCU, WCU, etc.).
// Same schema as Active_Wildfires_(PROD). Status "Assistance Started" = actively assisted;
// "Assistance Ended" = province has stood down (excluded from map).
const ALBERTA_MUTUAL_AID_URL =
  "https://services.arcgis.com/Eb8P5h4CJk8utIBz/arcgis/rest/services/Active_Mutual_Aid_Wildfires/FeatureServer/0/query" +
  "?where=FIRE_STATUS%20%3C%3E%20%27Assistance%20Ended%27" +
  "&outFields=LABEL%2CFIRE_NUMBER%2CLATITUDE%2CLONGITUDE%2CFIRE_YEAR%2CFIRE_TYPE%2CFIRE_STATUS%2CFIRE_STATUS_DATE%2CAREA_ESTIMATE%2CSIZE_CLASS%2CRESP_AREA%2CGENERAL_CAUSE%2CRESPONSE_TYPE%2CASSESSMENT_ASSISTANCE_DATE%2CCO_FLAG" +
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

// Parses Degrees Decimal Minutes strings used by the municipal fire service.
// e.g. "53° 18.5410" → 53.309017,  "-112° 56.7841" → -113.046402
function parseDDM(str) {
  if (!str) return NaN;
  const m = String(str).match(/^(-?\d+)[°\s]+(\d+\.?\d*)$/);
  if (!m) return NaN;
  const deg = Number(m[1]);
  const min = Number(m[2]);
  return deg < 0 ? deg - min / 60 : deg + min / 60;
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

function activeFireFeatures(visibleOnly = false) {
  const cwfis = visibleOnly && !legendVisible("fire-zone")
    ? []
    : (state.wildfires?.features || []);
  const alberta = (state.albertaFires?.features || [])
    .filter((feature) => !visibleOnly || legendVisible(albertaFireLegendKey(feature)));
  const bc = (state.bcFires?.features || [])
    .filter((feature) => !visibleOnly || legendVisible(bcFireLegendKey(feature)));
  return [...cwfis, ...alberta, ...bc];
}

function geometryRings(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return geometry.coordinates || [];
  if (geometry.type === "MultiPolygon") return (geometry.coordinates || []).flat();
  return [];
}

function pointInRing(lat, lon, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1];
    const xj = ring[j][0], yj = ring[j][1];
    const intersects = ((yi > lat) !== (yj > lat)) &&
      (lon < ((xj - xi) * (lat - yi)) / ((yj - yi) || 1e-12) + xi);
    if (intersects) inside = !inside;
  }
  return inside;
}

function geometryContainsPoint(feature, lat, lon) {
  const rings = geometryRings(feature?.geometry);
  if (!rings.length) return false;
  // Treat any ring hit as exposed. This is intentionally conservative for
  // wildfire screening; exact polygon-with-holes handling belongs in ETL/GIS.
  return rings.some((ring) => pointInRing(lat, lon, ring));
}

function walkCoordinates(coords, visit) {
  if (!Array.isArray(coords)) return;
  if (typeof coords[0] === "number" && typeof coords[1] === "number") {
    visit(coords[1], coords[0]);
    return;
  }
  coords.forEach((item) => walkCoordinates(item, visit));
}

function distanceToGeometryKm(feature, lat, lon) {
  if (!feature?.geometry) return Infinity;
  if (geometryContainsPoint(feature, lat, lon)) return 0;
  let best = Infinity;
  walkCoordinates(feature.geometry.coordinates, (vLat, vLon) => {
    const dist = haversineKm(lat, lon, vLat, vLon);
    if (dist < best) best = dist;
  });
  return best;
}

function getFireRisk(assetLat, assetLon) {
  let minDist = Infinity;
  let nearestFire = null;

  for (const feature of activeFireFeatures(true)) {
    const c = geojsonCentroid(feature);
    if (!c) continue;
    const dist = haversineKm(assetLat, assetLon, c.lat, c.lon);
    if (dist < minDist) { minDist = dist; nearestFire = feature; }
  }

  if (!Number.isFinite(minDist) || minDist === Infinity) return { level: "none", distanceKm: Infinity, nearestFire: null };
  const level = minDist < 75 ? "high" : minDist < 200 ? "moderate" : "none";
  return { level, distanceKm: Math.round(minDist), nearestFire };
}

function getAssetFireRisk(asset) {
  if (!asset || asset.latitude == null || asset.longitude == null) {
    return { level: "none", distanceKm: Infinity, nearestFire: null };
  }
  let best = getFireRisk(asset.latitude, asset.longitude);
  const footprints = state.assetGeometryById.get(asset.asset_id) || [];
  if (!footprints.length) return best;

  for (const fire of activeFireFeatures(true)) {
    const c = geojsonCentroid(fire);
    if (!c) continue;
    for (const footprint of footprints) {
      const dist = distanceToGeometryKm(footprint, c.lat, c.lon);
      if (dist < best.distanceKm) {
        const level = dist < 75 ? "high" : dist < 200 ? "moderate" : "none";
        best = { level, distanceKm: Math.round(dist), nearestFire: fire };
      }
    }
  }
  return best;
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
    refreshFireLayers();
  }
}

// ============================================================
// ALBERTA PROVINCIAL ACTIVE WILDFIRES  — Official Alberta Government ArcGIS
// Loaded automatically on boot and refreshed alongside CWFIS.
// FIRE_STATUS uses full English strings (same convention as BC):
//   "Out of Control", "Being Held", "Under Control"
// CO_FLAG = "Y" means carry-over fire from a prior season.
// ============================================================

const ALBERTA_STAGE_STYLE = {
  "Out of Control":      { color: "#7f1d1d", fill: "#ef4444", weight: 2.5, opacity: 0.95, label: "Out of Control"     },
  "Being Held":          { color: "#7c2d12", fill: "#f97316", weight: 2,   opacity: 0.90, label: "Being Held"         },
  "Under Control":       { color: "#78350f", fill: "#fbbf24", weight: 2,   opacity: 0.85, label: "Under Control"      },
  "Carryover":           { color: "#475569", fill: "#94a3b8", weight: 2.2, opacity: 0.88, label: "Carryover"          },
  "Assistance Started":  { color: "#4c1d95", fill: "#7c3aed", weight: 2,   opacity: 0.90, label: "Mutual Aid — Active"   },
  "Active":              { color: "#92400e", fill: "#d97706", weight: 2,   opacity: 0.90, label: "Municipal Fire — Active" },
  default:               { color: "#1e293b", fill: "#94a3b8", weight: 1.5, opacity: 0.75, label: "Unknown"              },
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

const FIRE_MENU_ITEMS = [
  { section: "FWI / Satellite" },
  { key: "fire-zone", label: "NRCan CWFIS hotspots", color: "#ef4444", type: "dot" },
  { section: "Alberta Official" },
  { key: "ab-fire-oc", label: "Out of Control", color: ALBERTA_STAGE_STYLE["Out of Control"].fill, type: "dot" },
  { key: "ab-fire-bh", label: "Being Held", color: ALBERTA_STAGE_STYLE["Being Held"].fill, type: "dot" },
  { key: "ab-fire-uc", label: "Under Control", color: ALBERTA_STAGE_STYLE["Under Control"].fill, type: "dot" },
  { key: "ab-fire-carryover", label: "Carryover", color: ALBERTA_STAGE_STYLE.Carryover.fill, type: "dot" },
  { key: "ab-fire-ma", label: "Mutual Aid", color: ALBERTA_STAGE_STYLE["Assistance Started"].fill, type: "dot" },
  { key: "ab-fire-mun", label: "Municipal", color: ALBERTA_STAGE_STYLE.Active.fill, type: "dot" },
  { section: "BC Official" },
  { key: "bc-fire-oc", label: "Out of Control", color: BC_STATUS_STYLE["Out of Control"].fill, type: "dot" },
  { key: "bc-fire-bh", label: "Being Held", color: BC_STATUS_STYLE["Being Held"].fill, type: "dot" },
  { key: "bc-fire-uc", label: "Under Control", color: BC_STATUS_STYLE["Under Control"].fill, type: "dot" },
  { key: "bc-fire-fon", label: "Fire of Note", color: BC_STATUS_STYLE["Fire of Note"].fill, type: "dot" },
];

const FIRE_DEFAULT_KEYS = new Set([
  "ab-fire-oc",
  "ab-fire-bh",
  "ab-fire-uc",
  "ab-fire-carryover",
  "ab-fire-ma",
  "ab-fire-mun",
  "bc-fire-oc",
  "bc-fire-bh",
  "bc-fire-uc",
  "bc-fire-fon",
]);

function fireFilterItems() {
  return FIRE_MENU_ITEMS.filter((item) => !item.section);
}

function fireSelectedCount() {
  return fireFilterItems().filter((item) => !state.hiddenLegendKeys.has(item.key)).length;
}

function setFireMenuOpen(open) {
  state.fireMenuOpen = open;
  const menu = document.getElementById("fireMenu");
  if (menu) menu.hidden = !open;
  updateFireToggleUI();
}

function fireLegendCounts() {
  const counts = {};
  if (state.wildfires?.features?.length) {
    counts["fire-zone"] = state.wildfires.features.length;
  }
  for (const feature of state.albertaFires?.features || []) {
    const key = albertaFireLegendKey(feature);
    counts[key] = (counts[key] || 0) + 1;
  }
  for (const feature of state.bcFires?.features || []) {
    const key = bcFireLegendKey(feature);
    counts[key] = (counts[key] || 0) + 1;
  }
  return counts;
}

function buildFireMenu() {
  const options = document.getElementById("fireOptions");
  if (!options) return;
  const counts = fireLegendCounts();
  let currentSection = "";
  let html = "";
  for (const item of FIRE_MENU_ITEMS) {
    if (item.section) {
      currentSection = item.section;
      html += `<div class="fire-menu-section">${escapeHtml(item.section)}</div>`;
      continue;
    }
    const checked = !state.hiddenLegendKeys.has(item.key);
    const count = counts[item.key] ? counts[item.key].toLocaleString("en-CA") : "";
    html += `
      <label class="fire-option" title="${escapeHtml(currentSection)}">
        <input type="checkbox" data-fire-key="${escapeHtml(item.key)}" ${checked ? "checked" : ""} />
        <span class="fire-dot-swatch" style="background:${item.color}"></span>
        <span class="fire-option-text">
          <strong>${escapeHtml(item.label)}</strong>
          <em>${count ? `${count} fires` : currentSection}</em>
        </span>
      </label>`;
  }
  options.innerHTML = html;
}

function selectedFireKeys() {
  return new Set(fireFilterItems()
    .filter((item) => !state.hiddenLegendKeys.has(item.key))
    .map((item) => item.key));
}

function ensureSelectedFireSources() {
  const keys = selectedFireKeys();
  let started = false;
  const wantsCwfis = keys.has("fire-zone");
  const wantsAlberta = [...keys].some((key) => key.startsWith("ab-fire-"));
  const wantsBC = [...keys].some((key) => key.startsWith("bc-fire-"));

  if (wantsCwfis && !state.wildfires && !state.wildfireLoading) {
    fetchWildfires();
    started = true;
  }
  if (wantsAlberta && !state.albertaFires && !state.albertaFireLoading) {
    fetchAlbertaFires();
    started = true;
  }
  if (wantsBC && !state.bcFires && !state.bcFireLoading) {
    fetchBCFires();
    started = true;
  }
  return started;
}

function handleFireMenuChange(event) {
  const input = event.target.closest("input[data-fire-key]");
  if (!input) return;
  const key = input.dataset.fireKey;
  if (input.checked) state.hiddenLegendKeys.delete(key);
  else state.hiddenLegendKeys.add(key);
  state.wildfireEnabled = fireSelectedCount() > 0;
  ensureSelectedFireSources();
  refreshFireLayers();
  updateFireToggleUI();
}

function handleFireMenuClick(event) {
  const action = event.target.closest("[data-fire-action]")?.dataset.fireAction;
  if (!action) return;
  for (const item of fireFilterItems()) {
    if (action === "all") {
      state.hiddenLegendKeys.delete(item.key);
    } else if (action === "none") {
      state.hiddenLegendKeys.add(item.key);
    } else if (action === "defaults") {
      if (FIRE_DEFAULT_KEYS.has(item.key)) state.hiddenLegendKeys.delete(item.key);
      else state.hiddenLegendKeys.add(item.key);
    }
  }
  state.wildfireEnabled = fireSelectedCount() > 0;
  ensureSelectedFireSources();
  buildFireMenu();
  refreshFireLayers();
  updateFireToggleUI();
}

function refreshFireLayers() {
  if (!state.wildfireEnabled) {
    clearFireLayers();
  } else {
    renderFireLayer();
  }
  buildFireMenu();
  updateWildfireStatus(buildFireStatusMsg());
  refreshFireDependentPanels();
}

function refreshFireDependentPanels() {
  const aggregated = aggregateForDate();
  renderMetrics(aggregated);
  renderDetails(aggregated);
}

async function fetchAlbertaFires() {
  if (state.albertaFireLoading) return;
  state.albertaFireLoading = true;
  state.albertaFireError = null;
  try {
    // Fetch provincial, mutual aid, and municipal fires in parallel
    const [provResp, maResp, munResp] = await Promise.all([
      fetch(ALBERTA_FIRES_URL,       { mode: "cors" }),
      fetch(ALBERTA_MUTUAL_AID_URL,  { mode: "cors" }),
      fetch(ALBERTA_MUNICIPAL_URL,   { mode: "cors" }),
    ]);
    if (!provResp.ok) throw new Error(`HTTP ${provResp.status} (provincial)`);
    if (!maResp.ok)   throw new Error(`HTTP ${maResp.status} (mutual aid)`);
    // Municipal endpoint failure is non-fatal — log and continue
    const [provRaw, maRaw] = await Promise.all([provResp.json(), maResp.json()]);
    const munRaw = munResp.ok ? await munResp.json() : { features: [] };

    // Normalize provincial + mutual aid: use LATITUDE/LONGITUDE props over geometry
    // (geometry may be in a projected CRS on some ArcGIS exports).
    const normalize = f => {
      const p = f.properties || {};
      const lat = Number(p.LATITUDE);
      const lon = Number(p.LONGITUDE);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
      return { ...f, geometry: { type: "Point", coordinates: [lon, lat] } };
    };

    // Normalize municipal fires: different schema + DDM coordinates → common format
    const normalizeMunicipal = f => {
      const p = f.properties || {};
      const lat = parseDDM(p.LatitudeDDM);
      const lon = parseDDM(p.LongitudeDDM);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
      const startMs = Number(p.EstimatedStartDate);
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [lon, lat] },
        properties: {
          LABEL:                      p.MRFireNumber || "Municipal Fire",
          FIRE_TYPE:                  "Municipal",
          FIRE_STATUS:                p.FireIncidentStatus || "Active",
          AREA_ESTIMATE:              Number(p.Hectares) || 0,
          SIZE_CLASS:                 null,
          RESP_AREA:                  p.LocalGovernment || null,
          GENERAL_CAUSE:              null,
          RESPONSE_TYPE:              p.MutualAidContactZone || null,
          ASSESSMENT_ASSISTANCE_DATE: Number.isFinite(startMs) ? startMs : null,
          FIRE_YEAR:                  startMs > 0 ? new Date(startMs).getFullYear() : new Date().getFullYear(),
          CO_FLAG:                    "N",
        },
      };
    };

    const features = [
      ...(provRaw.features || []).map(normalize),
      ...(maRaw.features   || []).map(normalize),
      ...(munRaw.features  || []).map(normalizeMunicipal),
    ].filter(Boolean);

    state.albertaFires = { type: "FeatureCollection", features };
  } catch (err) {
    state.albertaFireError = `Alberta fire data unavailable (${err.message}).`;
    state.albertaFires = null;
  } finally {
    state.albertaFireLoading = false;
    updateFireToggleUI();
    refreshFireLayers();
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
    filter(feature) {
      return legendVisible(albertaFireLegendKey(feature));
    },
    pointToLayer(feature, latlng) {
      const p = feature.properties || {};
      const status = p.FIRE_STATUS || "";
      const isCarryover = p.CO_FLAG === "Y";
      const style = isCarryover
        ? ALBERTA_STAGE_STYLE.Carryover
        : (ALBERTA_STAGE_STYLE[status] || ALBERTA_STAGE_STYLE.default);
      const ha = Number(p.AREA_ESTIMATE);
      const r = Number.isFinite(ha) && ha > 0
        ? Math.min(22, 8 + Math.log10(ha + 1) * 4)
        : 8;
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
      const label = p.LABEL || "Unnamed Alberta fire";
      const ha = Number(p.AREA_ESTIMATE);
      const haStr = Number.isFinite(ha) && ha > 0 ? `${ha.toLocaleString("en-CA")} ha` : "size unknown";
      const sizeClass = p.SIZE_CLASS ? ` (Class ${escapeHtml(p.SIZE_CLASS)})` : "";
      const startMs = Number(p.ASSESSMENT_ASSISTANCE_DATE);
      const startDate = Number.isFinite(startMs) && startMs > 0 ? new Date(startMs) : null;
      const startStr = startDate ? startDate.toLocaleDateString("en-CA") : "—";
      const fireYear = Number(p.FIRE_YEAR) || currentYear;
      const isCarryover = p.CO_FLAG === "Y";
      const status = p.FIRE_STATUS || "";
      const stageStyle = isCarryover
        ? ALBERTA_STAGE_STYLE.Carryover
        : (ALBERTA_STAGE_STYLE[status] || ALBERTA_STAGE_STYLE.default);
      const carryoverNote = isCarryover
        ? `<span style="color:#b45309">⚠️ Carryover — fire from ${fireYear}</span><br>`
        : `<span style="color:#166534">🔥 New fire (${fireYear})</span><br>`;
      const isMutualAid  = p.FIRE_TYPE === "Mutual Aid";
      const isMunicipal  = p.FIRE_TYPE === "Municipal";
      const maBadge  = isMutualAid ? `<span style="color:#7c3aed;font-weight:700">🤝 Mutual Aid Fire</span><br>`   : "";
      const munBadge = isMunicipal  ? `<span style="color:#d97706;font-weight:700">🏘️ Municipal Fire</span><br>`    : "";
      const respArea  = p.RESP_AREA      ? `📍 ${escapeHtml(p.RESP_AREA)}<br>`            : "";
      const cause     = p.GENERAL_CAUSE  ? `Cause: ${escapeHtml(p.GENERAL_CAUSE)}<br>`    : "";
      const respType  = p.RESPONSE_TYPE  ? `Response: ${escapeHtml(p.RESPONSE_TYPE)}<br>` : "";
      layer.bindTooltip(
        `<strong>${escapeHtml(label)}</strong><br>` +
        maBadge +
        munBadge +
        carryoverNote +
        respArea +
        `Status: ${escapeHtml(stageStyle.label)}<br>` +
        `Size: ${haStr}${sizeClass}<br>` +
        cause +
        respType +
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
    updateFireToggleUI();
    refreshFireLayers();
  }
}

function renderBCFireLayer() {
  if (!state.map || !window.L) return;
  if (state.bcFireLayer) { state.map.removeLayer(state.bcFireLayer); state.bcFireLayer = null; }
  if (!state.wildfireEnabled || !state.bcFires?.features?.length) return;

  const currentYear = new Date().getFullYear();

  state.bcFireLayer = L.geoJSON(state.bcFires, {
    filter(feature) {
      return legendVisible(bcFireLegendKey(feature));
    },
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
  const cwfisCount = legendVisible("fire-zone") ? (state.wildfires?.features?.length ?? 0) : 0;
  if (state.wildfireError && !cwfisCount) {
    parts.push(`NRCan CWFIS: ${state.wildfireError}`);
  } else if (cwfisCount > 0) {
    const sev = summarizeFireSeverity(state.wildfires.features);
    parts.push(`${cwfisCount} NRCan hotspot${cwfisCount !== 1 ? "s" : ""}${sev ? ` (${sev})` : ""}`);
  }

  // Alberta official fires (provincial + mutual aid combined)
  const abFeatures   = (state.albertaFires?.features ?? [])
    .filter((feature) => legendVisible(albertaFireLegendKey(feature)));
  const abCount      = abFeatures.filter(f => !["Mutual Aid","Municipal"].includes(f.properties?.FIRE_TYPE)).length;
  const maCount      = abFeatures.filter(f => f.properties?.FIRE_TYPE === "Mutual Aid").length;
  const munCount     = abFeatures.filter(f => f.properties?.FIRE_TYPE === "Municipal").length;
  if (state.albertaFireError && !abFeatures.length) {
    parts.push(`AB: ${state.albertaFireError}`);
  } else if (abFeatures.length > 0) {
    const ooc = abFeatures.filter(f => f.properties?.FIRE_STATUS === "Out of Control").length;
    const bh  = abFeatures.filter(f => f.properties?.FIRE_STATUS === "Being Held").length;
    const stageSummary = [
      ooc    > 0 ? `${ooc} OC`     : "",
      bh     > 0 ? `${bh} BH`      : "",
      maCount  > 0 ? `${maCount} MA`  : "",
      munCount > 0 ? `${munCount} MUN` : "",
    ].filter(Boolean).join(", ");
    const total = abCount + maCount + munCount;
    parts.push(`${total} AB fire${total !== 1 ? "s" : ""}${stageSummary ? ` (${stageSummary})` : ""}`);
  }

  // BC official fires
  const bcFeatures = (state.bcFires?.features ?? [])
    .filter((feature) => legendVisible(bcFireLegendKey(feature)));
  const bcCount = bcFeatures.length;
  if (state.bcFireError && !bcCount) {
    parts.push(`BC: ${state.bcFireError}`);
  } else if (bcCount > 0) {
    const ooc = bcFeatures.filter(f => f.properties?.FIRE_STATUS === "Out of Control").length;
    const fon = bcFeatures.filter(f => f.properties?.FIRE_OF_NOTE_IND === "Y").length;
    const stageSummary = [ooc > 0 ? `${ooc} OC` : "", fon > 0 ? `${fon} FON` : ""].filter(Boolean).join(", ");
    parts.push(`${bcCount} BC fire${bcCount !== 1 ? "s" : ""}${stageSummary ? ` (${stageSummary})` : ""}`);
  }

  return parts.join(" · ");
}

function toggleWildfires() {
  state.wildfireEnabled = fireSelectedCount() > 0;
  setFireMenuOpen(!state.fireMenuOpen);
  if (state.wildfireEnabled) {
    ensureSelectedFireSources();
    refreshFireLayers();
  } else {
    clearFireLayers();
    updateWildfireStatus("");
    refreshFireDependentPanels();
  }
  updateFireToggleUI();
}

function clearFireLayers() {
  if (state.fireLayer        && state.map) { state.map.removeLayer(state.fireLayer);        state.fireLayer        = null; }
  if (state.albertaFireLayer && state.map) { state.map.removeLayer(state.albertaFireLayer); state.albertaFireLayer = null; }
  if (state.bcFireLayer      && state.map) { state.map.removeLayer(state.bcFireLayer);      state.bcFireLayer      = null; }
  if (state.riskBufferLayer  && state.map) { state.map.removeLayer(state.riskBufferLayer);  state.riskBufferLayer  = null; }
}

function updateFireToggleUI() {
  const btn = els.wildfireToggle;
  if (!btn) return;
  const selectedCount = fireSelectedCount();
  const loading = state.wildfireLoading || state.albertaFireLoading || state.bcFireLoading;
  if (loading) {
    btn.textContent = "Loading fires...";
    btn.className = "fire-toggle-btn loading";
    btn.setAttribute("aria-expanded", state.fireMenuOpen ? "true" : "false");
  } else if (state.wildfireEnabled && selectedCount) {
    btn.textContent = `Fires (${selectedCount})`;
    btn.title = `${selectedCount.toLocaleString("en-CA")} fire source categories selected`;
    btn.className = "fire-toggle-btn active";
    btn.setAttribute("aria-expanded", state.fireMenuOpen ? "true" : "false");
  } else {
    btn.textContent = "Fires";
    btn.title = "Official Alberta and BC fires plus optional NRCan CWFIS hotspots";
    btn.className = "fire-toggle-btn";
    btn.setAttribute("aria-expanded", state.fireMenuOpen ? "true" : "false");
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
  if (!state.wildfireEnabled || !activeFireFeatures(true).length) return;

  const group = L.layerGroup();
  for (const { asset, kbbl } of byAsset.values()) {
    if (asset.latitude == null || asset.longitude == null) continue;
    const risk = getAssetFireRisk(asset);
    if (risk.level === "none") continue;
    const isHigh = risk.level === "high";
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

  if (!state.wildfireEnabled || state.hiddenLegendKeys.has("fire-zone") || !state.wildfires?.features?.length) return;

  const SEVERITY_COLOR = { extreme: "#b91c1c", high: "#ef4444", moderate: "#f97316", low: "#f6ad55", unknown: "#64748b" };

  state.fireLayer = L.geoJSON(state.wildfires, {
    filter() {
      return legendVisible("fire-zone");
    },
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
        { opacity: 0.95, className: "fire-hotspot-tip" }
      );
    },
  }).addTo(state.map);
}

// ============================================================
// PIPELINE LAYER — AER Feeder Pipelines + Installations
// 32 550 operating feeder segments + 5 502 pipeline installations
// Data source: AER Pipeline Spatial Dataset (GCS NAD83 ≈ WGS84)
// ============================================================

const PIPELINE_SUBSTANCE_COLOR = {
  'Oil-Well Effluent':    '#a16207',
  'Crude Oil':            '#c2570a',
  'HVP Products':         '#7c3aed',
  'LVP Products':         '#0e7490',
  'Condensate':           '#1d4ed8',
  'Hydrocarbon Diluents': '#15803d',
};

const PIPELINE_SUBSTANCE_BADGE = {
  'Oil-Well Effluent':    'oilwell',
  'Crude Oil':            'crude',
  'HVP Products':         'hvp',
  'LVP Products':         'lvp',
  'Condensate':           'condensate',
  'Hydrocarbon Diluents': 'diluent',
};

const PIPELINE_LEGEND_KEY = {
  'Oil-Well Effluent':    'pipe-oilwell',
  'Crude Oil':            'pipe-crude',
  'HVP Products':         'pipe-hvp',
  'LVP Products':         'pipe-lvp',
  'Condensate':           'pipe-condensate',
  'Hydrocarbon Diluents': 'pipe-diluent',
};

const INSTALLATION_STYLE = {
  'Pump Station':         { color: '#0c4a6e', fill: '#0ea5e9', radius: 7 },
  'Compressor Station':   { color: '#431407', fill: '#fb923c', radius: 7 },
  'Oil Terminal':         { color: '#713f12', fill: '#f59e0b', radius: 8 },
  'Tank Farm':            { color: '#14532d', fill: '#22c55e', radius: 7 },
  'Meter Station':        { color: '#312e81', fill: '#a78bfa', radius: 4 },
  'Regulator Station':    { color: '#374151', fill: '#d1d5db', radius: 3 },
  'Meter Regulator Stn.': { color: '#312e81', fill: '#c4b5fd', radius: 4 },
  'Line Heater':          { color: '#4a044e', fill: '#e879f9', radius: 4 },
};

const INSTALLATION_LEGEND_KEY = {
  'Pump Station':         'inst-pump',
  'Compressor Station':   'inst-compressor',
  'Oil Terminal':         'inst-terminal',
  'Tank Farm':            'inst-terminal',
  'Meter Station':        'inst-meter',
  'Regulator Station':    'inst-meter',
  'Meter Regulator Stn.': 'inst-meter',
  'Line Heater':          'inst-meter',
};

// ============================================================
// MARKET ACCESS PIPELINES - Canadian export/import trunks
// ============================================================

function marketPipelineFeatures() {
  return (state.marketPipelineData?.features || [])
    .filter((feature) => feature.properties?.feature_kind === 'pipeline')
    .sort((a, b) => (a.properties?.display_order || 999) - (b.properties?.display_order || 999));
}

function marketHubSlug(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function tariffHubIdFromName(name) {
  const key = String(name || '').trim().toLowerCase();
  return state.marketTariffData?.hub_aliases?.[key] || marketHubSlug(name);
}

function marketHubId(feature) {
  const p = feature.properties || {};
  return p.hub_id || tariffHubIdFromName(p.name);
}

function marketHubFeatures() {
  const baseFeatures = (state.marketPipelineData?.features || [])
    .filter((feature) => feature.properties?.feature_kind === 'hub');
  const features = [...baseFeatures];
  const seenHubIds = new Set(baseFeatures.map(marketHubId));
  const tariffHubs = state.marketTariffData?.hubs || {};

  for (const [hubId, hub] of Object.entries(tariffHubs)) {
    if (seenHubIds.has(hubId) || !Array.isArray(hub.coordinates)) continue;
    seenHubIds.add(hubId);
    features.push({
      type: 'Feature',
      properties: {
        feature_kind: 'hub',
        hub_id: hubId,
        name: hub.name,
        hub_type: hub.hub_type,
        source_summary: 'Tariff document route-node reference and public geographic coordinates',
      },
      geometry: { type: 'Point', coordinates: hub.coordinates },
    });
  }

  return features;
}

function selectedMarketPipelineFeatures() {
  return marketPipelineFeatures()
    .filter((feature) => state.selectedMarketPipelineIds.has(feature.properties?.route_id));
}

function initializeMarketPipelineSelection() {
  if (state.selectedMarketPipelineIds.size || !state.marketPipelineData) return;
  for (const feature of marketPipelineFeatures()) {
    if (feature.properties?.default_visible !== false) {
      state.selectedMarketPipelineIds.add(feature.properties.route_id);
    }
  }
}

function marketPipelineStyle(feature) {
  return {
    color: feature.properties?.color || '#334155',
    weight: 1.55,
    opacity: 0.72,
    lineCap: 'round',
    lineJoin: 'round',
  };
}

async function fetchMarketPipelineData() {
  if (state.marketPipelineData) return true;
  if (state.marketPipelineLoading) return false;

  state.marketPipelineLoading = true;
  state.marketPipelineError = null;
  updateMarketPipelineToggleUI();
  updatePipelineStatus('Loading market access pipelines and current tariffs...');

  try {
    const [response, tariffResponse] = await Promise.all([
      fetch(DATA_PATHS.marketPipelines),
      fetch(DATA_PATHS.marketTariffs),
    ]);
    if (!response.ok) throw new Error(`Market pipelines: HTTP ${response.status}`);
    state.marketPipelineData = await response.json();
    if (!tariffResponse.ok) {
      state.marketTariffData = null;
      console.warn(`Market tariffs unavailable: HTTP ${tariffResponse.status}`);
    } else {
      state.marketTariffData = await tariffResponse.json();
    }
    initializeMarketPipelineSelection();
    buildMarketPipelineMenu();
  } catch (err) {
    state.marketPipelineError = err.message || String(err);
    updatePipelineStatus(`Market pipeline data unavailable: ${state.marketPipelineError}`);
    state.marketPipelineLoading = false;
    updateMarketPipelineToggleUI();
    return false;
  }

  state.marketPipelineLoading = false;
  updateMarketPipelineToggleUI();
  updatePipelineStatus('');
  return true;
}

function marketTariffRowsForHub(hubId) {
  const rows = state.marketTariffData?.tariffs || [];
  return rows
    .filter((row) => row.destination_hub_id === hubId || row.origin_hub_id === hubId)
    .sort((a, b) => {
      const directionA = a.destination_hub_id === hubId ? 0 : 1;
      const directionB = b.destination_hub_id === hubId ? 0 : 1;
      if (directionA !== directionB) return directionA - directionB;
      return [
        a.pipeline || '',
        a.destination || '',
        a.origin || '',
        a.service || '',
        a.product || '',
      ].join('|').localeCompare([
        b.pipeline || '',
        b.destination || '',
        b.origin || '',
        b.service || '',
        b.product || '',
      ].join('|'));
    });
}

function tariffMoney(value, currency, unit) {
  if (!Number.isFinite(value)) return '';
  const digits = unit === 'bbl' ? 4 : 4;
  return `${currency} ${formatNumber(value, digits)}/${unit}`;
}

function tariffSourceLink(label, url) {
  if (!url) return escapeHtml(label || '');
  return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label || 'Source')}</a>`;
}

function tariffCostItemText(item) {
  if (!item) return '';
  const unit = item.unit === 'bbl' ? 'bbl' : 'm3';
  const value = Number.isFinite(item.value) ? tariffMoney(item.value, item.currency, unit) : '';
  const bbl = item.unit === 'm3' && Number.isFinite(item.value_per_bbl)
    ? ` (${tariffMoney(item.value_per_bbl, item.currency, 'bbl')})`
    : '';
  const text = item.text ? ` - ${item.text}` : '';
  return `${item.name || 'Charge'}${value ? `: ${value}${bbl}` : ''}${text}`;
}

function renderTariffCostItems(title, items, className = '') {
  if (!Array.isArray(items) || !items.length) return '';
  const rows = items
    .map((item) => {
      const label = tariffCostItemText(item);
      const link = item.source_label && item.source_url
        ? ` ${tariffSourceLink(item.source_label, item.source_url)}`
        : '';
      return `<li>${escapeHtml(label)}${link}</li>`;
    })
    .join('');
  return `<div class="tariff-detail ${className}"><span>${escapeHtml(title)}</span><ul>${rows}</ul></div>`;
}

function renderTariffTextList(title, items) {
  if (!Array.isArray(items) || !items.length) return '';
  return `<div class="tariff-detail"><span>${escapeHtml(title)}</span><ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`;
}

function renderTariffCost(row) {
  const unit = row.unit === 'bbl' ? 'bbl' : 'm3';
  if (Number.isFinite(row.total)) {
    const total = tariffMoney(row.total, row.currency, unit);
    const bbl = unit === 'm3' && Number.isFinite(row.total_per_bbl)
      ? ` (${tariffMoney(row.total_per_bbl, row.currency, 'bbl')})`
      : '';
    const baseBefore = Number.isFinite(row.base_before_included_costs)
      ? `<span>Base before included costs ${tariffMoney(row.base_before_included_costs, row.currency, unit)}${unit === 'm3' && Number.isFinite(row.base_before_included_costs_per_bbl) ? ` (${tariffMoney(row.base_before_included_costs_per_bbl, row.currency, 'bbl')})` : ''}</span>`
      : '';
    const fixed = Number.isFinite(row.fixed)
      ? `<span>Fixed ${tariffMoney(row.fixed, row.currency, unit)}${unit === 'm3' && Number.isFinite(row.fixed_per_bbl) ? ` (${tariffMoney(row.fixed_per_bbl, row.currency, 'bbl')})` : ''}</span>`
      : '';
    const variable = Number.isFinite(row.variable)
      ? `<span>Variable ${tariffMoney(row.variable, row.currency, unit)}${unit === 'm3' && Number.isFinite(row.variable_per_bbl) ? ` (${tariffMoney(row.variable_per_bbl, row.currency, 'bbl')})` : ''}</span>`
      : '';
    const allIn = Number.isFinite(row.total_with_default_adders)
      ? `<div class="tariff-all-in"><span>All-in with default adders</span><strong>${escapeHtml(tariffMoney(row.total_with_default_adders, row.currency, unit))}${unit === 'm3' && Number.isFinite(row.total_with_default_adders_per_bbl) ? ` (${escapeHtml(tariffMoney(row.total_with_default_adders_per_bbl, row.currency, 'bbl'))})` : ''}</strong></div>`
      : '';
    return `<strong>${escapeHtml(total)}${escapeHtml(bbl)}</strong>${baseBefore || fixed || variable ? `<div class="tariff-components">${baseBefore}${fixed}${variable}</div>` : ''}${allIn}`;
  }

  if (Number.isFinite(row.cad_component_m3) || Number.isFinite(row.usd_component_m3)) {
    const cad = Number.isFinite(row.cad_component_m3)
      ? `CAD ${formatNumber(row.cad_component_m3, 4)}/m3 (${formatNumber(row.cad_component_per_bbl, 4)}/bbl)`
      : '';
    const usd = Number.isFinite(row.usd_component_m3)
      ? `USD ${formatNumber(row.usd_component_m3, 4)}/m3 (${formatNumber(row.usd_component_per_bbl, 4)}/bbl)`
      : '';
    return `<strong>${escapeHtml([cad, usd].filter(Boolean).join(' + '))}</strong>`;
  }

  return '<strong>Rate not published in loaded rows</strong>';
}

function renderTariffDetails(row) {
  const notes = row.notes ? `<div class="tariff-note">${escapeHtml(row.notes)}</div>` : '';
  const loss = Number.isFinite(row.loss_allowance_percent)
    ? `<div class="tariff-note">Loss allowance: ${escapeHtml(formatNumber(row.loss_allowance_percent, 4))}% where applicable.</div>`
    : '';
  return [
    renderTariffCostItems('Included in table rate', row.included_costs, 'included'),
    renderTariffCostItems('Additional charges / credits', row.additional_costs, 'additional'),
    renderTariffCostItems('Variable cost components', row.variable_components, 'variable-items'),
    renderTariffTextList('Other tariff conditions', row.conditional_charges),
    notes,
    loss,
  ].filter(Boolean).join('');
}

function renderMarketHubTooltip(p) {
  const name = p.name || 'Market hub';
  const hubId = p.hub_id || tariffHubIdFromName(name);
  const rows = marketTariffRowsForHub(hubId);
  const docs = new Set(rows.map((row) => row.document_id));
  const inbound = rows.filter((row) => row.destination_hub_id === hubId).length;
  const outbound = rows.length - inbound;

  let html =
    `<div class="hub-tip-head">` +
    `<strong>${escapeHtml(name)}</strong>` +
    `${p.hub_type ? `<div class="pt-sub">${escapeHtml(p.hub_type)}</div>` : ''}` +
    `</div>`;

  if (!rows.length) {
    return html + '<div class="pt-sub">No current crude tariff rows loaded for this hub.</div>';
  }

  html +=
    `<div class="tariff-summary">` +
    `<span>${formatNumber(rows.length, 0)} tariff rows</span>` +
    `<span>${formatNumber(inbound, 0)} inbound</span>` +
    `<span>${formatNumber(outbound, 0)} outbound</span>` +
    `<span>${formatNumber(docs.size, 0)} source docs</span>` +
    `</div>` +
    `<div class="tariff-list">`;

  for (const row of rows) {
    const direction = row.destination_hub_id === hubId ? 'Inbound' : 'Outbound';
    const status = row.status === 'pending-effective-forward-use' ? 'pending forward' : row.status;
    html +=
      `<div class="tariff-row">` +
      `<div class="tariff-row-title">` +
      `<strong>${escapeHtml(row.pipeline)}</strong>` +
      `<span>${escapeHtml(direction)}</span>` +
      `</div>` +
      `<div class="tariff-route">${escapeHtml(row.origin)} -> ${escapeHtml(row.destination)}</div>` +
      `<div class="tariff-product">${escapeHtml(row.product)} · ${escapeHtml(row.service)}</div>` +
      `<div class="tariff-cost">${renderTariffCost(row)}</div>` +
      renderTariffDetails(row) +
      `<div class="tariff-source">` +
      `<span>Effective ${escapeHtml(row.effective)} · ${escapeHtml(status)}</span>` +
      tariffSourceLink(row.source_label || `${row.document_page} - ${row.document_name}`, row.source_url) +
      `</div>` +
      `</div>`;
  }

  html += `</div>`;
  return html;
}

function renderMarketHubPopup(p) {
  return `<div class="market-hub-popup-inner">${renderMarketHubTooltip(p)}</div>`;
}

function renderMarketPipelineLayers() {
  if (!state.map || !window.L) return;
  if (state.marketPipelineLineLayer) {
    state.map.removeLayer(state.marketPipelineLineLayer);
    state.marketPipelineLineLayer = null;
  }
  if (state.marketHubLayer) {
    state.map.removeLayer(state.marketHubLayer);
    state.marketHubLayer = null;
  }
  if (!state.marketPipelineEnabled || !state.marketPipelineData?.features?.length) return;

  const lineFeatures = selectedMarketPipelineFeatures();
  if (!lineFeatures.length) return;

  state.marketPipelineLineLayer = L.geoJSON({ type: 'FeatureCollection', features: lineFeatures }, {
    style: marketPipelineStyle,
    onEachFeature(feature, layer) {
      const p = feature.properties || {};
      const source = p.source_summary || 'public GIS';
      const confidence = p.geometry_confidence || 'route-level linework';
      layer.bindTooltip(
        `<div>` +
        `<strong>${escapeHtml(p.route_name || 'Market access pipeline')}</strong>` +
        `<div class="pt-sub">${escapeHtml(p.operator || '')}${p.commodity ? ' · ' + escapeHtml(p.commodity) : ''}</div>` +
        `<div class="pt-sub">${escapeHtml(p.flow_role || '')}</div>` +
        `<div class="pt-route">` +
        `<span class="pt-route-label">Source</span><span class="pt-route-val">${escapeHtml(source)}</span>` +
        `<span class="pt-route-label">Direction</span><span class="pt-route-val">${escapeHtml(p.direction || '—')}</span>` +
        `</div>` +
        `<div class="pt-sub" style="margin-top:4px">${escapeHtml(source)} · ${escapeHtml(confidence)}</div>` +
        `</div>`,
        { sticky: true, opacity: 0.96, className: 'pipeline-tip' }
      );
    },
  }).addTo(state.map);

  if (state.marketHubsEnabled) {
    state.marketHubLayer = L.geoJSON(
      { type: 'FeatureCollection', features: marketHubFeatures() },
      {
        pointToLayer(feature, latlng) {
          return L.circleMarker(latlng, {
            radius: 4,
            color: '#111827',
            weight: 1.4,
            fillColor: '#facc15',
            fillOpacity: 0.92,
            opacity: 0.9,
          });
        },
        onEachFeature(feature, layer) {
          const p = feature.properties || {};
          layer.bindTooltip(
            renderMarketHubTooltip(p),
            { sticky: true, opacity: 0.96, className: 'pipeline-tip market-hub-tip', interactive: true }
          );
          layer.bindPopup(
            renderMarketHubPopup(p),
            {
              className: 'market-hub-popup',
              maxWidth: 760,
              autoPan: true,
              closeOnClick: false,
            }
          );
        },
      }
    ).addTo(state.map);
  }

  state.marketPipelineLineLayer.bringToBack();
  bringPipelineLayersToBack();
  if (state.formationLayer) state.formationLayer.bringToBack();
}

async function toggleMarketPipelines() {
  const ok = await fetchMarketPipelineData();
  if (!ok) return;
  state.marketPipelineEnabled = true;
  setMarketPipelineMenuOpen(!state.marketPipelineMenuOpen);
  renderMarketPipelineLayers();
  updateMarketPipelineToggleUI();
}

function updateMarketPipelineToggleUI() {
  const btn = document.getElementById('marketPipelineToggle');
  if (!btn) return;
  const selectedCount = state.selectedMarketPipelineIds.size;
  const totalCount = marketPipelineFeatures().length;
  if (state.marketPipelineLoading) {
    btn.textContent = 'Loading...';
    btn.className = 'market-pipeline-toggle-btn loading';
    btn.setAttribute('aria-expanded', 'false');
  } else if (state.marketPipelineEnabled && selectedCount) {
    btn.textContent = `Market Pipes (${selectedCount})`;
    btn.title = `${selectedCount.toLocaleString('en-CA')} of ${totalCount.toLocaleString('en-CA')} market-access routes selected`;
    btn.className = 'market-pipeline-toggle-btn active';
    btn.setAttribute('aria-expanded', state.marketPipelineMenuOpen ? 'true' : 'false');
  } else {
    btn.textContent = 'Market Pipes';
    btn.title = 'Major Canadian crude export/import and diluent market-access pipelines';
    btn.className = 'market-pipeline-toggle-btn';
    btn.setAttribute('aria-expanded', state.marketPipelineMenuOpen ? 'true' : 'false');
  }
}

function setMarketPipelineMenuOpen(open) {
  state.marketPipelineMenuOpen = open;
  const menu = document.getElementById('marketPipelineMenu');
  if (menu) menu.hidden = !open;
  updateMarketPipelineToggleUI();
}

function buildMarketPipelineMenu() {
  const options = document.getElementById('marketPipelineOptions');
  if (!options || !state.marketPipelineData) return;
  let html = '';
  let currentSection = '';
  for (const feature of marketPipelineFeatures()) {
    const p = feature.properties || {};
    const section = p.menu_section || 'Core Market Access Pipelines';
    if (section !== currentSection) {
      currentSection = section;
      html += `<div class="market-pipeline-menu-section">${escapeHtml(section)}</div>`;
    }
    const checked = state.selectedMarketPipelineIds.has(p.route_id);
    const color = p.color || '#334155';
    html += `
      <label class="market-pipeline-option" title="${escapeHtml(p.flow_role || p.route_name)}">
        <input type="checkbox" data-market-pipeline-id="${escapeHtml(p.route_id)}" ${checked ? 'checked' : ''} />
        <span class="market-pipeline-swatch" style="background:${color}"></span>
        <span class="market-pipeline-option-text">
          <strong>${escapeHtml(p.route_name || p.route_id)}</strong>
          <em>${escapeHtml(p.commodity || '')}</em>
        </span>
      </label>`;
  }
  options.innerHTML = html;
  const hubsToggle = document.getElementById('marketHubToggle');
  if (hubsToggle) hubsToggle.checked = state.marketHubsEnabled;
}

function handleMarketPipelineMenuChange(event) {
  const pipelineInput = event.target.closest('input[data-market-pipeline-id]');
  if (pipelineInput) {
    const id = pipelineInput.dataset.marketPipelineId;
    if (pipelineInput.checked) state.selectedMarketPipelineIds.add(id);
    else state.selectedMarketPipelineIds.delete(id);
    state.marketPipelineEnabled = state.selectedMarketPipelineIds.size > 0;
    refreshMarketPipelineLayers();
    updateMarketPipelineToggleUI();
    return;
  }

  if (event.target.id === 'marketHubToggle') {
    state.marketHubsEnabled = event.target.checked;
    refreshMarketPipelineLayers();
  }
}

function handleMarketPipelineMenuClick(event) {
  const action = event.target.closest('[data-market-action]')?.dataset.marketAction;
  if (!action) return;
  if (action === 'all') {
    for (const feature of marketPipelineFeatures()) {
      state.selectedMarketPipelineIds.add(feature.properties.route_id);
    }
  } else if (action === 'none') {
    state.selectedMarketPipelineIds.clear();
  } else if (action === 'defaults') {
    state.selectedMarketPipelineIds.clear();
    for (const feature of marketPipelineFeatures()) {
      if (feature.properties?.default_visible !== false) {
        state.selectedMarketPipelineIds.add(feature.properties.route_id);
      }
    }
  }
  state.marketPipelineEnabled = state.selectedMarketPipelineIds.size > 0;
  buildMarketPipelineMenu();
  refreshMarketPipelineLayers();
  updateMarketPipelineToggleUI();
}

function refreshMarketPipelineLayers() {
  renderMarketPipelineLayers();
}

// Extend app state for pipelines
Object.assign(state, {
  pipelineEnabled:      false,
  pipelineIndex:        null,
  pipelineIndexPromise: null,
  pipelineLoading:      false,
  pipelineError:        null,
  pipelineSegmentLayersByKey: null,
  pipelineInstallLayersByKey: null,
  pipelineLayerPromisesByKey: null,
  pipelineTileLayersByKey: null,
  pipelineTileRefreshPending: false,
  pipelineMenuOpen:     false,
});

const PIPELINE_TILE_MIN_MAP_ZOOM = 6;

function pipelineSubstanceWeight(diamMm) {
  const d = parseFloat(diamMm) || 0;
  if (d <= 0)   return 0.7;
  if (d <= 60)  return 0.8;
  if (d <= 114) return 1.15;
  if (d <= 219) return 1.55;
  return 2.1;
}

function pipelineSegmentStyle(feature) {
  const p   = feature.properties || {};
  const sub = p.substance || '';
  const col = PIPELINE_SUBSTANCE_COLOR[sub] || '#888888';
  const w   = pipelineSubstanceWeight(p.diameter_mm);
  return { color: col, weight: w, opacity: 0.62 };
}

function bindPipelineSegmentTooltip(feature, layer) {
  const p     = feature.properties || {};
  const sub   = p.substance || 'Unknown';
  const badge = PIPELINE_SUBSTANCE_BADGE[sub] || '';
  const from  = [p.from_fac, p.from_loc].filter(Boolean).join(' @ ') || '—';
  const to    = [p.to_fac,   p.to_loc  ].filter(Boolean).join(' @ ') || '—';
  const diam  = p.diameter_mm ? `${p.diameter_mm} mm OD` : '—';
  const maop  = p.maop_kpa ? `${Number(p.maop_kpa).toLocaleString('en-CA')} kPa MAOP` : '';
  const len   = p.length_km ? `${p.length_km} km` : '';
  const h2s   = p.h2s_pct && p.h2s_pct !== '0' ? `H₂S ${p.h2s_pct}%` : '';
  const env   = p.environ || '';
  const extras = [maop, len, h2s, env].filter(Boolean).join(' · ');

  layer.bindTooltip(
    `<div>` +
    `<strong><span class="pt-badge ${badge}">${escapeHtml(sub)}</span>${escapeHtml(p.company || '—')}</strong>` +
    `<div class="pt-sub">Licence ${escapeHtml(p.licence || '—')} · ${escapeHtml(p.field_ctr || '—')}</div>` +
    `<div class="pt-route">` +
    `<span class="pt-route-label">From</span><span class="pt-route-val">${escapeHtml(from)}</span>` +
    `<span class="pt-route-label">To</span><span class="pt-route-val">${escapeHtml(to)}</span>` +
    `</div>` +
    `<div class="pt-sub" style="margin-top:4px">${escapeHtml(diam)}${extras ? ' · ' + escapeHtml(extras) : ''}</div>` +
    `${p.material ? `<div class="pt-sub">${escapeHtml(p.material)}${p.joint ? ' · ' + escapeHtml(p.joint) : ''}</div>` : ''}` +
    `</div>`,
    { sticky: true, opacity: 0.96, className: 'pipeline-tip' }
  );
}

function bindPipelineInstallTooltip(feature, layer) {
  const p    = feature.properties || {};
  const type = p.type || 'Installation';
  const pwr  = p.power_kw ? `${parseFloat(p.power_kw).toLocaleString('en-CA')} kW` : '';
  const src  = p.prime_source || '';
  const h2s  = p.h2s_pct && p.h2s_pct !== '0' ? `H₂S ${p.h2s_pct}%` : '';
  const extras = [pwr && src ? `${pwr} (${src})` : (pwr || src), h2s].filter(Boolean).join(' · ');

  layer.bindTooltip(
    `<div>` +
    `<strong>${escapeHtml(type)}</strong>` +
    `<div class="pt-sub">${escapeHtml(p.company || '—')}</div>` +
    `<div class="pt-sub">Lic. ${escapeHtml(p.licence || '—')} · ${escapeHtml(p.location || '—')}</div>` +
    `${p.substance || p.field_ctr ? `<div class="pt-sub">${escapeHtml(p.substance || '')}${p.field_ctr ? ' · ' + escapeHtml(p.field_ctr) : ''}</div>` : ''}` +
    `${extras ? `<div class="pt-sub" style="margin-top:2px">${escapeHtml(extras)}</div>` : ''}` +
    `</div>`,
    { sticky: true, opacity: 0.96, className: 'inst-tip' }
  );
}

function setCachedLayerVisible(layer, visible) {
  if (!layer || !state.map) return;
  const shown = state.map.hasLayer(layer);
  if (visible && !shown) layer.addTo(state.map);
  if (!visible && shown) state.map.removeLayer(layer);
}

function bringPipelineLayersToBack() {
  if (!state.map) return;
  for (const layerMap of [state.pipelineSegmentLayersByKey, state.pipelineInstallLayersByKey]) {
    if (!layerMap) continue;
    for (const layer of layerMap.values()) {
      if (state.map.hasLayer(layer) && typeof layer.bringToBack === 'function') layer.bringToBack();
    }
  }
  for (const tileStore of state.pipelineTileLayersByKey?.values?.() || []) {
    for (const layer of tileStore.layers.values()) {
      if (state.map.hasLayer(layer) && typeof layer.bringToBack === 'function') layer.bringToBack();
    }
  }
  if (state.formationLayer) state.formationLayer.bringToBack();
}

async function togglePipelines() {
  const ok = await fetchPipelineData();
  if (!ok) return;
  state.pipelineEnabled = pipelineSelectedCount() > 0;
  setPipelineMenuOpen(!state.pipelineMenuOpen);
  refreshPipelineLayers();
  updatePipelineToggleUI();
}

function updatePipelineToggleUI() {
  const btn = document.getElementById('pipelineToggle');
  if (!btn) return;
  const selectedCount = pipelineSelectedCount();
  const totalCount = pipelineFilterItems().length;
  if (state.pipelineLoading) {
    btn.textContent = 'Loading…';
    btn.className   = 'pipeline-toggle-btn loading';
    btn.setAttribute('aria-expanded', 'false');
  } else if (state.pipelineEnabled && selectedCount) {
    btn.textContent = `Pipelines (${selectedCount})`;
    btn.title       = `${selectedCount.toLocaleString('en-CA')} of ${totalCount.toLocaleString('en-CA')} AER feeder categories selected`;
    btn.className   = 'pipeline-toggle-btn active';
    btn.setAttribute('aria-expanded', state.pipelineMenuOpen ? 'true' : 'false');
  } else {
    btn.textContent = 'Pipelines';
    btn.title       = 'AER feeder pipelines — crude, HVP/LVP, condensate, diluents, well effluent';
    btn.className   = 'pipeline-toggle-btn';
    btn.setAttribute('aria-expanded', state.pipelineMenuOpen ? 'true' : 'false');
  }
}

function updatePipelineStatus(msg) {
  const el = document.getElementById('pipelineStatus');
  if (!el) return;
  el.textContent = msg || '';
  el.hidden      = !msg;
}

// AER feeder pipeline category dropdown.

const PIPELINE_LEGEND_ITEMS = [
  // Lines section
  { section: 'Pipeline Lines' },
  { key: 'pipe-oilwell',    label: 'Oil-Well Effluent',     color: '#a16207', type: 'line' },
  { key: 'pipe-crude',      label: 'Crude Oil',              color: '#c2570a', type: 'line' },
  { key: 'pipe-hvp',        label: 'HVP Products',           color: '#7c3aed', type: 'line' },
  { key: 'pipe-lvp',        label: 'LVP Products',           color: '#0e7490', type: 'line' },
  { key: 'pipe-condensate', label: 'Condensate',             color: '#1d4ed8', type: 'line' },
  { key: 'pipe-diluent',    label: 'Hydrocarbon Diluents',   color: '#15803d', type: 'line' },
  // Installations section
  { section: 'Installations' },
  { key: 'inst-pump',       label: 'Pump Stations',          color: '#0ea5e9', type: 'dot' },
  { key: 'inst-compressor', label: 'Compressor Stations',    color: '#fb923c', type: 'dot' },
  { key: 'inst-terminal',   label: 'Oil Terminals / Tank Farms', color: '#f59e0b', type: 'dot' },
  { key: 'inst-meter',      label: 'Meter / Regulator Stns.', color: '#a78bfa', type: 'dot' },
];

const PIPELINE_CORE_KEYS = new Set([
  'pipe-oilwell',
  'pipe-crude',
  'pipe-lvp',
  'pipe-condensate',
]);

function pipelineFilterItems() {
  return PIPELINE_LEGEND_ITEMS.filter((item) => !item.section);
}

function pipelineSelectedCount() {
  return pipelineFilterItems().filter((item) => !state.hiddenLegendKeys.has(item.key)).length;
}

function setPipelineMenuOpen(open) {
  state.pipelineMenuOpen = open;
  const menu = document.getElementById('pipelineMenu');
  if (menu) menu.hidden = !open;
  updatePipelineToggleUI();
}

function buildPipelineMenu() {
  const options = document.getElementById('pipelineOptions');
  if (!options) return;
  const counts = pipelineLegendCounts();
  let currentSection = '';
  let html = '';
  for (const item of PIPELINE_LEGEND_ITEMS) {
    if (item.section) {
      currentSection = item.section;
      html += `<div class="pipeline-menu-section">${escapeHtml(item.section)}</div>`;
      continue;
    }
    const checked = !state.hiddenLegendKeys.has(item.key);
    const count = counts[item.key] ? counts[item.key].toLocaleString('en-CA') : '';
    const swatchClass = item.type === 'line' ? 'pipeline-swatch' : 'pipeline-dot-swatch';
    html += `
      <label class="pipeline-option" title="${escapeHtml(currentSection)}">
        <input type="checkbox" data-pipeline-key="${escapeHtml(item.key)}" ${checked ? 'checked' : ''} />
        <span class="${swatchClass}" style="background:${item.color}"></span>
        <span class="pipeline-option-text">
          <strong>${escapeHtml(item.label)}</strong>
          <em>${count ? `${count} features` : currentSection}</em>
        </span>
      </label>`;
  }
  options.innerHTML = html;
}

function handlePipelineMenuChange(event) {
  const input = event.target.closest('input[data-pipeline-key]');
  if (!input) return;
  const key = input.dataset.pipelineKey;
  if (input.checked) state.hiddenLegendKeys.delete(key);
  else state.hiddenLegendKeys.add(key);
  state.pipelineEnabled = pipelineSelectedCount() > 0;
  refreshPipelineLayers();
  updatePipelineToggleUI();
}

function handlePipelineMenuClick(event) {
  const action = event.target.closest('[data-pipeline-action]')?.dataset.pipelineAction;
  if (!action) return;
  for (const item of pipelineFilterItems()) {
    if (action === 'all') {
      state.hiddenLegendKeys.delete(item.key);
    } else if (action === 'none') {
      state.hiddenLegendKeys.add(item.key);
    } else if (action === 'core') {
      if (PIPELINE_CORE_KEYS.has(item.key)) state.hiddenLegendKeys.delete(item.key);
      else state.hiddenLegendKeys.add(item.key);
    }
  }
  state.pipelineEnabled = pipelineSelectedCount() > 0;
  buildPipelineMenu();
  refreshPipelineLayers();
  updatePipelineToggleUI();
}

// Fast path: load AER pipeline categories from pre-split GeoJSON files.
// The old monolithic 30 MB file remains available as a source artifact, but
// interactive toggles should only fetch/build the category the user selected.
async function fetchPipelineData() {
  if (state.pipelineIndex) return true;
  if (state.pipelineIndexPromise) return state.pipelineIndexPromise;

  state.pipelineIndexPromise = (async () => {
    state.pipelineLoading = true;
    state.pipelineError = null;
    updatePipelineToggleUI();
    updatePipelineStatus('Loading AER pipeline index...');

    try {
      const response = await fetch(DATA_PATHS.pipelineIndex);
      if (!response.ok) throw new Error(`Pipeline index: HTTP ${response.status}`);
      state.pipelineIndex = await response.json();
      state.pipelineSegmentLayersByKey = new Map();
      state.pipelineInstallLayersByKey = new Map();
      state.pipelineLayerPromisesByKey = new Map();
      state.pipelineTileLayersByKey = new Map();
      buildPipelineMenu();
      updatePipelineStatus('');
      return true;
    } catch (err) {
      state.pipelineError = err.message || String(err);
      updatePipelineStatus(`Pipeline data unavailable: ${state.pipelineError}`);
      return false;
    } finally {
      state.pipelineLoading = false;
      state.pipelineIndexPromise = null;
      updatePipelineToggleUI();
    }
  })();

  return state.pipelineIndexPromise;
}

function pipelineIndexEntry(key) {
  return state.pipelineIndex?.line_categories?.[key]
    || state.pipelineIndex?.installation_categories?.[key]
    || null;
}

function pipelineLayerStore(key) {
  if (key.startsWith('pipe-')) return state.pipelineSegmentLayersByKey;
  if (key.startsWith('inst-')) return state.pipelineInstallLayersByKey;
  return null;
}

function pipelineLayerOptions(key) {
  if (key.startsWith('pipe-')) {
    return {
      style: pipelineSegmentStyle,
      onEachFeature: bindPipelineSegmentTooltip,
    };
  }
  return {
    pointToLayer(feature, latlng) {
      const t = feature.properties?.type || '';
      const style = INSTALLATION_STYLE[t] || { color: '#374151', fill: '#94a3b8', radius: 4 };
      return L.circleMarker(latlng, {
        radius: style.radius,
        color: style.color,
        weight: 1.5,
        fillColor: style.fill,
        fillOpacity: 0.88,
        opacity: 0.9,
      });
    },
    onEachFeature: bindPipelineInstallTooltip,
  };
}

async function ensurePipelineCategoryLayer(key) {
  if (!state.map || !window.L || !state.pipelineIndex) return null;
  const entry = pipelineIndexEntry(key);
  if (pipelineUsesTiles(entry)) return null;
  const store = pipelineLayerStore(key);
  if (!store) return null;
  if (store.has(key)) return store.get(key);
  if (!state.pipelineLayerPromisesByKey) state.pipelineLayerPromisesByKey = new Map();
  if (state.pipelineLayerPromisesByKey.has(key)) return state.pipelineLayerPromisesByKey.get(key);

  if (!entry?.path) return null;
  const item = pipelineFilterItems().find((candidate) => candidate.key === key);
  updatePipelineStatus(`Loading ${item?.label || 'pipeline layer'}...`);

  const promise = fetch(entry.path)
    .then((response) => {
      if (!response.ok) throw new Error(`${key}: HTTP ${response.status}`);
      return response.json();
    })
    .then((geojson) => {
      const layer = L.geoJSON(geojson, pipelineLayerOptions(key));
      store.set(key, layer);
      updatePipelineStatus('');
      return layer;
    })
    .catch((err) => {
      state.pipelineLayerPromisesByKey.delete(key);
      state.pipelineError = err.message || String(err);
      updatePipelineStatus(`Pipeline data unavailable: ${state.pipelineError}`);
      updatePipelineToggleUI();
      return null;
    });

  state.pipelineLayerPromisesByKey.set(key, promise);
  return promise;
}

function pipelineUsesTiles(entry) {
  return Boolean(entry?.tile_template && Number.isFinite(Number(entry.tile_zoom)));
}

function pipelineTileStore(key) {
  if (!state.pipelineTileLayersByKey) state.pipelineTileLayersByKey = new Map();
  if (!state.pipelineTileLayersByKey.has(key)) {
    state.pipelineTileLayersByKey.set(key, {
      layers: new Map(),
      promises: new Map(),
      tileKeys: null,
    });
  }
  return state.pipelineTileLayersByKey.get(key);
}

function pipelineEntryTileKeys(entry) {
  if (!entry) return new Set();
  if (!entry._tileKeySet) entry._tileKeySet = new Set(entry.tile_keys || []);
  return entry._tileKeySet;
}

function lonLatToTile(lon, lat, zoom) {
  const n = 2 ** zoom;
  const clampedLat = Math.max(-85.05112878, Math.min(85.05112878, lat));
  const latRad = clampedLat * Math.PI / 180;
  const x = Math.floor((lon + 180) / 360 * n);
  const y = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * n);
  return {
    x: Math.max(0, Math.min(n - 1, x)),
    y: Math.max(0, Math.min(n - 1, y)),
  };
}

function visiblePipelineTileCoords(entry) {
  if (!state.map || !pipelineUsesTiles(entry)) return [];
  const zoom = Number(entry.tile_zoom);
  const bounds = state.map.getBounds().pad(0.12);
  const nw = lonLatToTile(bounds.getWest(), bounds.getNorth(), zoom);
  const se = lonLatToTile(bounds.getEast(), bounds.getSouth(), zoom);
  const minX = Math.min(nw.x, se.x);
  const maxX = Math.max(nw.x, se.x);
  const minY = Math.min(nw.y, se.y);
  const maxY = Math.max(nw.y, se.y);
  const available = pipelineEntryTileKeys(entry);
  const coords = [];
  for (let x = minX; x <= maxX; x++) {
    for (let y = minY; y <= maxY; y++) {
      const id = `${x}/${y}`;
      if (!available.size || available.has(id)) coords.push({ x, y, id });
    }
  }
  return coords;
}

function pipelineTileUrl(entry, coord) {
  return entry.tile_template
    .replace('{z}', String(entry.tile_zoom))
    .replace('{x}', String(coord.x))
    .replace('{y}', String(coord.y));
}

function hidePipelineTileStore(store) {
  if (!store || !state.map) return;
  for (const layer of store.layers.values()) {
    if (state.map.hasLayer(layer)) state.map.removeLayer(layer);
  }
}

async function ensurePipelineTileLayer(key, entry, coord, store) {
  if (store.layers.has(coord.id)) return store.layers.get(coord.id);
  if (store.promises.has(coord.id)) return store.promises.get(coord.id);

  const item = pipelineFilterItems().find((candidate) => candidate.key === key);
  updatePipelineStatus(`Loading ${item?.label || 'pipeline'} map tile...`);
  const promise = fetch(pipelineTileUrl(entry, coord))
    .then((response) => {
      if (!response.ok) throw new Error(`${key} tile ${coord.id}: HTTP ${response.status}`);
      return response.json();
    })
    .then((geojson) => {
      const layer = L.geoJSON(geojson, pipelineLayerOptions(key));
      store.layers.set(coord.id, layer);
      store.promises.delete(coord.id);
      updatePipelineStatus('');
      return layer;
    })
    .catch((err) => {
      store.promises.delete(coord.id);
      state.pipelineError = err.message || String(err);
      updatePipelineStatus(`Pipeline tile unavailable: ${state.pipelineError}`);
      return null;
    });

  store.promises.set(coord.id, promise);
  return promise;
}

async function syncPipelineTileCategory(key, entry, visible) {
  const store = pipelineTileStore(key);
  if (!visible) {
    hidePipelineTileStore(store);
    return;
  }
  if (state.map.getZoom() < PIPELINE_TILE_MIN_MAP_ZOOM) {
    hidePipelineTileStore(store);
    updatePipelineStatus('Zoom in to load detailed AER feeder pipeline tiles.');
    return;
  }
  updatePipelineStatus('');

  const needed = visiblePipelineTileCoords(entry);
  const neededIds = new Set(needed.map((coord) => coord.id));
  for (const [id, layer] of store.layers.entries()) {
    if (!neededIds.has(id) && state.map.hasLayer(layer)) state.map.removeLayer(layer);
  }

  await Promise.all(needed.map(async (coord) => {
    const layer = await ensurePipelineTileLayer(key, entry, coord, store);
    if (!layer || !state.map || !state.pipelineEnabled || !legendVisible(key)) return;
    if (!state.map.hasLayer(layer)) layer.addTo(state.map);
  }));
}

function hideNonVisiblePipelineLayers() {
  for (const item of pipelineFilterItems()) {
    const entry = pipelineIndexEntry(item.key);
    const visible = state.pipelineEnabled && legendVisible(item.key);
    if (pipelineUsesTiles(entry)) {
      if (!visible) hidePipelineTileStore(state.pipelineTileLayersByKey?.get(item.key));
      continue;
    }
    const store = pipelineLayerStore(item.key);
    const layer = store?.get(item.key);
    if (layer) setCachedLayerVisible(layer, visible);
  }
}

function schedulePipelineTileRefresh() {
  if (state.pipelineTileRefreshPending) return;
  state.pipelineTileRefreshPending = true;
  requestAnimationFrame(() => {
    state.pipelineTileRefreshPending = false;
    if (state.pipelineEnabled) syncPipelineLayerCache();
  });
}

async function syncPipelineLayerCache() {
  if (!state.map || !window.L) return;
  if (!state.pipelineEnabled) {
    hideNonVisiblePipelineLayers();
    return;
  }

  const ok = await fetchPipelineData();
  if (!ok) return;
  const work = [];
  for (const item of pipelineFilterItems()) {
    const key = item.key;
    const entry = pipelineIndexEntry(key);
    const visible = legendVisible(key);
    if (pipelineUsesTiles(entry)) {
      work.push(syncPipelineTileCategory(key, entry, visible));
    } else if (visible) {
      work.push(ensurePipelineCategoryLayer(key));
    }
  }
  await Promise.all(work);
  hideNonVisiblePipelineLayers();
  bringPipelineLayersToBack();
}

function renderPipelineSegmentLayer() {
  syncPipelineLayerCache();
}

function renderPipelineInstallLayer() {
  syncPipelineLayerCache();
}

function refreshPipelineLayers() {
  syncPipelineLayerCache();
  buildPipelineMenu();
}

function pipelineLegendCounts() {
  const counts = {};
  if (state.pipelineIndex) {
    for (const [key, entry] of Object.entries(state.pipelineIndex.line_categories || {})) {
      counts[key] = entry.count || 0;
    }
    for (const [key, entry] of Object.entries(state.pipelineIndex.installation_categories || {})) {
      counts[key] = entry.count || 0;
    }
    return counts;
  }
  return counts;
}

async function boot() {
  try {
    await loadData();
    initControls();
    initMap();
    // Default map state: official AB/BC fires, selected AER pipeline liquids,
    // and Canada + PADD II/V refinery regions.
    state.wildfireEnabled = fireSelectedCount() > 0;
    state.refineryEnabled = refinerySelectedCount() > 0;
    state.pipelineEnabled = pipelineSelectedCount() > 0;
    updateFireToggleUI();
    updateFormationToggleUI();
    updateRefineryToggleUI();
    updatePipelineToggleUI();
    updateMarketPipelineToggleUI();
    updateWildfireStatus("Fetching official Alberta and BC fire data...");
    render();
    // Fetch defaults in parallel. NRCan CWFIS/FWI stays off until selected.
    fetchAlbertaFires();
    fetchBCFires();
    fetchPipelineData().then((ok) => {
      if (ok) refreshPipelineLayers();
    });
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

  // Expose so distance tool can deactivate select mode
  state.setSelectMode = setSelectMode;

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
    for (const point of byAsset.values()) {
      const { asset } = point;
      if (asset.latitude == null) continue;
      if (!legendVisible(pointLegendKey(point))) continue;
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
// ============================================================

const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const SEA_COLORS   = { band: "#d1d5db", y0: "#2563eb", y1: "#16a34a", yCur: "#dc2626" };

function computeSeasonality(assetIds) {
  const ym = {};
  const assetSet = new Set(assetIds); // O(1) lookup instead of O(n) includes()

  // Base records (oil sands, petrinex NGL — always loaded at startup)
  for (const r of state.baseRecords) {
    if (!assetSet.has(r.asset_id)) continue;
    const year  = Number(r.date.slice(0, 4));
    const month = Number(r.date.slice(5, 7));
    if (!ym[year]) ym[year] = {};
    ym[year][month] = (ym[year][month] || 0) + r.volume_kbbl_d;
  }

  // Petrinex / BCER historical index (pre-aggregated; covers AB conventional + BC)
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

  // On-demand cache (BC + AB conventional for dates the user has already visited).
  // This fills in BC production history from already-loaded on_demand files.
  if (state.dateRecordCache) {
    for (const records of state.dateRecordCache.values()) {
      for (const r of records) {
        if (!assetSet.has(r.asset_id)) continue;
        const year  = Number(r.date.slice(0, 4));
        const month = Number(r.date.slice(5, 7));
        if (!ym[year]) ym[year] = {};
        ym[year][month] = (ym[year][month] || 0) + (r.volume_kbbl_d || 0);
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
  const existing = document.getElementById("seasonalityPanel");
  if (existing) existing.remove();

  if (!state.seasonalityIndex && !state.seasonalityIndexLoading) {
    state.seasonalityIndexLoading = true;
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
      const resp = await fetch("public/data/asset_seasonality.json?v=20260521");
      state.seasonalityIndex = await resp.json();
    } catch(e) {
      console.warn("Could not load asset_seasonality.json:", e);
      state.seasonalityIndex = {};
    }
    state.seasonalityIndexLoading = false;
    loadingPanel.remove();
  } else if (state.seasonalityIndexLoading) {
    setTimeout(() => showSeasonalityPanel(assetIds), 300);
    return;
  }

  const data = computeSeasonality(assetIds);
  const { byAsset } = aggregateForDate();

  const names = assetIds.slice(0, 3).map(id => {
    const hit = byAsset.get(id);
    return hit ? hit.asset.display_name : id;
  });
  const titleStr = names.join(", ") + (assetIds.length > 3 ? ` +${assetIds.length - 3} more` : "");

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

  const fullYears = years.filter(y => y !== currentYear && Object.keys(ym[y] || {}).length === 12);
  const envYears  = fullYears.slice(-5);
  const lineYears = fullYears.slice(-2);

  const envMin = new Array(12).fill(Infinity);
  const envMax = new Array(12).fill(-Infinity);
  for (const y of envYears) {
    for (let m = 1; m <= 12; m++) {
      const v = ym[y]?.[m] ?? 0;
      if (v < envMin[m-1]) envMin[m-1] = v;
      if (v > envMax[m-1]) envMax[m-1] = v;
    }
  }
  for (let i = 0; i < 12; i++) {
    if (envMin[i] === Infinity)  envMin[i] = 0;
    if (envMax[i] === -Infinity) envMax[i] = 0;
  }

  let globalMax = 0;
  for (const y of [...envYears, ...lineYears, currentYear]) {
    for (let m = 1; m <= 12; m++) {
      const v = ym[y]?.[m] ?? 0;
      if (v > globalMax) globalMax = v;
    }
  }
  if (globalMax === 0) globalMax = 1;

  const xPos = (m) => pad.left + ((m - 0.5) / 12) * cW;
  const yPos = (v) => pad.top + cH - (v / globalMax) * cH;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = "#f9fafb";
  ctx.fillRect(0, 0, W, H);

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

  ctx.save();
  ctx.translate(12, pad.top + cH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillStyle = "#6b7280";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("kbbl/d", 0, 0);
  ctx.restore();

  ctx.fillStyle = "#6b7280";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "center";
  for (let m = 1; m <= 12; m++) {
    ctx.fillText(MONTH_LABELS[m-1], xPos(m), H - pad.bottom + 14);
  }

  if (envYears.length > 0) {
    ctx.beginPath();
    for (let m = 1; m <= 12; m++) ctx.lineTo(xPos(m), yPos(envMax[m-1]));
    for (let m = 12; m >= 1; m--) ctx.lineTo(xPos(m), yPos(envMin[m-1]));
    ctx.closePath();
    ctx.fillStyle = "rgba(156,163,175,0.28)";
    ctx.fill();
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

  const curMonths = Object.keys(ym[currentYear] || {}).map(Number);
  if (curMonths.length) {
    ctx.strokeStyle = SEA_COLORS.yCur;
    ctx.fillStyle = SEA_COLORS.yCur;
    ctx.lineWidth = 2;
    const sorted = curMonths.sort((a,b) => a-b);
    ctx.beginPath();
    sorted.forEach((m, i) => {
      const v = ym[currentYear][m] ?? 0;
      i === 0 ? ctx.moveTo(xPos(m), yPos(v)) : ctx.lineTo(xPos(m), yPos(v));
    });
    ctx.stroke();
    sorted.forEach(m => {
      const v = ym[currentYear][m] ?? 0;
      ctx.beginPath();
      ctx.arc(xPos(m), yPos(v), 3.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

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
