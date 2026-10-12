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
  railways: "public/data/railways.geojson",
  pipelineIndex: "public/data/aer_pipeline_index.json",
};

const DEFAULT_BASEMAP_KEY = "topographic";
const BASEMAP_META = {
  dark: {
    label: "Dark",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    referenceUrl: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
    options: {
      maxZoom: 13,
      attribution: "Tiles &copy; Esri &mdash; Sources: Esri, HERE, Garmin, &copy; OpenStreetMap contributors, GIS User Community",
    },
    referenceOptions: {
      maxZoom: 13,
      attribution: "",
      className: "basemap-label-layer",
      pane: "basemapLabels",
    },
  },
  topographic: {
    label: "Topo",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    options: {
      maxZoom: 13,
      attribution: "Tiles: Esri World Topographic Map",
    },
  },
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
  petrinex_sk_well_production:   "Petrinex SK",
  bcer_well_production:          "BCER wells",
  ndic_well_production:          "NDIC wells",
  montana_bogc_well_production:  "Montana BOGC",
  manitoba_well_production:      "Manitoba wells",
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

const RAILWAY_CATEGORY_META = {
  "rail-main": {
    label: "Main rail network",
    detail: "BTS/FRA NARN main network across Canada and the United States",
    color: "#111827",
    kind: "line",
  },
  "rail-industrial": {
    label: "Major industrial rail leads",
    detail: "Major industrial and terminal access tracks from BTS/FRA NARN",
    color: "#6b7280",
    kind: "line",
  },
  "crude-rail-terminal": {
    label: "Crude rail terminals",
    detail: "EIA-derived crude-by-rail inventory plus Canadian rail/transload facilities; source dates vary",
    color: "#111827",
    kind: "point",
  },
  "crude-terminal": {
    label: "Crude storage / marine terminals",
    detail: "Crude pipeline and marine terminals; source location and operating status vary",
    color: "#9a5546",
    kind: "point",
  },
  "product-terminal": {
    label: "Fuel / petroleum product terminals",
    detail: "Operator maps and EIA-derived inventory plus Canadian facilities; source dates and operators vary",
    color: "#0f766e",
    kind: "point",
  },
  "crude-storage": {
    label: "Crude oil storage",
    detail: "Storage sites identified by an operator or regulator; capacity is shown only when sourced",
    color: "#b45309",
    kind: "point",
  },
  "product-storage": {
    label: "Refined-product storage",
    detail: "Verified storage service for gasoline, diesel, jet fuel or other refined products",
    color: "#0369a1",
    kind: "point",
  },
  "ngl-storage": {
    label: "NGL / LPG storage",
    detail: "Storage facilities for natural gas liquids; distinct from crude and refined products",
    color: "#7c3aed",
    kind: "point",
  },
  "inactive-terminal": {
    label: "Inactive / decommissioned terminals",
    detail: "Former facilities retained for historical context and hidden by default",
    color: "#94a3b8",
    kind: "point",
  },
};

const DEFAULT_RAILWAY_CATEGORIES = ["rail-main", "crude-rail-terminal", "crude-terminal", "product-terminal", "crude-storage", "product-storage", "ngl-storage"];

// Rail line colour = owning railroad (first listed NARN owner, RROWNER1).
// Class I systems get distinct colours; passenger/commuter and regional/short
// lines are grouped. KCS/KCSM are shown as CPKC post-merger.
const RAIL_OWNER_META = [
  { key: "cn",        label: "CN",                     color: "#d62828", codes: ["CN", "BCR", "BCOL", "GTW", "IC", "WC", "EJE"] },
  { key: "cpkc",      label: "CPKC",                   color: "#e8a013", codes: ["CPKC", "CP", "CPRS", "KCS", "KCSM", "SOO", "DME"] },
  { key: "bnsf",      label: "BNSF",                   color: "#16803c", codes: ["BNSF"] },
  { key: "up",        label: "Union Pacific",          color: "#6d4c9f", codes: ["UP"] },
  { key: "csx",       label: "CSX",                    color: "#1d6ceb", codes: ["CSXT", "CSX"] },
  { key: "ns",        label: "Norfolk Southern",       color: "#1f2937", codes: ["NS"] },
  { key: "passenger", label: "Passenger / commuter",   color: "#9aa5b1", codes: [] },
  { key: "other",     label: "Regional & short line",  color: "#7b8794", codes: [] },
];
const RAIL_OWNER_DARK_COLORS = {
  cn: "#ff5a5f",
  cpkc: "#ffc43d",
  bnsf: "#4ade80",
  up: "#c084fc",
  csx: "#38bdf8",
  ns: "#f8fafc",
  passenger: "#d1d5db",
  other: "#a8b8c8",
};
const RAIL_TERMINAL_DARK_COLORS = {
  "crude-rail-terminal": "#fb923c",
  "crude-terminal": "#fb7185",
  "product-terminal": "#2dd4bf",
  "crude-storage": "#fbbf24",
  "product-storage": "#38bdf8",
  "ngl-storage": "#c084fc",
  "inactive-terminal": "#cbd5e1",
};
const RAIL_OWNER_BY_CODE = new Map(
  RAIL_OWNER_META.flatMap((m) => m.codes.map((code) => [code, m]))
);
const PASSENGER_RAIL_OWNERS = new Set([
  "AMTK", "VIA", "GO", "EXO", "AMT", "MBTA", "NJT", "MNCW", "LI", "SCAX",
  "NIRC", "MARC", "VRE", "UTA", "TRE", "DART", "ACEX", "NCTD", "SDNX",
  "SFRTA", "WES", "CTRL", "MTS",
]);
const RAIL_OWNER_FALLBACK = RAIL_OWNER_META.find((m) => m.key === "other");
const RAIL_OWNER_PASSENGER = RAIL_OWNER_META.find((m) => m.key === "passenger");

function railLineOwnerMeta(props) {
  const raw = String(props?.owner || "").trim();
  if (!raw) return RAIL_OWNER_FALLBACK;
  const code = raw.split(",")[0].trim().toUpperCase();
  if (RAIL_OWNER_BY_CODE.has(code)) return RAIL_OWNER_BY_CODE.get(code);
  if (PASSENGER_RAIL_OWNERS.has(code)) return RAIL_OWNER_PASSENGER;
  return RAIL_OWNER_FALLBACK;
}

const DEFAULT_REFINERY_GROUP_KEYS = [
  "canada-western",
  "canada-central",
  "canada-eastern",
  "us-padd-i",
  "us-padd-ii",
  "us-padd-iii",
  "us-padd-iv",
  "us-padd-v",
  "mexico",
  "europe",
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
  refreshStatus: null,
  referenceStatus: null,
  statusLoading: false,
  statusError: null,
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
  basemapKey: DEFAULT_BASEMAP_KEY,
  basemapLayer: null,
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
  fireImpactSettings: {
    windArrow: true,
    downwindCorridor: true,
    exposedProduction: true,
  },
  hoverFireImpactLayer: null,
  hoverFireImpactAbort: null,
  hoverFireImpactToken: null,
  hoverFireTooltipLayer: null,
  hoverFireBaseTooltipHtml: "",
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
  marketPipelineSearch: "",
  railwayEnabled: false,
  railwayData: null,
  railwayLoading: false,
  railwayError: null,
  railwayLayer: null,
  railwayLineLayer: null,
  railwayLineData: null,
  railwayLineSelection: '',
  selectedRailwayCategories: new Set(DEFAULT_RAILWAY_CATEGORIES),
  selectedRailwayOwners: new Set(RAIL_OWNER_META.map((meta) => meta.key)),
  railwayMenuOpen: false,
  railwaySearch: "",
  railwaySearchTimer: null,
  // Seasonality index (lazy-loaded from asset_seasonality.json)
  seasonalityIndex: null,
  seasonalityIndexLoading: false,
  // Multi-asset rubber-band selection
  selectedAssets: [],
  rubberBandActive: false,
  selectMode: false,
  setSelectMode: null,
  selectModeKind: "assets", // "assets" | "refineries"
  selectMenuOpen: false,
  hiddenLegendKeys: new Set(DEFAULT_HIDDEN_LEGEND_KEYS),
  distanceMode: false,
  distancePoints: [],
  distanceLayer: null,
  facilityLayer: null,
  optionalDataWarnings: [],
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
  railwayToggle:    document.querySelector("#railwayToggle"),
  distanceToggle:   document.querySelector("#distanceToggle"),
  distanceStatus:   document.querySelector("#distanceStatus"),
  mapLegend:        document.querySelector("#mapLegend"),
  basemapSwitch:    document.querySelector("#basemapSwitch"),
  map:              document.querySelector("#map"),
  mapFallback:      document.querySelector("#mapFallback"),
};

// ============================================================
// FORMAT HELPERS
// ============================================================

const NUMBER_FORMATTERS = new Map();
function formatNumber(value, digits = 0) {
  if (!Number.isFinite(value)) return "--";
  if (!NUMBER_FORMATTERS.has(digits)) NUMBER_FORMATTERS.set(digits, new Intl.NumberFormat("en-CA", {
    maximumFractionDigits: digits, minimumFractionDigits: digits,
  }));
  return NUMBER_FORMATTERS.get(digits).format(value);
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

function safeHttpUrl(value) {
  if (!value) return "";
  try {
    const url = new URL(String(value), window.location.href);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : "";
  } catch (_error) {
    return "";
  }
}

function safeCssColor(value, fallback = "#334155") {
  const candidate = String(value || "").trim();
  if (!candidate) return fallback;
  if (window.CSS?.supports?.("color", candidate)) return candidate;
  return /^#(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(candidate) ? candidate : fallback;
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

async function requestJson(url, options = {}) {
  const { timeoutMs = 45000, ...fetchOptions } = options;
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort(fetchOptions.signal?.reason);
  if (fetchOptions.signal?.aborted) abort();
  else fetchOptions.signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetch(url, { cache: "no-cache", ...fetchOptions, signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (data?.error) throw new Error(data.error.message || data.reason || "Source returned an error");
    if (data?.exceededTransferLimit || data?.properties?.exceededTransferLimit) {
      throw new Error("Source response is incomplete (transfer limit)");
    }
    return data;
  } catch (error) {
    if (timedOut && !fetchOptions.signal?.aborted) {
      const timeout = new Error("Source request timed out");
      timeout.name = "TimeoutError";
      throw timeout;
    }
    throw error;
  } finally {
    clearTimeout(timer);
    fetchOptions.signal?.removeEventListener("abort", abort);
  }
}

function requireFeatureCollection(data) {
  if (data?.type !== "FeatureCollection" || !Array.isArray(data.features)) {
    throw new Error("Invalid geographic data response");
  }
  return data;
}

async function loadData() {
  const requiredDataPaths = [
    DATA_PATHS.manifest,
    DATA_PATHS.assets,
    DATA_PATHS.production,
  ];
  const optionalData = [
    [DATA_PATHS.schemeApprovals, "AER scheme approvals"],
    [DATA_PATHS.st102Facilities, "AER ST102 facilities"],
    [DATA_PATHS.assetGeometries, "asset footprints"],
    [DATA_PATHS.refineries, "refineries"],
  ];
  state.optionalDataWarnings = [];
  const [requiredResults, optionalResults] = await Promise.all([
    Promise.all(requiredDataPaths.map((path) => requestJson(path))),
    Promise.all(optionalData.map(([path, label]) => fetchOptionalFeatureCollection(path, label))),
  ]);
  const [manifest, assets, records] = requiredResults;
  const [schemeApprovals, st102Facilities, assetGeometries, refineries] = optionalResults;
  const assetRows = expandAssetRecords(assets);
  if (!assetRows.length || !Array.isArray(records) || !Array.isArray(manifest.periods) || !manifest.periods.length) {
    throw new Error("Production data is incomplete. Please reload or contact the data administrator.");
  }
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

  const sourceIds = [...new Set([...records.map((r) => r.source_id), ...(manifest.source_coverage || []).map((r) => r.source_id)])].sort();
  recordsForDate(state.selectedDate).forEach((r) => sourceIds.push(r.source_id));
  [...new Set(sourceIds)].sort().forEach((s) => state.selectedSources.add(s));

  const initialRecords = recordsForDate(state.selectedDate);
  [...new Set([...initialRecords.map((r) => r.stream), ...(manifest.source_coverage || []).map((r) => r.stream)])].filter(Boolean).forEach((s) => state.selectedStreams.add(s));
}

async function fetchOptionalJson(path) {
  return requestJson(path);
}

async function fetchOptionalFeatureCollection(path, label) {
  try {
    const data = await fetchOptionalJson(path);
    if (!data || data.type !== "FeatureCollection" || !Array.isArray(data.features)) {
      throw new Error("invalid FeatureCollection schema");
    }
    return data;
  } catch (error) {
    state.optionalDataWarnings.push(`${label}: ${error.message || error}`);
    return { type: "FeatureCollection", features: [] };
  }
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

function monthlyAssetId(ref) {
  if (typeof ref === "number") return state.assets?.[ref]?.asset_id || "";
  return ref || "";
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
        (group.rows || []).map(([asset_ref, volume_kbbl_d]) => ({
          date:           group.date,
          asset_id:       monthlyAssetId(asset_ref),
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
    return (raw.rows || []).map(([asset_ref, volume_kbbl_d]) => ({
      date:           raw.date,
      asset_id:       monthlyAssetId(asset_ref),
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
    const raw = await requestJson(path);
    const records = expandMonthlyRecords(raw);
    if (!records.length || records.some((r) => r.date !== date || !state.assetById.has(r.asset_id) || !Number.isFinite(r.volume_kbbl_d) || r.volume_kbbl_d < 0)) {
      throw new Error("Monthly production data is incomplete or invalid");
    }
    state.dateRecordCache.set(date, records);
    state.timelineCache = null;
  } catch (error) {
    state.dateRecordErrors.set(date, error.message || String(error));
  } finally {
    state.dateRecordLoading.delete(date);
  }
}

function requestDateRecords(date) {
  if (!state.manifest?.monthly_record_files?.[date]) return;
  if (state.dateRecordCache.has(date) || state.dateRecordLoading.has(date) || state.dateRecordErrors.has(date)) return;
  ensureDateRecords(date).then(() => {
    if (state.selectedDate === date) {
      state.records = recordsForDate(date);
      // The successful loader invalidates totals before this redraw.
      render();
    }
  });
}

// ============================================================
// CONTROLS INIT
// ============================================================

function initControls() {
  const sourceCount = new Set((state.manifest.source_coverage || []).map((item) => item.source_id)).size;
  const overlayWarningCount = state.optionalDataWarnings.length;
  const overlayWarningText = overlayWarningCount
    ? ` · ⚠ ${overlayWarningCount} optional overlay${overlayWarningCount === 1 ? "" : "s"} unavailable`
    : "";
  els.freshness.textContent = `${sourceCount || "--"} production sources · updated ${dateLabel(String(state.manifest.generated_at).slice(0, 10))}${overlayWarningText}`;
  els.freshness.title = state.optionalDataWarnings.join("\n");

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

  const sourceIds = [...state.selectedSources].sort();
  els.sourceFilters.innerHTML = sourceIds
    .map((s) => toggleMarkup("source", s, SOURCE_SHORT[s] || s))
    .join("");
  els.sourceFilters.addEventListener("change", (e) => updateSetFromToggle(e, "source", state.selectedSources));

  const streamNames = [...state.selectedStreams].sort((a, b) => {
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

  els.etlCommand.textContent = "gh workflow run refresh-official-data.yml --ref main";
  els.etlButton.addEventListener("click", () => { renderDataStatus(); els.etlPanel.hidden = false; els.closeEtl.focus(); refreshDataStatus(); });
  els.closeEtl.addEventListener("click", () => { els.etlPanel.hidden = true; els.etlButton.focus(); });
  document.getElementById("retryDataBtn")?.addEventListener("click", async () => {
    state.dateRecordErrors.delete(state.selectedDate);
    await ensureDateRecords(state.selectedDate);
    render();
    renderDataStatus();
  });
  document.getElementById("toggleFiltersBtn")?.addEventListener("click", (event) => {
    const rail = document.querySelector(".filter-rail");
    const expanded = event.currentTarget.getAttribute("aria-expanded") !== "true";
    event.currentTarget.setAttribute("aria-expanded", String(expanded));
    rail.classList.toggle("mobile-open", expanded);
  });

  // ── Docs panel ──
  if (els.docsBtn && els.docsPanel) {
    els.docsBtn.addEventListener("click", () => {
      els.docsPanel.hidden = false;
      els.docsBtn.classList.add("active");
      els.closeDocs.focus();
    });
    els.closeDocs.addEventListener("click", () => {
      els.docsPanel.hidden = true;
      els.docsBtn.classList.remove("active");
      els.docsBtn.focus();
    });
    els.docsPanel.addEventListener("keydown", e => {
      if (e.key === "Escape") { els.docsPanel.hidden = true; els.docsBtn.classList.remove("active"); }
    });
    // Tab switching
    els.docsPanel.querySelectorAll(".docs-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        els.docsPanel.querySelectorAll(".docs-tab").forEach(t => { t.classList.remove("active"); t.setAttribute("aria-selected", "false"); });
        els.docsPanel.querySelectorAll(".docs-section").forEach(s => { s.hidden = true; });
        tab.classList.add("active");
        tab.setAttribute("aria-selected", "true");
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
    marketPipelineMenu.addEventListener("input", handleInfrastructureSearchInput);
  }
  if (els.railwayToggle) {
    els.railwayToggle.addEventListener("click", toggleRailways);
  }
  const railwayMenu = document.getElementById("railwayMenu");
  if (railwayMenu) {
    railwayMenu.addEventListener("change", handleRailwayMenuChange);
    railwayMenu.addEventListener("click", handleRailwayMenuClick);
    railwayMenu.addEventListener("input", handleInfrastructureSearchInput);
    buildRailwayMenu();
    updateRailwayToggleUI();
  }
  document.addEventListener("click", (event) => {
    const control = document.getElementById("marketPipelineControl");
    if (control && !control.contains(event.target)) {
      setMarketPipelineMenuOpen(false);
    }
    const railwayControl = document.getElementById("railwayControl");
    if (railwayControl && !railwayControl.contains(event.target)) {
      setRailwayMenuOpen(false);
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
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (!els.etlPanel.hidden) { els.etlPanel.hidden = true; els.etlButton.focus(); }
      if (!els.docsPanel.hidden) { els.docsPanel.hidden = true; els.docsBtn.classList.remove("active"); els.docsBtn.focus(); }
      [setFireMenuOpen, setRefineryMenuOpen, setFormationMenuOpen, setPipelineMenuOpen, setMarketPipelineMenuOpen, setRailwayMenuOpen].forEach((close) => close(false));
      state.setSelectMode?.(false);
      setDistanceMode(false);
    }
    const panel = !els.docsPanel.hidden ? els.docsPanel : !els.etlPanel.hidden ? els.etlPanel : null;
    if (event.key === "Tab" && panel) {
      const focusable = [...panel.querySelectorAll('button, a[href], input, select, summary, [tabindex="0"]')].filter((el) => el.getClientRects().length && !el.disabled);
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });
  initLegendControls();
}

async function refreshDataStatus() {
  if (state.statusLoading) return;
  state.statusLoading = true;
  state.statusError = null;
  renderDataStatus();
  const results = await Promise.allSettled([
    fetchJsonLive("public/data/elt_status.json"),
    fetchJsonLive("public/data/reference_source_status.json"),
  ]);
  ["refreshStatus", "referenceStatus"].forEach((key, index) => {
    if (results[index].status === "fulfilled" && results[index].value?.schema_version === 1) state[key] = results[index].value;
    else state.statusError = "Automatic refresh status is temporarily unavailable. Published production remains accessible.";
  });
  state.statusLoading = false;
  renderDataStatus();
}

function dataStatusLink(url, label) {
  if (!/^https:\/\/(github\.com|www\.eia\.gov)\//.test(String(url || ""))) return "";
  return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function renderDataStatus() {
  const target = document.getElementById("dataStatusContent");
  if (!target || !state.manifest) return;
  const coverage = (state.manifest.source_coverage || []).filter((r) => r.scenario === "actual");
  const warnings = [...state.optionalDataWarnings, ...state.dateRecordErrors.values(), ...(state.statusError ? [state.statusError] : [])];
  const checks = ["production", "infrastructure"].filter((key) => state.refreshStatus?.[key]).map((key) => {
    const check = state.refreshStatus[key];
    const statusLabel = {failed: "Update held", degraded: "Needs attention", updated: "Updated", unchanged: "No new data"}[check.status] || "Pending";
    return `<div class="refresh-card"><div class="refresh-card-heading"><strong>${key === "production" ? "Production" : "Infrastructure"}</strong><span class="refresh-badge ${["failed", "degraded"].includes(check.status) ? "needs-review" : ""}">${escapeHtml(statusLabel)}</span></div>
      ${check.scope ? `<p>${escapeHtml(check.scope)}</p>` : ""}<p>${check.execution_mode === "offline_replay" ? "Local replay of official inputs · " : ""}${check.checked_at ? `Checked ${escapeHtml(formatDateTime(check.checked_at))}` : "Online source check pending"}<br>Last data update: ${check.last_data_update ? escapeHtml(formatDateTime(check.last_data_update)) : "Awaiting first successful refresh"}</p>
      ${(check.warnings || []).map((warning) => `<p class="data-status-warning">${escapeHtml(warning)}</p>`).join("")}
      <div class="refresh-links">${dataStatusLink(check.run_url, "Run details")}${dataStatusLink(check.raw_archive_url, "Source archive")}</div></div>`;
  }).join("");
  const review = (state.referenceStatus?.checks || []).filter((check) => check.review_required);
  target.innerHTML = `<p>Official reported production · <strong>No analyst forecasts</strong></p>
    <p>Selected month: <strong>${escapeHtml(dateLabel(state.selectedDate))}</strong>. Dataset built ${escapeHtml(formatDateTime(state.manifest.generated_at))} · Each source has its own reporting lag.</p>
    <div class="refresh-policy">Production checked daily · Infrastructure weekly · Power every 30 minutes</div>
    ${state.statusLoading ? '<p role="status">Checking refresh status…</p>' : ""}
    ${checks ? `<div class="refresh-grid">${checks}</div>` : ""}
    ${review.length ? `<details class="reference-review"><summary>${review.length} reference sources need attention</summary><p>Reviewed capacities, tariffs and statuses retain their verification dates until a change is reconciled.</p><ul>${review.map((check) => `<li><strong>${escapeHtml(check.name || check.id)}</strong>: ${escapeHtml(check.error || check.reason || check.status)}</li>`).join("")}</ul></details>` : ""}
    ${state.referenceStatus ? `<p class="refresh-source-note">Reference check: ${escapeHtml(formatDateTime(state.referenceStatus.checked_at))} · ${dataStatusLink("https://www.eia.gov/petroleum/refinerycapacity/", "EIA annual capacity source")} · <a href="public/data/eia_refinery_capacity.json" target="_blank" rel="noopener noreferrer">Official capacity snapshot</a></p>` : ""}
    ${warnings.length ? `<p class="data-status-warning">${warnings.map(escapeHtml).join("<br>")}</p>` : ""}
    <div class="data-status-scroll"><table class="docs-table"><thead><tr><th>Source / stream</th><th>Latest actual</th></tr></thead><tbody>${coverage.map((r) => `<tr><td><strong>${escapeHtml(SOURCE_SHORT[r.source_id] || r.source_id)}</strong><br>${escapeHtml(r.stream)}</td><td>${escapeHtml(dateLabel(r.last_date))}</td></tr>`).join("")}</tbody></table></div>
    <p>Volumes are monthly daily averages. Summing bitumen with synthetic crude, or raw NGL mix with finished NGL products, can count the same material twice. The map is an asset exposure view; its gross stream sum is not net regional supply.</p>
    <p>Pipeline routes follow published GIS where available. Approximate corridors and DLS locations are identified in tooltips. Public infrastructure inventories may omit gathering and private systems.</p>`;
  const retry = document.getElementById("retryDataBtn");
  if (retry) retry.hidden = !state.dateRecordErrors.has(state.selectedDate);
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

function initLegendDisclosure() {
  const legend = els.mapLegend;
  if (!legend || legend.querySelector("#legendItems")) return;
  const header = legend.querySelector(".map-legend-header");
  if (!header) return;
  const toggle = document.createElement("button");
  toggle.id = "legendToggle";
  toggle.type = "button";
  toggle.className = "map-legend-header";
  toggle.setAttribute("aria-controls", "legendItems");
  toggle.setAttribute("aria-expanded", "false");
  toggle.title = "Show legend";
  toggle.innerHTML = '<span>Legend</span><span class="legend-caret" aria-hidden="true">▴</span>';
  const items = document.createElement("div");
  items.id = "legendItems";
  items.hidden = true;
  header.replaceWith(toggle);
  Array.from(legend.children).filter((child) => child !== toggle).forEach((child) => items.appendChild(child));
  legend.appendChild(items);
  legend.classList.add("is-collapsed");
  toggle.addEventListener("click", () => {
    items.hidden = !items.hidden;
    toggle.setAttribute("aria-expanded", String(!items.hidden));
    toggle.title = items.hidden ? "Show legend" : "Hide legend";
    toggle.querySelector(".legend-caret").textContent = items.hidden ? "▴" : "▾";
    legend.classList.toggle("is-collapsed", items.hidden);
  });
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
    if (POINT_LEGEND_KEYS.has(key)) {
      state.timelineCache = null;
      scheduleRender();
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
    if (els.basemapSwitch) els.basemapSwitch.hidden = true;
    state.fallbackReady = true;
    return;
  }
  state.map = L.map("map", {
    zoomControl: false,
    attributionControl: true,
    preferCanvas: true,
    // Keep thin map lines easy to hover and tap without drawing wider strokes.
    renderer: L.canvas({ tolerance: 5 }),
  }).setView([55.7, -112.0], 5);

  L.control.zoom({ position: "bottomright" }).addTo(state.map);
  const basemapLabelsPane = state.map.createPane("basemapLabels");
  basemapLabelsPane.style.zIndex = "625";
  basemapLabelsPane.style.pointerEvents = "none";
  initBasemapSwitch();
  state.markerLayer = L.layerGroup().addTo(state.map);
  initRubberBand();
  initDistanceTool();
  state.map.on("moveend zoomend", schedulePipelineTileRefresh);
  state.map.on("zoomend", refreshRailwayStyles);
}

function updateBasemapUI() {
  if (!els.basemapSwitch) return;
  els.basemapSwitch.querySelectorAll("button[data-basemap]").forEach((button) => {
    const selected = button.dataset.basemap === state.basemapKey;
    button.setAttribute("aria-pressed", selected ? "true" : "false");
  });
  const mapStage = els.map?.closest(".map-stage");
  if (mapStage) mapStage.dataset.basemap = state.basemapKey;
}

function setBasemap(key) {
  if (!state.map || !window.L || !BASEMAP_META[key]) return;
  if (state.basemapLayer) state.map.removeLayer(state.basemapLayer);
  state.basemapKey = key;
  const meta = BASEMAP_META[key];
  const layers = [L.tileLayer(meta.url, meta.options)];
  if (meta.referenceUrl) {
    layers.push(L.tileLayer(meta.referenceUrl, meta.referenceOptions || {}));
  }
  state.basemapLayer = layers.length === 1 ? layers[0] : L.layerGroup(layers);
  state.basemapLayer.addTo(state.map);
  if (typeof state.basemapLayer.bringToBack === "function") state.basemapLayer.bringToBack();
  updateBasemapUI();
  refreshRailwayStyles();
  if (state.railwayData) buildRailwayMenu();
}

function initBasemapSwitch() {
  if (!els.basemapSwitch) return;
  els.basemapSwitch.hidden = false;
  els.basemapSwitch.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-basemap]");
    if (!button || !els.basemapSwitch.contains(button)) return;
    setBasemap(button.dataset.basemap);
  });
  setBasemap(state.basemapKey);
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
      .setContent(escapeHtml(snapped.label))
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
  }

  const sourceTotals = new Map();
  for (const [assetId, point] of byAsset) {
    if (!legendVisible(pointLegendKey(point))) {
      byAsset.delete(assetId);
      continue;
    }
    for (const record of point.records) {
      sourceTotals.set(record.source_id, (sourceTotals.get(record.source_id) || 0) + record.volume_kbbl_d);
    }
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

function matchingReportedRecords(date = state.selectedDate) {
  return recordsForDate(date).filter(record => {
    if (record.scenario !== "actual" || typeof record.volume_kbbl_d !== "number"
      || !Number.isFinite(record.volume_kbbl_d) || record.volume_kbbl_d < 0) return false;
    const asset = state.assetById.get(record.asset_id);
    if (!asset || asset.is_rollup || ["province", "province_refinery", "region"].includes(asset.asset_kind)) return false;
    if (!state.selectedSources.has(record.source_id) || !state.selectedStreams.has(record.stream)
      || !state.selectedLocationConfidence.has(locationConfidenceKey(asset))) return false;
    if (!legendVisible(STREAM_LEGEND_KEYS[record.stream] || systemMeta(asset.production_system).className)) return false;
    return !state.search || `${asset.display_name} ${asset.company} ${asset.province} ${record.stream}`.toLowerCase().includes(state.search);
  });
}

function productionGroupsForActiveFilters(catalog) {
  const active = new Set();
  for (const date of Object.keys(state.manifest?.date_filter_totals || {})) {
    for (const row of selectedDateSummaryRows(date)) if (row.scenario === "actual") active.add(productionGroupKey(row.source_id, row.stream));
  }
  const searchSources = new Set();
  if (state.search) {
    for (const asset of state.assetById.values()) {
      if (`${asset.display_name} ${asset.company} ${asset.province}`.toLowerCase().includes(state.search)) searchSources.add(asset.source_id);
    }
  }
  return catalog.filter(group => state.selectedSources.has(group.source_id) && state.selectedStreams.has(group.stream)
    && (!active.size || active.has(group.key))
    && (!state.search || searchSources.has(group.source_id) || group.stream.toLowerCase().includes(state.search)));
}

function productionReportingForDate(date, total, catalogInfo = productionReportingCatalog(), groups = productionGroupsForActiveFilters(catalogInfo.catalog)) {
  // A source-wide summary cannot establish an observation for a name search.
  const rows = state.search ? [] : selectedDateSummaryRows(date).filter(row => row.scenario === "actual");
  const records = matchingReportedRecords(date);
  const present = new Set([...rows, ...records].map(row => productionGroupKey(row.source_id, row.stream)));
  const loading = state.dateRecordLoading.has(date) || state.dateRecordErrors.has(date)
    || (state.search && state.manifest?.monthly_record_files?.[date] && !state.dateRecordCache.has(date));
  const hasAmount = total > 0 || records.some(record => record.volume_kbbl_d === 0) || rows.some(row => row.kbbl_d === 0);
  const point = classifyProductionMonth(date, groups, present, hasAmount ? total : null,
    !loading && groups.length > 0);
  if (loading && point.reportedTotal !== null) {
    point.status = "unverified";
    point.value = null;
    point.note = "Monthly records have not finished loading. The displayed amount is an incomplete subtotal.";
  }
  return applyProductionQuality(point, groups);
}

// Sources that stopped reporting before this date while other sources continue.
// The ETL's stored date_warnings only compare each source-stream's own last two
// months, so a source that simply drops out (e.g. Petrinex AB after its final
// cached month) produced no warning at all — months after the drop silently
// looked like clean "actual" months at half the volume. This recovers that case
// client-side from manifest.source_coverage.
function missingSourcesForDate(date = state.selectedDate) {
  if (!date) return [];
  const rows = state.manifest?.date_filter_totals?.[date] || [];
  if (!rows.length) return [];
  if (!rows.some((row) => row.scenario === "actual")) return [];
  const present = new Set(rows.filter((row) => row.scenario === "actual").map((row) => `${row.source_id}|${row.stream}`));
  const missing = new Map();
  for (const item of state.manifest?.source_coverage || []) {
    if (item.scenario !== "actual") continue;
    if (!item.last_date || !item.first_date) continue;
    if (present.has(`${item.source_id}|${item.stream}`)) continue;
    if (!state.selectedSources.has(item.source_id)) continue;
    if (!state.selectedStreams.has(item.stream)) continue;
    if (item.first_date > date || item.last_date >= date) continue;
    const prev = missing.get(item.source_id);
    if (!prev || item.last_date > prev.last_date) {
      missing.set(item.source_id, { source_id: item.source_id, last_date: item.last_date });
    }
  }
  return [...missing.values()].sort((a, b) => a.source_id.localeCompare(b.source_id));
}

function scenarioLabelForDate(date = state.selectedDate) {
  if (state.dateRecordLoading.has(date)) return "loading";
  if (state.dateRecordErrors.has(date)) return "partial load";
  const rows = selectedDateSummaryRows(date);
  const scenarios = new Set(rows.map((row) => row.scenario).filter(Boolean));
  const warnings = state.manifest?.data_quality?.date_warnings?.[date] || [];
  if (missingSourcesForDate(date).length) return "partial coverage";
  if (warnings.some((w) => w.severity === "high")) return "data warning";
  if (scenarios.has("actual") && scenarios.has("forecast")) return "mixed";
  if (scenarios.has("forecast")) return "forecast";
  if (scenarios.has("actual")) return "actual";
  return "no coverage";
}

function renderCoverageNotice(date = state.selectedDate) {
  if (!els.coverageNotice) return;
  const warnings = state.manifest?.data_quality?.date_warnings?.[date] || [];
  const missingSources = missingSourcesForDate(date);
  const rows = selectedDateSummaryRows(date);
  const low = rows
    .filter((row) => row.location_confidence === "low")
    .reduce((sum, row) => sum + Number(row.kbbl_d || 0), 0);
  const unmapped = rows
    .filter((row) => row.location_confidence === "unmapped")
    .reduce((sum, row) => sum + Number(row.kbbl_d || 0), 0);
  const sources = new Set(rows.map((row) => row.source_id));
  const messages = [];
  const forecast = state.search
    ? filteredRecords(date).filter((r) => r.scenario === "forecast").reduce((sum, r) => sum + r.volume_kbbl_d, 0)
    : rows.filter((r) => r.scenario === "forecast").reduce((sum, r) => sum + Number(r.kbbl_d || 0), 0);
  if (forecast > 0) messages.push(`Includes ${kbbl(forecast)} of legacy forecast data. Refresh the app to load official actuals.`);
  if (state.dateRecordLoading.has(date)) messages.push("Loading this month's facility records… Totals are incomplete until loading finishes.");
  if (state.dateRecordErrors.has(date)) messages.push("Monthly facility records could not load. Open Data status to retry; the displayed total is incomplete.");
  if ((state.selectedStreams.has("Mined bitumen gross") || state.selectedStreams.has("In-situ bitumen")) && state.selectedStreams.has("Synthetic crude oil")) {
    messages.push("Gross stream sum: bitumen and upgraded synthetic crude overlap. This is not net oil supply.");
  }
  if (["Propane", "Butane"].some((product) => state.selectedStreams.has(`${product} mix`) && state.selectedStreams.has(`${product} spec`))) {
    messages.push("NGL mix and spec volumes can overlap across processing stages.");
  }
  if (warnings.length) {
    const extraWarnings = warnings.filter((w) => !missingSources.some((m) => m.source_id === w.source_id) || !/has no .+ data for/.test(w.message));
    messages.push(...extraWarnings.slice(0, 2).map((w) => Object.entries(SOURCE_SHORT).reduce((message, [id, name]) => message.replaceAll(id, name), w.message)));
  }
  if (missingSources.length) {
    const names = missingSources
      .map((m) => `${SOURCE_SHORT[m.source_id] || m.source_id} (last ${m.last_date.slice(0, 7)})`)
      .join(", ");
    messages.push(`Partial month: actual data is missing from ${names}. Do not compare this total with fully reported months.`);
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
  const isWarning = warnings.length > 0 || missingSources.length > 0 || state.dateRecordErrors.has(date);
  const title = state.dateRecordErrors.has(date) ? "Incomplete data load" : missingSources.length ? "Partial source coverage" : isWarning ? "Data quality warning" : `Coverage note · ${sources.size || 0} source${sources.size === 1 ? "" : "s"}`;
  els.coverageNotice.className = `coverage-notice${isWarning ? "" : " info"}`;
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
  clearHoverFireImpact();
  const { byAsset } = aggregated || aggregateForDate();
  const points = [...byAsset.values()].filter(
    ({ asset, kbbl: v }) => asset.latitude != null && asset.longitude != null && v > 0
  );
  const visiblePoints = points.filter((point) => legendVisible(pointLegendKey(point)));

  if (state.map && state.markerLayer && window.L) {
    state.markerLayer.clearLayers();
    state.selectedProductionMarker = null;
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
      if (isSelected) state.selectedProductionMarker = marker;
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
        state.selectedProductionMarker?.setStyle({ weight: 1.4, color: "#ffffff", fillOpacity: .65 });
        state.selectedAssetId = point.asset.asset_id;
        state.selectedProductionMarker = marker;
        marker.setStyle({ weight: 3, color: "#101820", fillOpacity: .9 });
        renderDetails(aggregated);
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
  const circles = points.map(({ asset, kbbl: value, streams }) => {
    const [x, y] = project(asset.latitude, asset.longitude);
    const color = streamColor(
      [...(streams?.entries() || [])].sort((a, b) => b[1] - a[1])[0]?.[0]
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
  const reporting = productionReportingForDate(state.selectedDate, total);
  els.totalShown.textContent = reporting.reportedTotal === null ? "--" : `${kbbl(total)}${reporting.status === "complete" ? "" : " · partial"}`;
  els.totalShown.title = reporting.note;
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
  if (!selected && state.selectedAssetId) {
    const asset = state.assetById.get(state.selectedAssetId);
    if (asset) {
      const reported = matchingReportedRecords().filter(record => record.asset_id === asset.asset_id);
      if (reported.length) {
        selected = { asset, kbbl: reported.reduce((sum, record) => sum + record.volume_kbbl_d, 0),
          sources: new Set(reported.map(record => record.source_id)), scenarios: new Set(["actual"]),
          streams: new Map(), records: reported };
        for (const record of reported) selected.streams.set(record.stream, (selected.streams.get(record.stream) || 0) + record.volume_kbbl_d);
      } else {
        els.detailTitle.textContent = asset.display_name;
        els.detailSubtitle.textContent = "No reported observation for this asset at the selected date.";
        els.detailVolume.textContent = "--";
        els.detailSource.textContent = SOURCE_SHORT[asset.source_id] || asset.source_id;
        els.detailStatus.textContent = "Unavailable · missing records are not zero";
        if (els.detailLocationQuality) els.detailLocationQuality.textContent = locationQualityText(asset);
        if (els.streamBreakdown) els.streamBreakdown.innerHTML = '<p class="empty">Production is unavailable for this month.</p>';
        if (els.fireRiskSection) els.fireRiskSection.hidden = true;
        renderTopAssets(aggregated);
        return;
      }
    }
  }
  if (!selected && !state.selectedAssetId) selected = [...byAsset.values()].sort((a, b) => b.kbbl - a.kbbl)[0] || null;

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

    return `<div class="top-asset-row${isSelected ? " selected" : ""}" data-id="${escapeHtml(String(asset.asset_id))}">
      <span class="top-rank">${i + 1}</span>
      <i class="top-swatch" style="background:${color}"></i>
      <span class="top-name">${escapeHtml(asset.display_name)}</span>
      <span class="quality-pill ${quality.className}">${escapeHtml(quality.short)}</span>
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
  const incomplete = Boolean(state.albertaFireError || state.bcFireError || (legendVisible("fire-zone") && state.wildfireError));
  if (incomplete && risk.level === "none") {
    els.fireRiskBadge.textContent = "Incomplete data";
    els.fireRiskBadge.className = "risk-badge moderate";
    els.fireDistDisplay.textContent = "Some fire feeds are unavailable";
    els.fireVolAtRisk.textContent = "Unknown";
    return;
  }
  const labelMap = { high: "Within 75 km", moderate: "Within 200 km", none: "No nearby reports" };
  const classMap = { high: "risk-badge high", moderate: "risk-badge moderate", none: "risk-badge clear" };

  els.fireRiskBadge.textContent = labelMap[risk.level];
  els.fireRiskBadge.className = classMap[risk.level];
  els.fireDistDisplay.textContent = risk.level !== "none"
    ? `${risk.distanceKm.toLocaleString()} km to nearest fire`
    : "No active fires within 200 km";

  // Match the active date, source, stream, location-confidence, and search filters.
  const atRiskVol = filteredRecords(state.selectedDate)
    .filter((r) => r.asset_id === asset.asset_id)
    .reduce((s, r) => s + r.volume_kbbl_d, 0);
  els.fireVolAtRisk.textContent = risk.level !== "none"
    ? `${kbbl(atRiskVol)} within screening radius${incomplete ? " (partial feeds)" : ""}`
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
    const reportingCache = new Map();
    const catalog = productionReportingCatalog();
    const groups = productionGroupsForActiveFilters(catalog.catalog);
    for (const date of state.dates) {
      let total;
      const hasOnDemandFile = Boolean(state.manifest?.monthly_record_files?.[date]);
      // Names are absent from manifest totals. A search cannot estimate an
      // unloaded month from only its base records without understating it.
      if (hasOnDemandFile && !state.dateRecordCache.has(date) && state.search) {
        cache.set(date, null);
        reportingCache.set(date, { status: "unloaded", note: "Search total not loaded; select this month to load records." });
        continue;
      }
      // Manifest summaries already include both base and on-demand records.
      if (hasOnDemandFile && !state.dateRecordCache.has(date) && !state.search) {
        total = selectedDateSummaryRows(date).reduce((sum, row) => sum + Number(row.kbbl_d || 0), 0);
      }
      if (!Number.isFinite(total)) {
        const { byAsset } = aggregateForDate(date);
        total = [...byAsset.values()].reduce((s, p) => s + p.kbbl, 0);
      }
      const point = productionReportingForDate(date, total, catalog, groups);
      cache.set(date, point.reportedTotal);
      reportingCache.set(date, point);
    }
    state.timelineCache = cache;
    state.timelineReportingCache = reportingCache;
  }
  const rows = state.dates.map((date) => ({ date, total: state.timelineCache.get(date) ?? null,
    reporting: state.timelineReportingCache?.get(date) || { status: "unverified", note: "Reporting coverage unavailable." } }));
  const max = Math.max(...rows.map((r) => r.total), 1);
  const selectedIndex = rows.findIndex((r) => r.date === state.selectedDate);
  const windowStart = Math.max(0, selectedIndex - 30);
  const visible = rows.slice(windowStart, Math.min(rows.length, windowStart + 72));
  if (els.timelineLabel) {
    const unloaded = visible.filter(row => row.reporting.status === "unloaded").length;
    const partial = visible.filter(row => ["partial", "unverified"].includes(row.reporting.status) && row.total !== null).length;
    const missing = visible.filter(row => row.reporting.status !== "unloaded" && row.total === null).length;
    els.timelineLabel.textContent = `${visible.length} months in view${unloaded ? ` · ${unloaded} search totals not loaded; select a month to load` : ''}${partial ? ` · ${partial} partial reporting` : ''}${missing ? ` · ${missing} without reported observations` : ''}`;
  }
  if (els.timelineBars) {
    els.timelineBars.innerHTML = visible.map((row) => {
      const height = Math.max(3, (row.total / max) * 72);
      const sel = row.date === state.selectedDate;
      const unavailable = row.total === null;
      const status = row.reporting.status;
      const partial = status === "partial" || status === "unverified";
      const amount = unavailable ? (status === "unloaded" ? "search total not loaded; select to load" : "No reported observation; production unavailable")
        : `${kbbl(row.total)}${partial ? " reported subtotal · partial reporting" : " reported production"}`;
      const label = `${dateLabel(row.date)} — ${amount}. ${row.reporting.note || ""}`;
      const cssStatus = unavailable ? (status === "unloaded" ? "unloaded" : "missing") : partial ? "partial" : "";
      return `<button class="timeline-bar ${sel ? "selected" : ""} ${cssStatus}" style="height:${unavailable ? 7 : height}px" title="${escapeHtml(label)}" data-date="${row.date}" aria-label="${escapeHtml(label)}"></button>`;
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

function refineryUnitSummaryHtml(summary, limit = 99) {
  const rows = Array.isArray(summary) ? [...summary] : [];
  if (!rows.length) return "";
  // Sort by count desc (then name) so the most significant unit types lead; show
  // up to `limit` and indicate any remainder. (Previously sliced to 8 with the raw
  // alphabetical order, which hid late-alphabet units like Vacuum Distillation.)
  rows.sort((a, b) => (b.count || 0) - (a.count || 0) ||
    String(a.group || "").localeCompare(String(b.group || "")));
  const shown = rows.slice(0, limit);
  const extra = rows.length - shown.length;
  return `<div class="refinery-unit-summary">` +
    shown.map((item) =>
      `<span>${escapeHtml(item.group || "Unit")} <strong>${formatNumber(item.count || 0)}</strong></span>`
    ).join("") +
    (extra > 0 ? `<span class="rus-more">+${extra} more</span>` : "") +
  `</div>`;
}

function refineryCapacityProvenanceHtml(p) {
  const source = safeHttpUrl(p.capacity_source_url);
  const statusSource = safeHttpUrl(p.status_source_url);
  return (source ? `<p class="rt-sub">Capacity: <a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">${escapeHtml(p.capacity_source_name || "Operator source")}</a> · checked ${escapeHtml(p.capacity_checked_at || "")}<br>${escapeHtml(p.capacity_basis_note || "")} Unit rows retain their original source basis.</p>` : "") +
    (p.capacity_review_note ? `<p class="data-status-warning">${escapeHtml(p.capacity_review_note)}</p>` : "") +
    (statusSource ? `<p class="rt-sub">Status source: <a href="${escapeHtml(statusSource)}" target="_blank" rel="noopener noreferrer">${escapeHtml(p.status_source_name || "Published status")}</a> · as of ${escapeHtml(p.status_effective_as_of || "date unavailable")}</p>` : "") +
    (p.status_review_note ? `<p class="data-status-warning">${escapeHtml(p.status_review_note)}</p>` : "");
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
    refineryCapacityProvenanceHtml(p) +
    `${units.length ? refineryUnitSummaryHtml(p.refinery_unit_summary, 12) : ""}` +
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
    refineryCapacityProvenanceHtml(p) +
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

// WILDFIRE  —  CWFIS live feed (WFS hotspots_last24hrs, Western Canada bbox)
// ============================================================

// CWFIS GeoServer WFS — current 24-hour layer; CQL filter keeps only
// points inside Western Canada (lat 49–72, lon –141 to –94).
// The WFS geometry is in a projected CRS; real coords are in properties.lat/lon.
const CWFIS_URL =
  "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wfs" +
  "?service=WFS&version=1.1.0&request=GetFeature" +
  "&typeName=public:hotspots_last24hrs" +
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

const ECCC_PROGNOS_URL =
  "https://api.weather.gc.ca/collections/prognos-rdps-realtime/items";
const OPEN_METEO_FORECAST_URL =
  "https://api.open-meteo.com/v1/forecast";

function liveUrl(url) {
  const joiner = url.includes("?") ? "&" : "?";
  return `${url}${joiner}_=${Date.now()}`;
}

async function fetchJsonLive(url, options = {}) {
  return requestJson(liveUrl(url), {
    mode: "cors",
    cache: "no-store",
    timeoutMs: 20000,
    ...options,
  });
}

function isoNoMillis(date) {
  return date.toISOString().replace(/\.\d{3}Z$/, "Z");
}

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
// e.g. "53° 18.5410" → 53.309017,  "-112° 56.7841" → -112.946402
function parseDDM(str) {
  if (!str) return NaN;
  const m = String(str).match(/^(-?\d+)[°\s]+(\d+\.?\d*)$/);
  if (!m) return NaN;
  const deg = Number(m[1]);
  const min = Number(m[2]);
  if (min >= 60) return NaN;
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
  const geometry = feature?.geometry;
  const polygons = geometry?.type === "Polygon" ? [geometry.coordinates] : geometry?.type === "MultiPolygon" ? geometry.coordinates : [];
  return polygons.some((rings) => rings.length && pointInRing(lat, lon, rings[0]) && !rings.slice(1).some((hole) => pointInRing(lat, lon, hole)));
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
  // Measure to segment interiors too; using only vertices overstates distance
  // along long project boundaries. Local tangent-plane screening approximation.
  const cosLat = Math.cos(lat * Math.PI / 180);
  for (const ring of geometryRings(feature.geometry)) {
    for (let i = 1; i < ring.length; i++) {
      const a = ring[i - 1], b = ring[i];
      const ax = (a[0] - lon) * cosLat, ay = a[1] - lat;
      const dx = (b[0] - a[0]) * cosLat, dy = b[1] - a[1];
      const length2 = dx * dx + dy * dy;
      const t = length2 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / length2)) : 0;
      best = Math.min(best, haversineKm(lat, lon, a[1] + t * (b[1] - a[1]), a[0] + t * (b[0] - a[0])));
    }
  }
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
    const raw = requireFeatureCollection(await fetchJsonLive(CWFIS_URL));
    if (raw.features.length >= 2000) throw new Error("Hotspot response reached its feature limit; coverage cannot be confirmed");

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

const FIRE_CONTEXT_ITEMS = [
  {
    key: "windArrow",
    label: "Wind arrow on hover",
    detail: "Live ECCC RDPS wind at the hovered fire",
    color: "#0f172a",
  },
  {
    key: "downwindCorridor",
    label: "Downwind corridor on hover",
    detail: "Draw only for the hovered fire",
    color: "#b45309",
  },
  {
    key: "exposedProduction",
    label: "Exposed production on hover",
    detail: "Highlight assets inside the hovered corridor",
    color: "#d97706",
  },
];

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
  html += `<div class="fire-menu-section">Hover impact</div>`;
  for (const item of FIRE_CONTEXT_ITEMS) {
    const checked = state.fireImpactSettings?.[item.key] !== false;
    html += `
      <label class="fire-option fire-context-option" title="${escapeHtml(item.detail)}">
        <input type="checkbox" data-fire-context-key="${escapeHtml(item.key)}" ${checked ? "checked" : ""} />
        <span class="fire-dot-swatch fire-context-swatch" style="background:${item.color}"></span>
        <span class="fire-option-text">
          <strong>${escapeHtml(item.label)}</strong>
          <em>${escapeHtml(item.detail)}</em>
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
  const contextInput = event.target.closest("input[data-fire-context-key]");
  if (contextInput) {
    const key = contextInput.dataset.fireContextKey;
    if (key && Object.prototype.hasOwnProperty.call(state.fireImpactSettings, key)) {
      state.fireImpactSettings[key] = contextInput.checked;
      clearHoverFireImpact();
      buildFireMenu();
    }
    return;
  }

  const input = event.target.closest("input[data-fire-key]");
  if (!input) return;
  const key = input.dataset.fireKey;
  if (input.checked) state.hiddenLegendKeys.delete(key);
  else state.hiddenLegendKeys.add(key);
  clearHoverFireImpact();
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
  clearHoverFireImpact();
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

function fireImpactActive() {
  const settings = state.fireImpactSettings || {};
  return Boolean(settings.windArrow || settings.downwindCorridor || settings.exposedProduction);
}

function clearHoverFireImpact() {
  if (state.hoverFireImpactAbort) {
    state.hoverFireImpactAbort.abort();
    state.hoverFireImpactAbort = null;
  }
  if (state.hoverFireImpactLayer && state.map) {
    state.map.removeLayer(state.hoverFireImpactLayer);
  }
  if (state.hoverFireTooltipLayer && state.hoverFireBaseTooltipHtml) {
    try {
      state.hoverFireTooltipLayer.setTooltipContent(state.hoverFireBaseTooltipHtml);
    } catch (_) {
      // Layer may have been removed during a map refresh.
    }
  }
  state.hoverFireImpactLayer = null;
  state.hoverFireImpactToken = null;
  state.hoverFireTooltipLayer = null;
  state.hoverFireBaseTooltipHtml = "";
}

function normalizeBearing(value) {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return ((n % 360) + 360) % 360;
}

function compassDirection(degrees) {
  const bearing = normalizeBearing(degrees);
  if (bearing == null) return "--";
  const labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return labels[Math.round(bearing / 45) % 8];
}

function angularDifference(a, b) {
  const diff = Math.abs(normalizeBearing(a) - normalizeBearing(b));
  return Math.min(diff, 360 - diff);
}

function bearingDegrees(lat1, lon1, lat2, lon2) {
  const d2r = Math.PI / 180;
  const y = Math.sin((lon2 - lon1) * d2r) * Math.cos(lat2 * d2r);
  const x =
    Math.cos(lat1 * d2r) * Math.sin(lat2 * d2r) -
    Math.sin(lat1 * d2r) * Math.cos(lat2 * d2r) * Math.cos((lon2 - lon1) * d2r);
  return normalizeBearing(Math.atan2(y, x) * 180 / Math.PI);
}

function destinationPoint(lat, lon, bearing, distanceKm) {
  const R = 6371;
  const d2r = Math.PI / 180;
  const r2d = 180 / Math.PI;
  const brng = bearing * d2r;
  const phi1 = lat * d2r;
  const lambda1 = lon * d2r;
  const delta = distanceKm / R;
  const phi2 = Math.asin(
    Math.sin(phi1) * Math.cos(delta) +
    Math.cos(phi1) * Math.sin(delta) * Math.cos(brng)
  );
  const lambda2 = lambda1 + Math.atan2(
    Math.sin(brng) * Math.sin(delta) * Math.cos(phi1),
    Math.cos(delta) - Math.sin(phi1) * Math.sin(phi2)
  );
  return { lat: phi2 * r2d, lon: ((lambda2 * r2d + 540) % 360) - 180 };
}

function fireSizeHa(feature) {
  const p = feature?.properties || {};
  const value = Number(p.AREA_ESTIMATE ?? p.CURRENT_SIZE ?? p.Hectares);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function fireDisplayName(feature) {
  const p = feature?.properties || {};
  if (p.LABEL) return String(p.LABEL);
  if (p.INCIDENT_NAME && p.INCIDENT_NAME !== p.FIRE_NUMBER) {
    return `${p.FIRE_NUMBER || "BC fire"} - ${p.INCIDENT_NAME}`;
  }
  if (p.FIRE_NUMBER) return String(p.FIRE_NUMBER);
  return "Fire hotspot";
}

function corridorLengthKm(feature, weather) {
  const speed = Number(weather?.speedKmh) || 0;
  const size = fireSizeHa(feature);
  const p = feature?.properties || {};
  const status = String(p.FIRE_STATUS || "").toLowerCase();
  let length = 55 + speed * 2.6;
  if (size > 0) length += Math.min(55, Math.log10(size + 10) * 14);
  if (status.includes("out of control")) length += 24;
  if (status.includes("under control")) length -= 18;
  if (p.FIRE_OF_NOTE_IND === "Y") length += 18;
  const score = fireScore(feature);
  if (score != null) length += Math.min(35, score * 0.45);
  return Math.max(45, Math.min(220, length));
}

function corridorHalfAngle(weather) {
  const speed = Number(weather?.speedKmh) || 0;
  if (speed >= 35) return 20;
  if (speed >= 20) return 24;
  if (speed >= 10) return 29;
  return 34;
}

function corridorLatLngs(center, bearing, lengthKm, halfAngleDeg) {
  const distances = [
    Math.max(6, lengthKm * 0.12),
    lengthKm * 0.35,
    lengthKm * 0.68,
    lengthKm,
  ];
  const spread = Math.tan(halfAngleDeg * Math.PI / 180);
  const left = [];
  const right = [];
  for (const distance of distances) {
    const mid = destinationPoint(center.lat, center.lon, bearing, distance);
    const halfWidth = Math.min(60, Math.max(4, distance * spread));
    const l = destinationPoint(mid.lat, mid.lon, bearing - 90, halfWidth);
    const r = destinationPoint(mid.lat, mid.lon, bearing + 90, halfWidth);
    left.push([l.lat, l.lon]);
    right.push([r.lat, r.lon]);
  }
  return [[center.lat, center.lon], ...left, ...right.reverse(), [center.lat, center.lon]];
}

function ecccWindUrl(center, variable, radiusDeg, now = new Date()) {
  const from = new Date(now.getTime() - 60 * 60 * 1000);
  const to = new Date(now.getTime() + 3 * 60 * 60 * 1000);
  const params = new URLSearchParams({
    f: "json",
    bbox: [
      (center.lon - radiusDeg).toFixed(4),
      (center.lat - radiusDeg).toFixed(4),
      (center.lon + radiusDeg).toFixed(4),
      (center.lat + radiusDeg).toFixed(4),
    ].join(","),
    variable,
    datetime: `${isoNoMillis(from)}/${isoNoMillis(to)}`,
    limit: "700",
  });
  return `${ECCC_PROGNOS_URL}?${params.toString()}`;
}

function weatherRecords(features, variable, center) {
  return (features || [])
    .map((feature) => {
      const p = feature.properties || {};
      if (p.variable !== variable) return null;
      if (p.forecast_value == null || p.forecast_value === "") return null;
      const value = Number(p.forecast_value);
      const coords = feature.geometry?.coordinates || [];
      const lon = Number(coords[0]);
      const lat = Number(coords[1]);
      if (coords[0] == null || coords[1] == null || Math.abs(lon) > 180 || Math.abs(lat) > 90 || (variable === "WindDir" && (value < 0 || value > 360))) return null;
      const forecastMs = Date.parse(p.forecast_datetime);
      const referenceMs = Date.parse(p.reference_datetime);
      if (
        !Number.isFinite(value) ||
        !Number.isFinite(lat) ||
        !Number.isFinite(lon) ||
        !Number.isFinite(forecastMs) ||
        !Number.isFinite(referenceMs)
      ) return null;
      return {
        value,
        unit: p.unit || "",
        stationId: p.prognos_station_id || p.ade_id || "",
        stationName: p.ade_id || p.prognos_station_id || "ECCC station",
        lat,
        lon,
        distanceKm: haversineKm(center.lat, center.lon, lat, lon),
        forecastMs,
        referenceMs,
      };
    })
    .filter(Boolean);
}

function selectWindPair(dirFeatures, speedFeatures, center, now = new Date()) {
  const dirs = weatherRecords(dirFeatures, "WindDir", center);
  const speeds = weatherRecords(speedFeatures, "WindSpeed", center);
  if (!dirs.length || !speeds.length) return null;

  const speedExact = new Map();
  for (const speed of speeds) {
    speedExact.set(`${speed.stationId}|${speed.forecastMs}|${speed.referenceMs}`, speed);
  }

  const nowMs = now.getTime();
  let best = null;
  for (const dir of dirs) {
    let speed = speedExact.get(`${dir.stationId}|${dir.forecastMs}|${dir.referenceMs}`);
    if (!speed) continue;
    if (!dir.stationId || speed.value < 0 || !["km/h", "km h-1", "m/s", "m s-1"].includes(speed.unit)) continue;

    const forecastDeltaH = Math.abs(dir.forecastMs - nowMs) / 36e5;
    const refAgeH = Math.max(0, (nowMs - Math.max(dir.referenceMs, speed.referenceMs)) / 36e5);
    if (forecastDeltaH > 4 || refAgeH > 18) continue;
    const distanceKm = Math.min(dir.distanceKm, speed.distanceKm);
    const score =
      forecastDeltaH * 80 +
      refAgeH * 4 +
      distanceKm * 1.15 +
      Math.abs(dir.referenceMs - speed.referenceMs) / 36e5 * 4;

    const candidate = { dir, speed, score, forecastDeltaH, refAgeH, distanceKm };
    if (!best || candidate.score < best.score) best = candidate;
  }

  if (!best) return null;
  return {
    directionDeg: normalizeBearing(best.dir.value),
    speedKmh: /^(m\/s|m s-1)$/.test(best.speed.unit) ? Number(best.speed.value) * 3.6 : Number(best.speed.value),
    stationName: best.dir.stationName,
    stationDistanceKm: Math.round(best.distanceKm),
    validTime: new Date(best.dir.forecastMs),
    referenceTime: new Date(Math.max(best.dir.referenceMs, best.speed.referenceMs)),
    source: "ECCC RDPS live forecast",
  };
}

async function fetchWeatherFeatures(url, signal) {
  const features = [];
  const origin = new URL(url).origin;
  for (let page = 0; page < 8; page++) {
    const data = requireFeatureCollection(await fetchJsonLive(url, { signal }));
    features.push(...data.features);
    const next = data.links?.find((link) => link.rel === "next")?.href;
    if (!next) {
      if (Number.isFinite(data.numberMatched) && features.length < data.numberMatched) throw new Error("Incomplete wind forecast response");
      return features;
    }
    const nextUrl = new URL(next, url);
    if (nextUrl.origin !== origin) throw new Error("Unexpected weather pagination origin");
    url = nextUrl.href;
  }
  throw new Error("Wind forecast exceeded the paging limit");
}

async function fetchLiveFireWind(center, signal) {
  const now = new Date();
  try {
    for (const radius of [1.25, 2.5, 4]) {
      const [dirRaw, speedRaw] = await Promise.all([
        fetchWeatherFeatures(ecccWindUrl(center, "WindDir", radius, now), signal),
        fetchWeatherFeatures(ecccWindUrl(center, "WindSpeed", radius, now), signal),
      ]);
      const pair = selectWindPair(dirRaw, speedRaw, center, now);
      if (pair) return pair;
    }
  } catch (err) {
    if (err?.name === "AbortError") throw err;
  }
  return fetchOpenMeteoWind(center, signal);
}

async function fetchOpenMeteoWind(center, signal) {
  const params = new URLSearchParams({
    latitude: center.lat.toFixed(5),
    longitude: center.lon.toFixed(5),
    current: "wind_speed_10m,wind_direction_10m,wind_gusts_10m,relative_humidity_2m,precipitation",
    wind_speed_unit: "kmh",
    timezone: "UTC",
    forecast_days: "1",
  });
  const raw = await fetchJsonLive(`${OPEN_METEO_FORECAST_URL}?${params.toString()}`, { signal });
  const current = raw.current || {};
  const direction = normalizeBearing(current.wind_direction_10m);
  const speed = current.wind_speed_10m == null ? NaN : Number(current.wind_speed_10m);
  const validTime = current.time ? new Date(`${current.time.replace(" ", "T")}Z`) : null;
  const ageH = validTime instanceof Date && !Number.isNaN(validTime.getTime())
    ? Math.abs(Date.now() - validTime.getTime()) / 36e5
    : Infinity;
  if (direction == null || !Number.isFinite(speed) || ageH > 4) return null;
  return {
    directionDeg: direction,
    speedKmh: speed,
    gustKmh: Number(current.wind_gusts_10m),
    humidityPct: Number(current.relative_humidity_2m),
    precipitationMm: Number(current.precipitation),
    stationName: "model grid",
    stationDistanceKm: 0,
    validTime,
    referenceTime: validTime,
    source: "Open-Meteo live model fallback",
  };
}

function exposedProductionForFire(feature, center, downwindBearing, lengthKm, halfAngleDeg) {
  const { byAsset } = aggregateForDate();
  const items = [];
  let totalKbbl = 0;

  for (const point of byAsset.values()) {
    const { asset, kbbl: value } = point;
    if (!asset || asset.is_rollup || asset.latitude == null || asset.longitude == null || !Number.isFinite(value) || value <= 0) {
      continue;
    }
    if (!legendVisible(pointLegendKey(point))) continue;
    const distanceKm = haversineKm(center.lat, center.lon, asset.latitude, asset.longitude);
    if (distanceKm > lengthKm) continue;
    const bearing = bearingDegrees(center.lat, center.lon, asset.latitude, asset.longitude);
    const angle = angularDifference(downwindBearing, bearing);
    const direct = geometryContainsPoint(feature, asset.latitude, asset.longitude) || distanceKm <= 8;
    if (!direct && angle > halfAngleDeg) continue;
    totalKbbl += value;
    items.push({ asset, kbbl: value, distanceKm, angle, direct });
  }

  items.sort((a, b) => b.kbbl - a.kbbl);
  return { items, totalKbbl };
}

function formatDateTime(value) {
  if (!(value instanceof Date)) value = value ? new Date(value) : null;
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return "--";
  return value.toLocaleString("en-CA", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fireImpactTooltipHtml(baseHtml, stateName, weather, exposure, errorMessage) {
  if (stateName === "loading") {
    return `${baseHtml}<div class="fire-impact-block loading"><strong>Hover impact</strong><span>Fetching live ECCC wind...</span></div>`;
  }
  if (stateName === "unavailable") {
    return `${baseHtml}<div class="fire-impact-block muted"><strong>Hover impact</strong><span>${escapeHtml(errorMessage || "Live wind is unavailable for this fire location.")}</span></div>`;
  }

  const downwind = normalizeBearing(weather.directionDeg + 180);
  const windFrom = `${compassDirection(weather.directionDeg)} ${Math.round(weather.directionDeg)} deg`;
  const blowingTo = `${compassDirection(downwind)} ${Math.round(downwind)} deg`;
  const exposedCount = exposure?.items?.length || 0;
  const top = (exposure?.items || [])
    .slice(0, 3)
    .map((item) => item.asset.display_name)
    .filter(Boolean)
    .join(", ");
  const topHtml = top ? `<span>Top exposed: ${escapeHtml(top)}</span>` : "";
  const gustHtml = Number.isFinite(weather.gustKmh)
    ? `<span>Gust: ${formatNumber(weather.gustKmh, 0)} km/h</span>`
    : "";
  const humidityHtml = Number.isFinite(weather.humidityPct) || Number.isFinite(weather.precipitationMm)
    ? `<span>RH: ${Number.isFinite(weather.humidityPct) ? formatNumber(weather.humidityPct, 0) + "%" : "--"}; precip: ${Number.isFinite(weather.precipitationMm) ? formatNumber(weather.precipitationMm, 1) + " mm" : "--"}</span>`
    : "";

  return `${baseHtml}<div class="fire-impact-block">` +
    `<strong>Hover impact</strong>` +
    `<span>Wind from ${escapeHtml(windFrom)} at ${formatNumber(weather.speedKmh, 0)} km/h; blowing ${escapeHtml(blowingTo)}</span>` +
    gustHtml +
    humidityHtml +
    `<span>In corridor: ${kbbl(exposure?.totalKbbl || 0)} across ${formatNumber(exposedCount)} asset${exposedCount === 1 ? "" : "s"}</span>` +
    topHtml +
    `<em>${escapeHtml(weather.source)}; valid ${escapeHtml(formatDateTime(weather.validTime))}; station ${escapeHtml(weather.stationName)} (${formatNumber(weather.stationDistanceKm)} km)</em>` +
  `</div>`;
}

function renderHoverFireImpact(feature, center, weather, exposure, lengthKm, halfAngleDeg) {
  if (!state.map || !window.L) return;
  if (state.hoverFireImpactLayer) state.map.removeLayer(state.hoverFireImpactLayer);

  const settings = state.fireImpactSettings || {};
  const group = L.layerGroup();
  const focusRadius = Math.max(13, Math.min(28, 10 + Math.log10(fireSizeHa(feature) + 10) * 4));
  const downwind = weather ? normalizeBearing(weather.directionDeg + 180) : null;

  if (weather && settings.downwindCorridor && downwind != null) {
    L.polygon(corridorLatLngs(center, downwind, lengthKm, halfAngleDeg), {
      className: "fire-impact-corridor",
      color: "#92400e",
      weight: 1.8,
      opacity: 0.52,
      fillColor: "#d97706",
      fillOpacity: 0.13,
      interactive: false,
    }).addTo(group);
  }

  if (weather && settings.exposedProduction && exposure?.items?.length) {
    for (const item of exposure.items.slice(0, 45)) {
      const radius = Math.max(8, Math.min(30, 6 + Math.sqrt(item.kbbl) * 1.65));
      L.circleMarker([item.asset.latitude, item.asset.longitude], {
        className: "fire-impact-asset-ring",
        radius,
        color: item.direct ? "#b91c1c" : "#b45309",
        weight: item.direct ? 2.5 : 2,
        fillColor: item.direct ? "#fee2e2" : "#fef3c7",
        fillOpacity: 0.12,
        opacity: item.direct ? 0.92 : 0.78,
        dashArray: item.direct ? null : "5 4",
        interactive: false,
      }).addTo(group);
    }
  }

  if (weather && settings.windArrow && downwind != null) {
    const arrowDistance = Math.min(34, Math.max(16, lengthKm * 0.18));
    const arrowPoint = destinationPoint(center.lat, center.lon, downwind, arrowDistance);
    L.marker([arrowPoint.lat, arrowPoint.lon], {
      interactive: false,
      icon: L.divIcon({
        className: "wind-arrow-marker",
        iconSize: [34, 34],
        iconAnchor: [17, 17],
        html: `<svg viewBox="0 0 32 32" aria-hidden="true" style="transform:rotate(${downwind}deg)"><path d="M16 3 L24 14 H19 V29 H13 V14 H8 Z"></path></svg>`,
      }),
    }).addTo(group);
  }

  L.circleMarker([center.lat, center.lon], {
    className: "fire-impact-focus",
    radius: focusRadius,
    color: "#111827",
    weight: 2.2,
    fillOpacity: 0,
    opacity: 0.82,
    interactive: false,
  }).addTo(group);

  state.hoverFireImpactLayer = group;
  group.addTo(state.map);
  if (state.albertaFireLayer) state.albertaFireLayer.bringToFront();
  if (state.bcFireLayer) state.bcFireLayer.bringToFront();
  if (state.fireLayer) state.fireLayer.bringToFront();
}

async function handleFireImpactHover(feature, layer, baseTooltipHtml) {
  if (!fireImpactActive()) return;
  const center = geojsonCentroid(feature);
  if (!center) return;

  clearHoverFireImpact();
  const token = Symbol("fire-impact-hover");
  const abort = new AbortController();
  state.hoverFireImpactToken = token;
  state.hoverFireImpactAbort = abort;
  state.hoverFireTooltipLayer = layer;
  state.hoverFireBaseTooltipHtml = baseTooltipHtml;

  layer.setTooltipContent(fireImpactTooltipHtml(baseTooltipHtml, "loading"));
  renderHoverFireImpact(feature, center, null, null, 0, 0);

  try {
    const weather = await fetchLiveFireWind(center, abort.signal);
    if (state.hoverFireImpactToken !== token) return;
    if (!weather) {
      layer.setTooltipContent(fireImpactTooltipHtml(
        baseTooltipHtml,
        "unavailable",
        null,
        null,
        "No current ECCC RDPS wind was found near this fire."
      ));
      renderHoverFireImpact(feature, center, null, null, 0, 0);
      return;
    }
    const downwind = normalizeBearing(weather.directionDeg + 180);
    const lengthKm = corridorLengthKm(feature, weather);
    const halfAngleDeg = corridorHalfAngle(weather);
    const exposure = exposedProductionForFire(feature, center, downwind, lengthKm, halfAngleDeg);
    renderHoverFireImpact(feature, center, weather, exposure, lengthKm, halfAngleDeg);
    layer.setTooltipContent(fireImpactTooltipHtml(baseTooltipHtml, "ready", weather, exposure));
  } catch (err) {
    if (err?.name === "AbortError") return;
    if (state.hoverFireImpactToken !== token) return;
    layer.setTooltipContent(fireImpactTooltipHtml(
      baseTooltipHtml,
      "unavailable",
      null,
      null,
      `Live wind unavailable (${err.message || err}).`
    ));
    renderHoverFireImpact(feature, center, null, null, 0, 0);
  }
}

function bindFireImpactHover(feature, layer, baseTooltipHtml) {
  layer.on("mouseover", () => handleFireImpactHover(feature, layer, baseTooltipHtml));
  layer.on("mouseout", () => clearHoverFireImpact());
}

async function fetchAlbertaFires() {
  if (state.albertaFireLoading) return;
  state.albertaFireLoading = true;
  state.albertaFireError = null;
  try {
    const labels = ["provincial", "mutual aid", "municipal"];
    const results = await Promise.allSettled([ALBERTA_FIRES_URL, ALBERTA_MUTUAL_AID_URL, ALBERTA_MUNICIPAL_URL]
      .map(async (url) => requireFeatureCollection(await fetchJsonLive(url))));
    const failed = results.flatMap((r, i) => r.status === "rejected" ? [labels[i]] : []);
    if (failed.length === results.length) throw new Error("All Alberta sources failed");
    state.albertaFireError = failed.length ? `Partial coverage: ${failed.join(", ")} unavailable` : null;
    const [provRaw, maRaw, munRaw] = results.map((r) => r.status === "fulfilled" ? r.value : { features: [] });

    // Normalize provincial + mutual aid: use LATITUDE/LONGITUDE props over geometry
    // (geometry may be in a projected CRS on some ArcGIS exports).
    const normalize = f => {
      const p = f.properties || {};
      if (p.LATITUDE == null || p.LONGITUDE == null) return null;
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
      const tooltipHtml =
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
        `<em>Alberta Wildfire (official)</em>`;
      layer.bindTooltip(
        tooltipHtml,
        { opacity: 0.96, className: "alberta-fire-tip" }
      );
      bindFireImpactHover(feature, layer, tooltipHtml);
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
    const raw = requireFeatureCollection(await fetchJsonLive(BC_FIRES_URL));
    // Geometry is already valid WGS84 — use as-is, but fall back to
    // LATITUDE/LONGITUDE props if geometry is null for any feature.
    const features = (raw.features || []).map(f => {
      if (f.geometry) return f;
      if (f.properties?.LATITUDE == null || f.properties?.LONGITUDE == null) return null;
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
      const tooltipHtml =
        `<strong>${name}</strong><br>` +
        fonBadge +
        carryoverNote +
        `Status: ${escapeHtml(stageStyle.label)}<br>` +
        `Size: ${haStr}<br>` +
        desc +
        `Started: ${ignStr}<br>` +
        `<em>BC Wildfire Service (official)</em>`;
      layer.bindTooltip(
        tooltipHtml,
        { opacity: 0.96, className: "bc-fire-tip" }
      );
      bindFireImpactHover(feature, layer, tooltipHtml);
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
  if (state.albertaFireError) {
    parts.push(`AB: ${state.albertaFireError}`);
  }
  if (abFeatures.length > 0) {
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
  clearHoverFireImpact();
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
  if (feature?.properties?.fwi == null || feature.properties.fwi === "") return null;
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
      const tooltipHtml =
        `<strong>Fire hotspot</strong> (${escapeHtml(p.agency || "?")})<br>` +
        `${escapeHtml(fwi)}${fuel}<br>` +
        `${escapeHtml(p.sensor || "")}${date ? " - " + date : ""}`;
      layer.bindTooltip(
        `<strong>Fire hotspot</strong> (${escapeHtml(p.agency || "?")})<br>` +
        `${escapeHtml(fwi)}${fuel}<br>` +
        `${escapeHtml(p.sensor || "")}${date ? " · " + date : ""}`,
        { opacity: 0.95, className: "fire-hotspot-tip" }
      );
      bindFireImpactHover(feature, layer, tooltipHtml);
    },
  }).addTo(state.map);
}

// ============================================================
// PIPELINE LAYER — AER Feeder Pipelines + Installations
// Counts and source dates come from the validated AER index.
// Data source: AER Pipeline Spatial Dataset (NAD83 transformed to WGS84)
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
        geometry_confidence: 'Approximate market-area reference',
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
    color: safeCssColor(feature.properties?.color),
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
    const [routes, tariffs] = await Promise.allSettled([
      requestJson(DATA_PATHS.marketPipelines).then(requireFeatureCollection),
      requestJson(DATA_PATHS.marketTariffs),
    ]);
    if (routes.status === "rejected") throw routes.reason;
    state.marketPipelineData = routes.value;
    state.marketTariffData = tariffs.status === "fulfilled" && Array.isArray(tariffs.value?.tariffs) ? tariffs.value : null;
    if (!state.marketTariffData) state.optionalDataWarnings.push("Market tariffs unavailable; routes remain available.");
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
  const safeUrl = safeHttpUrl(url);
  if (!safeUrl) return escapeHtml(label || '');
  return `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label || 'Source')}</a>`;
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

  html += `<div class="pt-sub">Area reference: ${escapeHtml(p.geometry_confidence || 'Approximate market-area location')}. This marker identifies a market hub, not a specific storage facility.</div>`;
  if (p.source_summary) html += `<div class="pt-sub">${escapeHtml(p.source_summary)}</div>`;

  const tariffMeta = state.marketTariffData?.metadata || {};
  if (tariffMeta.last_verified) {
    const stale = tariffMeta.next_known_change && new Date().toISOString().slice(0, 10) >= tariffMeta.next_known_change;
    html += `<div class="pt-sub${stale ? " data-status-warning" : ""}">Tariff snapshot verified ${escapeHtml(tariffMeta.last_verified)}${stale ? " · A scheduled tariff change has passed. Reverify rates before use." : ""}. ${escapeHtml(tariffMeta.freshness_note || "")}</div>`;
  }
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

function pipelineCardRows(rows) {
  return `<div class="pt-route">${rows.map(([label, value]) =>
    `<span class="pt-route-label">${escapeHtml(label)}</span><span class="pt-route-val">${escapeHtml(value)}</span>`
  ).join('')}</div>`;
}

function renderMarketPipelineTooltip(p) {
  const details = p.pipeline_details || {};
  const capacity = Number(details.capacity_kbbl_d);
  const capacityText = Number.isFinite(capacity) && capacity > 0
    ? `${(capacity * 1000).toLocaleString('en-CA', { maximumFractionDigits: 0 })} bbl/d`
    : details.capacity_label || 'Not published';
  const basis = String(details.capacity_basis || 'not_published').replaceAll('_', ' ');
  const capacityTitle = details.capacity_basis === 'multiple_systems' ? 'Published component capacities'
    : ['operating', 'available', 'initial'].includes(details.capacity_basis)
      ? `Published ${basis} capacity` : 'Nameplate / rated capacity';
  const source = safeHttpUrl(details.source_url);
  const inventorySource = safeHttpUrl(details.route_source_url);
  const routeSource = safeHttpUrl(p.geometry_source_url) || inventorySource;
  return `<div class="pipeline-card">` +
    `<div class="pipeline-card-kind">Market access pipeline</div>` +
    `<strong class="pipeline-card-title">${escapeHtml(p.route_name || 'Market access pipeline')}</strong>` +
    `<div class="pt-sub">${escapeHtml(p.operator || 'Operator not published')}</div>` +
    `<div class="pipeline-card-capacity"><span>${escapeHtml(capacityTitle)}</span><strong>${escapeHtml(capacityText)}</strong>` +
    `${details.capacity_basis && details.capacity_basis !== 'not_published' ? `<small>${escapeHtml(basis)}</small>` : ''}</div>` +
    pipelineCardRows([['Product', details.product || p.commodity || 'Not published'], ['Origin', details.origin || 'Not published'], ['Destination', details.destination || 'Not published']]) +
    `${details.capacity_note ? `<div class="pipeline-card-note">${escapeHtml(details.capacity_note)}</div>` : ''}` +
    `${p.status_note ? `<div class="pipeline-card-note">${escapeHtml(p.status_note)}</div>` : ''}` +
    `${p.geometry_note || p.coverage_note ? `<div class="pipeline-card-note">${escapeHtml(p.geometry_note || p.coverage_note)}</div>` : ''}` +
    `${p.network_identity_basis ? `<div class="pipeline-card-note">${escapeHtml(p.network_identity_basis)}</div>` : ''}` +
    `${p.geometry_source_date_note || p.source_as_of ? `<div class="pipeline-card-note">Route source timing: ${escapeHtml(p.geometry_source_date_note || p.source_as_of)}. Source timing does not confirm current operation or ownership of every segment.</div>` : ''}` +
    `<div class="pipeline-card-source">${source ? `<a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">${escapeHtml(details.source_name || 'Capacity source')}</a>` : 'Capacity not provided by the mapped GIS layer'}` +
    `${routeSource && routeSource !== source ? ` · <a href="${escapeHtml(routeSource)}" target="_blank" rel="noopener noreferrer">Displayed geometry source</a>` : ''}` +
    `${inventorySource && inventorySource !== routeSource && inventorySource !== source ? ` · <a href="${escapeHtml(inventorySource)}" target="_blank" rel="noopener noreferrer">Archived inventory reference</a>` : ''}` +
    `${details.as_of ? `<br>Source basis: ${escapeHtml(details.as_of)}` : ''}` +
    `${details.verified_at ? `<br>Reviewed ${escapeHtml(details.verified_at)}` : ''}</div>` +
    `<div class="pipeline-card-footer">${escapeHtml(p.geometry_confidence || 'Route-level map')}. Products describe service, not the current batch. Click or tap to keep this card open.</div></div>`;
}

function bindPipelineCard(layer, html) {
  layer.bindTooltip(html, { sticky: true, opacity: 1, className: 'pipeline-tip pipeline-detail-tip' });
  layer.bindPopup(html, { className: 'pipeline-detail-popup', maxWidth: 380, autoPan: true,
    autoPanPaddingTopLeft: [12, 80], autoPanPaddingBottomRight: [12, 12] });
  layer.on('popupopen', () => layer.closeTooltip());
  layer.on('mouseover', () => { if (layer.isPopupOpen()) layer.closeTooltip(); });
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
  if (lineFeatures.length) {
    state.marketPipelineLineLayer = L.geoJSON({ type: 'FeatureCollection', features: lineFeatures }, {
      style: marketPipelineStyle,
      onEachFeature(feature, layer) {
        bindPipelineCard(layer, renderMarketPipelineTooltip(feature.properties || {}));
      },
    }).addTo(state.map);
  }

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

  if (state.marketPipelineLineLayer) state.marketPipelineLineLayer.bringToBack();
  bringPipelineLayersToBack();
  if (state.formationLayer) state.formationLayer.bringToBack();
}

async function toggleMarketPipelines() {
  const ok = await fetchMarketPipelineData();
  if (!ok) return;
  state.marketPipelineEnabled = state.selectedMarketPipelineIds.size > 0 || state.marketHubsEnabled;
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
  } else if (state.marketPipelineEnabled && (selectedCount || state.marketHubsEnabled)) {
    btn.textContent = selectedCount ? `Market Pipes (${selectedCount})` : 'Market Hubs';
    btn.title = selectedCount
      ? `${selectedCount.toLocaleString('en-CA')} of ${totalCount.toLocaleString('en-CA')} market-access routes selected${state.marketHubsEnabled ? '; market hubs enabled' : ''}`
      : 'Market hubs enabled; no market-access routes selected';
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
  ensureInfrastructureSearch('marketPipelineOptions', 'marketPipelineSearch', 'Find a pipeline or operator', state.marketPipelineSearch);
  let html = '';
  let currentSection = '';
  const sections = new Map();
  for (const feature of marketPipelineFeatures()) {
    if (!infrastructureMatchesSearch(feature.properties, state.marketPipelineSearch)) continue;
    const section = feature.properties?.menu_section || 'Core Market Access Pipelines';
    if (!sections.has(section)) sections.set(section, []);
    sections.get(section).push(feature);
  }
  for (const feature of [...sections.values()].flat()) {
    const p = feature.properties || {};
    const section = p.menu_section || 'Core Market Access Pipelines';
    if (section !== currentSection) {
      currentSection = section;
      html += `<div class="market-pipeline-menu-section">${escapeHtml(section)}</div>`;
    }
    const checked = state.selectedMarketPipelineIds.has(p.route_id);
    const color = safeCssColor(p.color);
    html += `
      <label class="market-pipeline-option" title="${escapeHtml([p.route_name, p.operator, p.flow_role].filter(Boolean).join(' · '))}">
        <input type="checkbox" data-market-pipeline-id="${escapeHtml(p.route_id)}" ${checked ? 'checked' : ''} />
        <span class="market-pipeline-swatch" style="background:${escapeHtml(color)}"></span>
        <span class="market-pipeline-option-text">
          <strong>${escapeHtml(p.route_name || p.route_id)}</strong>
          <em>${escapeHtml(p.operator || p.commodity || '')}</em>
        </span>
      </label>`;
  }
  options.innerHTML = (html || '<div class="infrastructure-search-note">No pipelines match this search.</div>') +
    '<div class="infrastructure-search-note">Search narrows this list. Selected routes remain visible on the map. Route locations and source dates vary; open a line for details.</div>';
  const hubsToggle = document.getElementById('marketHubToggle');
  if (hubsToggle) hubsToggle.checked = state.marketHubsEnabled;
  const hubDescription = document.querySelector?.('#marketPipelineMenu .hub-option em');
  if (hubDescription) hubDescription.textContent = 'Approximate market areas and route nodes';
}

function handleMarketPipelineMenuChange(event) {
  const pipelineInput = event.target.closest('input[data-market-pipeline-id]');
  if (pipelineInput) {
    const id = pipelineInput.dataset.marketPipelineId;
    if (pipelineInput.checked) state.selectedMarketPipelineIds.add(id);
    else state.selectedMarketPipelineIds.delete(id);
    state.marketPipelineEnabled = state.selectedMarketPipelineIds.size > 0 || state.marketHubsEnabled;
    refreshMarketPipelineLayers();
    updateMarketPipelineToggleUI();
    return;
  }

  if (event.target.id === 'marketHubToggle') {
    state.marketHubsEnabled = event.target.checked;
    state.marketPipelineEnabled = state.selectedMarketPipelineIds.size > 0 || state.marketHubsEnabled;
    refreshMarketPipelineLayers();
    updateMarketPipelineToggleUI();
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
  state.marketPipelineEnabled = state.selectedMarketPipelineIds.size > 0 || state.marketHubsEnabled;
  buildMarketPipelineMenu();
  refreshMarketPipelineLayers();
  updateMarketPipelineToggleUI();
}

function refreshMarketPipelineLayers() {
  renderMarketPipelineLayers();
}

// ============================================================
// RAILWAYS LAYER - BTS/FRA NARN + EIA petroleum terminals
// ============================================================

function infrastructureMatchesSearch(props, query) {
  const normalize = (value) => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const tokens = normalize(query).trim().split(/\s+/).filter(Boolean);
  if (!tokens.length) return true;
  const p = props || {};
  const text = normalize([
    p.name, p.reported_name, p.operator, p.reported_operator, p.city, p.state, p.province,
    p.country, p.address, p.facility_id, p.route_name, p.route_id, p.commodity,
    p.search_aliases,
    ...(Array.isArray(p.source_pipeline_names) ? p.source_pipeline_names : []),
    ...(Array.isArray(p.source_operator_names) ? p.source_operator_names : []),
  ].filter(Boolean).join(' '));
  return tokens.every((token) => text.includes(token));
}

function ensureInfrastructureSearch(optionsId, inputId, label, value) {
  const options = document.getElementById(optionsId);
  if (!options || !document.createElement) return;
  let input = document.getElementById(inputId);
  if (!input) {
    const wrapper = document.createElement('div');
    wrapper.className = 'infrastructure-search';
    wrapper.innerHTML = `<label for="${inputId}">${escapeHtml(label)}</label><input id="${inputId}" type="search" placeholder="Name, operator or place" autocomplete="off" />`;
    options.before(wrapper);
    input = document.getElementById(inputId);
  }
  if (input && input.value !== value) input.value = value;
}

function handleInfrastructureSearchInput(event) {
  if (event.target.id === 'marketPipelineSearch') {
    state.marketPipelineSearch = event.target.value;
    buildMarketPipelineMenu();
  } else if (event.target.id === 'railwaySearch') {
    state.railwaySearch = event.target.value;
    buildRailwayMenu();
    clearTimeout(state.railwaySearchTimer);
    state.railwaySearchTimer = setTimeout(renderRailwayLayer, 200);
  }
}

function railwayFeatures() {
  return state.railwayData?.features || [];
}

function selectedRailwayFeatures() {
  return railwayFeatures()
    .filter((feature) => state.selectedRailwayCategories.has(feature.properties?.category))
    .filter((feature) => feature.properties?.feature_kind !== 'rail_line'
      || state.selectedRailwayOwners.has(railLineOwnerMeta(feature.properties).key))
    .filter((feature) => feature.properties?.feature_kind === 'rail_line'
      || infrastructureMatchesSearch(feature.properties, state.railwaySearch));
}

function railwaySelectedCount() {
  return state.selectedRailwayCategories.size;
}

function railwayOwnerColor(owner) {
  if (state.basemapKey === "dark") {
    return RAIL_OWNER_DARK_COLORS[owner.key] || RAIL_OWNER_DARK_COLORS.other;
  }
  return owner.color;
}

function railwayCategoryColor(category) {
  if (state.basemapKey === "dark" && RAIL_TERMINAL_DARK_COLORS[category]) {
    return RAIL_TERMINAL_DARK_COLORS[category];
  }
  return (RAILWAY_CATEGORY_META[category] || RAILWAY_CATEGORY_META["product-terminal"]).color;
}

function railwayStyle(feature) {
  const category = feature.properties?.category || "rail-main";
  const owner = railLineOwnerMeta(feature.properties);
  const dark = state.basemapKey === "dark";
  const zoom = state.map?.getZoom?.() ?? 5;
  const zoomBoost = zoom >= 9 ? 0.8 : zoom >= 7 ? 0.4 : 0;
  const baseWeight = category === "rail-main"
    ? (dark ? 3 : 2.4)
    : (dark ? 2 : 1.6);
  return {
    color: railwayOwnerColor(owner),
    weight: baseWeight + zoomBoost,
    opacity: category === "rail-main" ? (dark ? 0.98 : 0.94) : (dark ? 0.88 : 0.76),
    lineCap: "round",
    lineJoin: "round",
  };
}

function railwayTerminalStyle(feature) {
  const category = feature.properties?.category || "product-terminal";
  const reviewed = feature.properties?.review_status === 'operator_verified';
  return {
    radius: category.endsWith('-storage') ? 5 : category === "crude-rail-terminal" || category === "crude-terminal" ? 4.4 : 3.7,
    color: reviewed ? '#ffffff' : railwayCategoryColor(category),
    weight: reviewed ? 1.15 : 1.6,
    fillColor: railwayCategoryColor(category),
    fillOpacity: reviewed ? 0.9 : 0.3,
    opacity: 0.95,
  };
}

function railwayTerminalMarker(feature, latlng) {
  return L.circleMarker(latlng, railwayTerminalStyle(feature));
}

function refreshRailwayStyles() {
  for (const group of [state.railwayLineLayer, state.railwayLayer]) {
    if (!group) continue;
    group.eachLayer((layer) => {
    const feature = layer.feature;
    if (!feature || typeof layer.setStyle !== "function") return;
    const isLine = feature.properties?.feature_kind === "rail_line"
      || feature.geometry?.type === "LineString"
      || feature.geometry?.type === "MultiLineString";
    layer.setStyle(isLine ? railwayStyle(feature) : railwayTerminalStyle(feature));
    });
  }
}

function railwayTooltipHtml(p) {
  const meta = RAILWAY_CATEGORY_META[p.category] || {};
  const title = p.name || meta.label || "Railway feature";
  if (p.feature_kind !== 'rail_line') return terminalCardHtml(p);
  const rows = [
    ["Type", p.category_label || meta.label],
    ["Status", p.status],
    ["Owner", p.owner || p.operator],
    ["Source segments", p.segment_count ? formatNumber(p.segment_count, 0) : ""],
    ["Trackage rights", p.trackage_rights],
    ["Transport", p.modes || p.rail_connection],
    ["Subdivision", p.subdivision],
    ["Division", p.division],
    ["Location", [p.city, p.state || p.country].filter(Boolean).join(", ")],
    ["Commodity", p.commodity],
    ["Facility", p.facility_type],
    ["Scope", p.facility_scope],
    ["Location quality", p.location_confidence],
    ["Verified", p.last_verified],
    ["Source", p.source],
  ]
    .filter(([, value]) => value)
    .map(([label, value]) => `<span class="pt-route-label">${escapeHtml(label)}</span><span class="pt-route-val">${escapeHtml(String(value))}</span>`)
    .join("");
  return (
    `<div>` +
    `<strong>${escapeHtml(title)}</strong>` +
    `${meta.detail ? `<div class="pt-sub">${escapeHtml(meta.detail)}</div>` : ""}` +
    `<div class="pt-route">${rows}</div>` +
    `</div>`
  );
}

function terminalCardHtml(p) {
  const meta = RAILWAY_CATEGORY_META[p.category] || {};
  const reviewLabels = {
    operator_verified: 'Identity reviewed against an official operator source',
    inventory_only: 'Official inventory record; current identity and operating status not independently verified',
    historical_unverified: 'Historical record; current identity and operating status not verified',
  };
  const locationLabels = {
    exact: 'Official facility point; not a surveyed boundary',
    high: 'Facility location from a published source; not a surveyed boundary',
    medium: 'Approximate facility location',
    low: 'Approximate location',
    unknown: 'Location accuracy not specified by source',
  };
  const rows = [
    ['Type', p.facility_type || meta.label || p.category],
    ['Operator', p.operator || 'Not identified in source'],
    ['Location', [p.city, p.state || p.province, p.country].filter(Boolean).join(', ')],
    ['Address', p.address],
    ['Commodity', p.commodity || 'Not identified in source'],
    ['Storage capacity', typeof p.storage_capacity_bbl === 'number' && Number.isFinite(p.storage_capacity_bbl) && p.storage_capacity_bbl >= 0 && p.storage_capacity_note
      ? `${p.storage_capacity_bbl.toLocaleString('en-CA', { maximumFractionDigits: 0 })} bbl` : ''],
    ['Transport', p.modes || p.rail_connection || 'Not specified in source'],
    [p.review_status === 'operator_verified' ? 'Status' : 'Inventory status', p.status || 'Current operating status not verified'],
    ['Pipeline connections', p.pipeline_connections],
    ['Facility ID', p.facility_id],
    ['Source date', p.source_as_of || 'Not published in record'],
    ['Source timing', p.source_date_note],
    ['Coordinate source/check date', p.coordinate_as_of],
    ['Identity reviewed', p.review_status === 'operator_verified' ? (p.reviewed_at || p.last_verified) : ''],
    ['Coordinate record', p.coordinate_source_id],
    ['Location accuracy', p.location_accuracy || locationLabels[p.location_confidence] || p.location_confidence || locationLabels.unknown],
  ].filter(([, value]) => value);
  if (p.reported_name && p.reported_name !== p.name) rows.push(['Inventory name', p.reported_name]);
  if (p.reported_operator && p.reported_operator !== p.operator) rows.push(['Inventory operator', p.reported_operator]);
  const sourceLinks = [
    ['Identity / inventory source', p.source_url],
    ['Coordinate source', p.coordinate_source_url],
  ].flatMap(([label, url]) => {
    const safe = safeHttpUrl(url);
    return safe ? [`<a href="${escapeHtml(safe)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`] : [];
  });
  return `<div class="pipeline-card terminal-card">` +
    `<div class="pipeline-card-kind">${escapeHtml(meta.label || 'Petroleum facility')}</div>` +
    `<strong class="pipeline-card-title">${escapeHtml(p.name || 'Unnamed inventory facility')}</strong>` +
    pipelineCardRows(rows) +
    `<div class="pipeline-card-note">${escapeHtml(reviewLabels[p.review_status] || 'Source record; current identity and operating status not independently verified')}</div>` +
    `${p.location_note ? `<div class="pipeline-card-note">${escapeHtml(p.location_note)}</div>` : ''}` +
    `${p.storage_capacity_note && typeof p.storage_capacity_bbl === 'number' ? `<div class="pipeline-card-note">${escapeHtml(p.storage_capacity_note)}</div>` : ''}` +
    `${p.facility_scope ? `<div class="pipeline-card-note">${escapeHtml(p.facility_scope)}</div>` : ''}` +
    `<div class="pipeline-card-source">${sourceLinks.join(' · ') || escapeHtml(p.source || 'Source link not available')}</div>` +
    `<div class="pipeline-card-footer">Operator ownership does not establish a connection to a particular pipeline. Click or tap to keep this card open.</div></div>`;
}

async function fetchRailwayData() {
  if (state.railwayData) return true;
  if (state.railwayLoading) return false;
  state.railwayLoading = true;
  state.railwayError = null;
  updateRailwayToggleUI();
  updatePipelineStatus("Loading railways and petroleum terminals...");

  try {
    state.railwayData = requireFeatureCollection(await requestJson(DATA_PATHS.railways));
    buildRailwayMenu();
  } catch (err) {
    state.railwayError = err.message || String(err);
    updatePipelineStatus(`Railway data unavailable: ${state.railwayError}`);
    state.railwayLoading = false;
    updateRailwayToggleUI();
    return false;
  }

  state.railwayLoading = false;
  updateRailwayToggleUI();
  updatePipelineStatus("");
  return true;
}

function renderRailwayLayer() {
  if (!state.map || !window.L) return;
  if (state.railwayLayer) {
    state.map.removeLayer(state.railwayLayer);
    state.railwayLayer = null;
  }
  if (!state.railwayEnabled || !state.railwayData?.features?.length || !railwaySelectedCount()) {
    if (state.railwayLineLayer) state.map.removeLayer(state.railwayLineLayer);
    state.railwayLineLayer = null;
    state.railwayLineData = null;
    state.railwayLineSelection = '';
    return;
  }

  const features = selectedRailwayFeatures();
  const lineCategories = [...state.selectedRailwayCategories].filter((key) => RAILWAY_CATEGORY_META[key]?.kind === 'line').sort().join('|');
  const lineOwners = [...state.selectedRailwayOwners].sort().join('|');
  const lineSelection = `${lineCategories}::${lineOwners}`;
  // A facility search changes only point features. Keep the 110,000-segment
  // rail context intact rather than recreating it for every query or locator.
  if (state.railwayLineData !== state.railwayData || state.railwayLineSelection !== lineSelection) {
    if (state.railwayLineLayer) state.map.removeLayer(state.railwayLineLayer);
    state.railwayLineLayer = null;
    const lines = features.filter((feature) => feature.properties?.feature_kind === 'rail_line');
    if (lines.length) {
      state.railwayLineLayer = L.geoJSON({ type: 'FeatureCollection', features: lines }, {
        style: railwayStyle,
        onEachFeature(feature, layer) {
          layer.bindTooltip(railwayTooltipHtml(feature.properties || {}), { sticky: true, opacity: 0.96, className: 'pipeline-tip railway-tip' });
        },
      }).addTo(state.map);
    }
    state.railwayLineData = state.railwayData;
    state.railwayLineSelection = lineSelection;
  }
  const points = features.filter((feature) => feature.properties?.feature_kind !== 'rail_line');
  if (points.length) {
    state.railwayLayer = L.geoJSON({ type: 'FeatureCollection', features: points }, {
      pointToLayer: railwayTerminalMarker,
      onEachFeature(feature, layer) { bindPipelineCard(layer, railwayTooltipHtml(feature.properties || {})); },
    }).addTo(state.map);
  }

  state.railwayLineLayer?.bringToBack?.();
  bringPipelineLayersToBack();
  if (state.formationLayer) state.formationLayer.bringToBack();
}

async function toggleRailways() {
  const ok = await fetchRailwayData();
  if (!ok) return;
  state.railwayEnabled = true;
  setRailwayMenuOpen(!state.railwayMenuOpen);
  renderRailwayLayer();
  updateRailwayToggleUI();
}

function updateRailwayToggleUI() {
  const btn = els.railwayToggle || document.getElementById("railwayToggle");
  if (!btn) return;
  const selectedCount = railwaySelectedCount();
  if (state.railwayLoading) {
    btn.textContent = "Loading...";
    btn.className = "railway-toggle-btn loading";
    btn.setAttribute("aria-expanded", "false");
  } else if (state.railwayEnabled && selectedCount) {
    btn.textContent = `Rail & Storage (${selectedCount})`;
    btn.title = `${selectedCount.toLocaleString("en-CA")} rail, terminal and storage categories selected`;
    btn.className = "railway-toggle-btn active";
    btn.setAttribute("aria-expanded", state.railwayMenuOpen ? "true" : "false");
  } else {
    btn.textContent = "Rail & Storage";
    btn.title = "Rail context, petroleum terminals and storage facilities";
    btn.className = "railway-toggle-btn";
    btn.setAttribute("aria-expanded", state.railwayMenuOpen ? "true" : "false");
  }
}

function setRailwayMenuOpen(open) {
  state.railwayMenuOpen = open;
  const menu = document.getElementById("railwayMenu");
  if (menu) menu.hidden = !open;
  updateRailwayToggleUI();
}

function buildRailwayMenu() {
  const options = document.getElementById("railwayOptions");
  if (!options) return;
  ensureInfrastructureSearch('railwayOptions', 'railwaySearch', 'Find a terminal or storage facility', state.railwaySearch);
  const header = document.querySelector?.('#railwayMenu .railway-menu-header strong');
  if (header) header.textContent = 'Rail, terminals & storage';
  const subtitle = document.querySelector?.('#railwayMenu .railway-menu-header span');
  if (subtitle) subtitle.textContent = 'Source dates vary';
  const sourceNote = document.querySelector?.('#railwayMenu .layer-source-note');
  if (sourceNote) sourceNote.textContent = 'Rail geometry is refreshed weekly. Terminal and storage source dates vary, and facility coverage is incomplete. Minor tracks and private spurs may be missing.';
  const counts = {};
  for (const feature of railwayFeatures().filter((f) => f.properties?.feature_kind === 'rail_line' || infrastructureMatchesSearch(f.properties, state.railwaySearch))) {
    const category = feature.properties?.category;
    if (!category) continue;
    const increment = feature.properties?.feature_kind === "rail_line"
      ? Number(feature.properties?.segment_count) || 1
      : 1;
    counts[category] = (counts[category] || 0) + increment;
  }
  const ownerCounts = new Map();
  for (const feature of railwayFeatures()) {
    if (feature.properties?.feature_kind !== "rail_line") continue;
    const meta = railLineOwnerMeta(feature.properties);
    ownerCounts.set(
      meta.key,
      (ownerCounts.get(meta.key) || 0) + (Number(feature.properties?.segment_count) || 1),
    );
  }
  const ownerLegend = railwayFeatures().length
    ? `
      <div class="railway-owner-legend">
        <strong>Line colour = owning railroad</strong>
        ${RAIL_OWNER_META.map((meta) => {
          const count = ownerCounts.get(meta.key);
          return `
            <label class="railway-owner-item">
              <input type="checkbox" data-railway-owner="${escapeHtml(meta.key)}" ${state.selectedRailwayOwners.has(meta.key) ? 'checked' : ''} />
              <span class="railway-swatch" style="background:${railwayOwnerColor(meta)}"></span>
              <span class="railway-owner-name">${escapeHtml(meta.label)}${count ? ` · ${formatNumber(count, 0)}` : ""}</span>
            </label>`;
        }).join("")}
      </div>`
    : "";
  options.innerHTML = (state.railwaySearch.trim() ? terminalSearchResultsHtml() : '') + Object.entries(RAILWAY_CATEGORY_META)
    .map(([key, meta]) => {
      const checked = state.selectedRailwayCategories.has(key);
      const swatch = meta.kind === "point"
        ? `<span class="railway-dot-swatch" style="background:${railwayCategoryColor(key)}"></span>`
        : `<span class="railway-swatch" style="background:${railwayCategoryColor(key)}"></span>`;
      const count = counts[key] ? ` · ${formatNumber(counts[key], 0)}` : "";
      return `
        <label class="railway-option" title="${escapeHtml(meta.detail)}">
          <input type="checkbox" data-railway-category="${escapeHtml(key)}" ${checked ? "checked" : ""} />
          ${swatch}
          <span class="railway-option-text">
            <strong>${escapeHtml(meta.label)}</strong>
            <em>${escapeHtml(meta.detail)}${escapeHtml(count)}</em>
          </span>
        </label>`;
    })
    .join("") + (state.railwaySearch.trim() ? '' : terminalSearchResultsHtml()) + ownerLegend;
}

function terminalSearchResultsHtml() {
  if (!state.railwaySearch.trim()) return '<div class="infrastructure-search-note">Solid points have an identity reviewed against an operator source. Faint points retain inventory records awaiting current verification. Facility coverage is incomplete; open a point for dates and location accuracy.</div>';
  const matches = railwayFeatures().map((feature, index) => ({ feature, index }))
    .filter(({ feature }) => feature.properties?.feature_kind === 'terminal' && infrastructureMatchesSearch(feature.properties, state.railwaySearch))
    .sort((a, b) => Number(b.feature.properties.review_status === 'operator_verified') - Number(a.feature.properties.review_status === 'operator_verified')
      || String(a.feature.properties.name).localeCompare(String(b.feature.properties.name))
      || String(a.feature.properties.facility_id).localeCompare(String(b.feature.properties.facility_id)));
  return `<div class="infrastructure-search-note" role="status">${matches.length} matching facility records${matches.length > 20 ? ' · first 20 shown' : ''}. Source records may overlap at one site. Search filters facility points; rail context stays visible.</div>` +
    `<div class="terminal-search-results">${matches.slice(0, 20).map(({ feature, index }) => {
      const p = feature.properties;
      return `<button type="button" data-terminal-index="${index}" title="Locate ${escapeHtml(p.name)}"><strong>${escapeHtml(p.name)}</strong><span>${escapeHtml([p.operator, p.city, p.state || p.province, p.country].filter(Boolean).join(' · '))}</span><span>${escapeHtml(p.address || p.facility_id || '')}</span></button>`;
    }).join('')}</div>`;
}

function handleRailwayMenuChange(event) {
  const ownerInput = event.target.closest("input[data-railway-owner]");
  if (ownerInput) {
    const key = ownerInput.dataset.railwayOwner;
    if (!RAIL_OWNER_META.some((meta) => meta.key === key)) return;
    if (ownerInput.checked) state.selectedRailwayOwners.add(key);
    else state.selectedRailwayOwners.delete(key);
    state.railwayEnabled = railwaySelectedCount() > 0;
    renderRailwayLayer();
    updateRailwayToggleUI();
    return;
  }
  const input = event.target.closest("input[data-railway-category]");
  if (!input) return;
  const key = input.dataset.railwayCategory;
  if (input.checked) state.selectedRailwayCategories.add(key);
  else state.selectedRailwayCategories.delete(key);
  state.railwayEnabled = railwaySelectedCount() > 0;
  renderRailwayLayer();
  updateRailwayToggleUI();
}

function handleRailwayMenuClick(event) {
  const facilityButton = event.target.closest('[data-terminal-index]');
  if (facilityButton) {
    const feature = railwayFeatures()[Number(facilityButton.dataset.terminalIndex)];
    if (!feature || feature.geometry?.type !== 'Point') return;
    state.selectedRailwayCategories.add(feature.properties.category);
    state.railwayEnabled = true;
    renderRailwayLayer();
    const [lon, lat] = feature.geometry.coordinates;
    state.map?.setView([lat, lon], Math.max(10, state.map.getZoom?.() || 5));
    state.railwayLayer?.eachLayer((layer) => { if (layer.feature === feature) layer.openPopup?.(); });
    buildRailwayMenu();
    updateRailwayToggleUI();
    setRailwayMenuOpen(false);
    return;
  }
  const action = event.target.closest("[data-railway-action]")?.dataset.railwayAction;
  if (!action) return;
  if (action === "all") {
    Object.keys(RAILWAY_CATEGORY_META).forEach((key) => state.selectedRailwayCategories.add(key));
    state.selectedRailwayOwners = new Set(RAIL_OWNER_META.map((meta) => meta.key));
  } else if (action === "none") {
    state.selectedRailwayCategories.clear();
  } else if (action === "defaults") {
    state.selectedRailwayCategories = new Set(DEFAULT_RAILWAY_CATEGORIES);
    state.selectedRailwayOwners = new Set(RAIL_OWNER_META.map((meta) => meta.key));
  }
  state.railwayEnabled = railwaySelectedCount() > 0;
  buildRailwayMenu();
  renderRailwayLayer();
  updateRailwayToggleUI();
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

function renderPipelineSegmentTooltip(p) {
  const sub   = p.substance || 'Unknown';
  const badge = PIPELINE_SUBSTANCE_BADGE[sub] || '';
  const from  = [p.from_fac, p.from_loc].filter(Boolean).join(' · ') || 'Not published';
  const to    = [p.to_fac,   p.to_loc  ].filter(Boolean).join(' · ') || 'Not published';
  const diam  = p.diameter_mm ? `${p.diameter_mm} mm OD` : '—';
  const maop  = p.maop_kpa ? `${Number(p.maop_kpa).toLocaleString('en-CA')} kPa MAOP` : '';
  const len   = p.length_km ? `${p.length_km} km` : '';
  const h2s   = p.h2s_pct != null && Number.isFinite(Number(p.h2s_pct)) ? `H₂S ${Number(p.h2s_pct).toLocaleString('en-CA', { maximumFractionDigits: 5 })}%` : '';
  const env   = p.environ || '';
  const extras = [maop, len, h2s, env].filter(Boolean).join(' · ');

  const name = p.pipeline_name || `Licence ${p.licence || '—'} · segment ${p.segment_line || p.segment_id || '—'}`;
  return `<div class="pipeline-card">` +
    `<div class="pipeline-card-kind">AER feeder pipeline</div>` +
    `<strong class="pipeline-card-title">${escapeHtml(name)}</strong>` +
    `<div class="pt-sub">${escapeHtml(p.company || 'Operator not published')}</div>` +
    `<div class="pt-sub"><span class="pt-badge ${badge}">${escapeHtml(sub)}</span>${escapeHtml(p.status || '')}</div>` +
    `<div class="pipeline-card-capacity"><span>Nameplate capacity</span><strong>Not published</strong><small>AER's spatial source does not report capacity or a commercial pipeline name.</small></div>` +
    pipelineCardRows([['Product', [...new Set([p.substance, p.substance2, p.substance3].filter(Boolean))].join(' / ') || 'Not published'], ['Origin', from], ['Destination', to]]) +
    `<div class="pipeline-card-note">${escapeHtml(diam)}${extras ? ' · ' + escapeHtml(extras) : ''}</div>` +
    `${p.material ? `<div class="pt-sub">${escapeHtml(p.material)}${p.joint ? ' · ' + escapeHtml(p.joint) : ''}</div>` : ''}` +
    `<div class="pipeline-card-source"><a href="https://www.aer.ca/data/pipeline/Pipelines_SHP.zip" target="_blank" rel="noopener noreferrer">AER Pipeline Spatial Dataset</a></div>` +
    `<div class="pipeline-card-footer">Licensed endpoints; flow direction may vary. Click or tap to keep this card open.</div></div>`;
}

function bindPipelineSegmentTooltip(feature, layer) {
  bindPipelineCard(layer, renderPipelineSegmentTooltip(feature.properties || {}));
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
      state.pipelineIndex = await requestJson(DATA_PATHS.pipelineIndex);
      if (!state.pipelineIndex.line_categories || typeof state.pipelineIndex.line_categories !== "object" || !state.pipelineIndex.installation_categories || typeof state.pipelineIndex.installation_categories !== "object") {
        state.pipelineIndex = null;
        throw new Error("Invalid pipeline index");
      }
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

  const promise = requestJson(entry.path).then(requireFeatureCollection)
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
  const promise = requestJson(pipelineTileUrl(entry, coord)).then(requireFeatureCollection)
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
    // Requests may finish after a pan or zoom. Cache the result, but only show
    // tiles that the current viewport still needs.
    if (state.map.getZoom() < PIPELINE_TILE_MIN_MAP_ZOOM) return;
    if (!visiblePipelineTileCoords(entry).some((current) => current.id === coord.id)) return;
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
    initLegendDisclosure();
    await loadData();
    initControls();
    initMap();
    // Default map state: official AB/BC fires, selected AER pipeline liquids,
    // and all configured refinery regions, including every U.S. PADD.
    state.wildfireEnabled = fireSelectedCount() > 0;
    state.refineryEnabled = refinerySelectedCount() > 0;
    state.pipelineEnabled = pipelineSelectedCount() > 0;
    updateFireToggleUI();
    updateFormationToggleUI();
    updateRefineryToggleUI();
    updatePipelineToggleUI();
    updateMarketPipelineToggleUI();
    updateRailwayToggleUI();
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
    if (els.freshness) els.freshness.textContent = "Production data is temporarily unavailable.";
    if (els.map) {
      els.map.innerHTML = `
        <div class="load-error">
          <h2>Production data did not load</h2>
          <p>${escapeHtml(error.message || error)}</p>
          <button type="button" onclick="window.location.reload()">Reload dashboard</button>
          <p>If this continues, contact the data administrator.</p>
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

  const SELECT_MODE_LABELS = { assets: "Assets", refineries: "Refineries" };
  function selectBtnLabel(on) {
    const kind = SELECT_MODE_LABELS[state.selectModeKind] || "Assets";
    return on ? `\u25A3 Select: ${kind}` : '\u25A3 Select <span class="select-caret">\u25BE</span>';
  }
  function setSelectMode(on) {
    selectMode = on;
    if (btn) {
      btn.classList.toggle("active", on);
      btn.innerHTML = selectBtnLabel(on);
      btn.title = on
        ? `Drag a box on the map to select ${SELECT_MODE_LABELS[state.selectModeKind] || "assets"} (Esc to exit)`
        : "Pick what to select by dragging a box on the map";
    }
    mapEl.style.cursor = on ? "crosshair" : "";
  }
  function setSelectMenuOpen(open) {
    state.selectMenuOpen = open;
    const menu = document.getElementById("selectMenu");
    if (menu) menu.hidden = !open;
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  function activateSelectKind(kind) {
    state.selectModeKind = kind === "refineries" ? "refineries" : "assets";
    setSelectMenuOpen(false);
    setSelectMode(true);
  }

  // Expose so distance tool can deactivate select mode
  state.setSelectMode = setSelectMode;

  if (btn) {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (selectMode) { setSelectMode(false); return; }
      setSelectMenuOpen(!state.selectMenuOpen);
    });
  }
  const selectMenuEl = document.getElementById("selectMenu");
  if (selectMenuEl) {
    selectMenuEl.addEventListener("click", (e) => {
      const opt = e.target.closest("[data-select-mode]");
      if (!opt) return;
      e.stopPropagation();
      activateSelectKind(opt.dataset.selectMode);
    });
  }
  document.addEventListener("click", (e) => {
    if (!state.selectMenuOpen) return;
    if (e.target.closest("#selectControl")) return;
    setSelectMenuOpen(false);
  });

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

    const inBox = (lat, lng) => {
      if (lat == null || lng == null) return false;
      const pt = state.map.latLngToContainerPoint([lat, lng]);
      return pt.x >= bLeft && pt.x <= bRight && pt.y >= bTop && pt.y <= bBottom;
    };

    if (state.selectModeKind === "refineries") {
      // Only currently-visible (filtered) refineries inside the box.
      const refFeatures = refineryVisibleFeatures().filter((ft) => {
        const c = ft.geometry && ft.geometry.coordinates;
        return c && inBox(c[1], c[0]);
      });
      showRefineryPanel(refFeatures);
      setSelectMode(false);
      return;
    }

    const { byAsset } = aggregateForDate();
    const hits = [];
    for (const point of byAsset.values()) {
      const { asset } = point;
      if (asset.latitude == null) continue;
      if (!legendVisible(pointLegendKey(point))) continue;
      if (inBox(asset.latitude, asset.longitude)) hits.push(asset.asset_id);
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

function productionGroupKey(sourceId, stream) {
  return JSON.stringify([sourceId, stream]);
}

function productionMonthEnd(month) {
  const [year, number] = month.split("-").map(Number);
  return `${month}-${String(new Date(Date.UTC(year, number, 0)).getUTCDate()).padStart(2, "0")}`;
}

function productionReportingCatalog() {
  const metadata = state.seasonalityIndex?.__reporting;
  const verified = metadata?.schema_version === 1 && Array.isArray(metadata.groups)
    && metadata.groups.every(g => g && typeof g.source_id === "string" && typeof g.stream === "string"
      && Array.isArray(g.months) && g.months.every(m => /^\d{4}-(0[1-9]|1[0-2])$/.test(m)));
  const sourceGroups = verified ? metadata.groups : (state.manifest?.source_coverage || []).filter(g => g.scenario === "actual");
  const catalog = sourceGroups.map(g => {
    const months = new Set(verified ? g.months : []);
    if (!verified) {
      for (const [date, rows] of Object.entries(state.manifest?.date_filter_totals || {})) {
        if (rows.some(r => r.scenario === "actual" && r.source_id === g.source_id && r.stream === g.stream)) months.add(date.slice(0, 7));
      }
      for (const r of state.baseRecords || []) {
        if (r.scenario === "actual" && r.source_id === g.source_id && r.stream === g.stream
          && typeof r.volume_kbbl_d === "number" && Number.isFinite(r.volume_kbbl_d) && r.volume_kbbl_d >= 0) months.add(r.date.slice(0, 7));
      }
    }
    const ordered = [...months].sort();
    return { ...g, key: productionGroupKey(g.source_id, g.stream), months,
      first_date: ordered.length ? productionMonthEnd(ordered[0]) : g.first_date,
      last_date: ordered.length ? productionMonthEnd(ordered.at(-1)) : g.last_date };
  });
  return { catalog, verified };
}

function classifyProductionMonth(date, groups, reportedGroups, reportedTotal, reliable = true, extraMissing = []) {
  const month = date.slice(0, 7);
  const missing = new Map();
  for (const group of groups) {
    const available = group.months.has(month);
    if (!available || !reportedGroups.has(group.key)) {
      const reason = !available
        ? (group.last_date && month > group.last_date.slice(0, 7) ? "Not yet reported"
          : group.first_date && month < group.first_date.slice(0, 7) ? "Earlier history unavailable" : "Report unavailable")
        : "No observation for the selected assets";
      missing.set(group.key, { source_id: group.source_id, stream: group.stream, last_date: group.last_date, reason });
    }
  }
  for (const group of extraMissing) missing.set(group.key, { source_id: group.source_id, stream: group.stream,
    last_date: group.last_date, reason: "A selected asset has no observation for this product stream" });
  const hasAmount = typeof reportedTotal === "number" && Number.isFinite(reportedTotal) && reportedTotal >= 0;
  const status = !hasAmount ? "missing" : !reliable || !groups.length ? "unverified" : missing.size ? "partial" : "complete";
  const missingSources = [...missing.values()];
  const names = [...new Set(missingSources.map(g => SOURCE_SHORT[g.source_id] || g.source_id))];
  const note = status === "complete" ? "All selected reporting sources cover this month. Values sum reported observations; omitted asset records are not assumed to be zero."
    : status === "partial" ? `Partial reporting${names.length ? ` — ${names.join(", ")}` : ""}. The full selection total is unavailable.`
    : status === "unverified" ? "Reporting coverage could not be verified. Showing available records only."
    : "No reported observation for this selection. Missing records do not confirm zero production.";
  return { date, status, reportedTotal: hasAmount ? reportedTotal : null, value: status === "complete" ? reportedTotal : null,
    missingSources, expectedGroupsCount: groups.length, reportingGroupsCount: groups.filter(g => g.months.has(month) && reportedGroups.has(g.key)).length,
    warnings: [], note };
}

function applyProductionQuality(point, groups) {
  const month = point.date.slice(0, 7);
  const warnings = Object.entries(state.manifest?.data_quality?.date_warnings || {})
    .filter(([date]) => date.startsWith(month)).flatMap(([, rows]) => rows)
    .filter(warning => groups.some(group => group.source_id === warning.source_id && (!warning.stream || group.stream === warning.stream)));
  point.warnings = warnings.filter(warning => warning.message).map(warning => {
    const name = SOURCE_SHORT[warning.source_id] || warning.source_id;
    const message = warning.message.replaceAll(warning.source_id, name);
    return message.includes(name) ? message : `${name}: ${message}`;
  });
  const needsReview = warnings.some(warning => warning.severity === "high"
    && !groups.filter(group => group.source_id === warning.source_id && (!warning.stream || group.stream === warning.stream))
      .every(group => (state.manifest?.source_reconciliation || []).some(observation => observation.source_id === group.source_id
        && observation.stream === group.stream && observation.period === month)));
  if (point.status === "complete" && needsReview) {
    point.status = "unverified";
    point.value = null;
    point.note = "Source reporting requires review. The reported amount remains visible, but complete reporting has not been verified.";
  }
  return point;
}

function computeSeasonality(assetIds) {
  const ym = {}, observations = new Map(), expected = new Map(), multiStreamMissing = new Map();
  const assetSet = new Set(assetIds);
  const { catalog, verified } = productionReportingCatalog();
  let reliable = verified;
  const assetGroups = new Map();
  for (const aid of assetSet) {
    const entry = state.seasonalityIndex?.[aid];
    const refs = entry?.__groups;
    let groups = verified && Array.isArray(refs) && refs.length && refs.every(i => Number.isInteger(i) && catalog[i])
      ? refs.map(i => catalog[i]) : [];
    if (!groups.length) {
      reliable = false;
      const asset = state.assetById.get(aid);
      groups = catalog.filter(g => g.source_id === asset?.source_id);
    }
    assetGroups.set(aid, groups);
    for (const group of groups) expected.set(group.key, group);
  }
  const addValue = (aid, date, value, groups, indexed = false) => {
    const month = String(date || "").slice(0, 7);
    if (!assetSet.has(aid) || !/^\d{4}-(0[1-9]|1[0-2])$/.test(month)
      || typeof value !== "number" || !Number.isFinite(value) || value < 0) return;
    const indexedValue = state.seasonalityIndex?.[aid]?.[month];
    if (!indexed && typeof indexedValue === "number" && Number.isFinite(indexedValue) && indexedValue >= 0) return;
    const year = Number(month.slice(0, 4)), number = Number(month.slice(5));
    if (!ym[year]) ym[year] = {};
    ym[year][number] = (ym[year][number] || 0) + value;
    if (!observations.has(month)) observations.set(month, { assetCount: 0, fallbackAssets: new Set(), groups: new Set() });
    const observation = observations.get(month);
    if (indexed) observation.assetCount++;
    else if (!observation.fallbackAssets.has(aid)) {
      observation.fallbackAssets.add(aid);
      observation.assetCount++;
    }
    for (const group of groups) observation.groups.add(group.key);
  };
  for (const aid of assetSet) {
    const entry = state.seasonalityIndex?.[aid];
    if (!entry) continue;
    const groups = assetGroups.get(aid);
    for (const [month, amount] of Object.entries(entry)) {
      if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) continue;
      let present = groups;
      if (groups.length > 1) {
        const refs = entry.__month_groups?.[month];
        present = Array.isArray(refs) ? refs.filter(i => Number.isInteger(i) && catalog[i]).map(i => catalog[i]) : [];
        const absent = groups.filter(g => !present.some(p => p.key === g.key));
        if (absent.length && typeof amount === "number" && Number.isFinite(amount) && amount >= 0) {
          const missing = multiStreamMissing.get(month) || [];
          missing.push(...absent);
          multiStreamMissing.set(month, missing);
        }
      }
      addValue(aid, month, amount, present, true);
    }
  }
  const fallbackKeys = new Set();
  const addFallback = record => {
    if (record.scenario !== "actual" || !assetSet.has(record.asset_id)) return;
    const key = JSON.stringify([record.asset_id, record.date, record.source_id, record.stream]);
    if (fallbackKeys.has(key)) return;
    fallbackKeys.add(key);
    const group = catalog.find(g => g.source_id === record.source_id && g.stream === record.stream);
    if (group) expected.set(group.key, group);
    addValue(record.asset_id, record.date, record.volume_kbbl_d, group ? [group] : []);
  };
  for (const record of state.baseRecords || []) addFallback(record);
  for (const records of state.dateRecordCache?.values() || []) for (const record of records) addFallback(record);
  const years = Object.keys(ym).map(Number).sort((a, b) => a - b);
  if (!years.length) return null;
  const datasetYear = Number(state.manifest?.latest_actual_date?.slice(0, 4));
  const currentYear = Math.max(years.at(-1), Number.isInteger(datasetYear) ? datasetYear : years.at(-1));
  if (!years.includes(currentYear)) years.push(currentYear);
  const months = {}, groups = [...expected.values()];
  for (const year of years) {
    months[year] = {};
    for (let number = 1; number <= 12; number++) {
      const month = `${year}-${String(number).padStart(2, "0")}`;
      const observation = observations.get(month);
      const point = classifyProductionMonth(`${month}-01`, groups, observation?.groups || new Set(), ym[year]?.[number], reliable, multiStreamMissing.get(month) || []);
      point.observedAssets = observation?.assetCount || 0;
      point.selectedAssetCount = assetSet.size;
      point.unavailableAssetsCount = assetSet.size - point.observedAssets;
      months[year][number] = applyProductionQuality(point, groups);
    }
  }
  const lastObservationMonth = [...observations.keys()].sort().at(-1);
  return { ym, years, currentYear, months, partialHistory: !reliable,
    latestDate: state.manifest?.latest_actual_date || `${lastObservationMonth}-01`, lastObservationDate: `${lastObservationMonth}-01` };
}

const SELECTION_GROUP_DIMS = [
  { key: "producer", label: "Producer" },
  { key: "system",   label: "Liquid type" },
  { key: "stream",   label: "Product stream" },
  { key: "province", label: "Province" },
  { key: "source",   label: "Data source" },
  { key: "kind",     label: "Asset kind" },
];

function prettyAssetKind(k) {
  return String(k || "unknown").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// Group a box-selected set of assets by a chosen dimension, summing current-date
// production (kbbl/d). Returns groups sorted by volume desc.
function computeSelectionBreakdown(assetIds, dim) {
  const { byAsset } = aggregateForDate();
  const groups = new Map();
  const get = (key, label, color) => {
    let g = groups.get(key);
    if (!g) { g = { key, label, color, kbbl: 0, count: 0 }; groups.set(key, g); }
    return g;
  };
  for (const id of assetIds) {
    const pt = byAsset.get(id);
    if (!pt) continue;
    const a = pt.asset;
    if (dim === "stream") {
      for (const [stream, v] of pt.streams.entries()) {
        const g = get(stream, STREAM_DESCRIPTIONS[stream] || stream, streamColor(stream));
        g.kbbl += v; g.count += 1;
      }
      continue;
    }
    let key, label, color = "#60717a";
    if (dim === "producer") { key = a.company || "Unknown"; label = key; color = systemMeta(a.production_system).color; }
    else if (dim === "system") { key = a.production_system || "unknown"; label = systemMeta(key).label; color = systemMeta(key).color; }
    else if (dim === "province") { key = a.province || "Unknown"; label = key; }
    else if (dim === "source") { key = a.source_id || "unknown"; label = SOURCE_SHORT[key] || key; }
    else { key = a.asset_kind || "unknown"; label = prettyAssetKind(key); }
    const g = get(key, label, color); g.kbbl += pt.kbbl; g.count += 1;
  }
  return [...groups.values()].sort((x, y) => y.kbbl - x.kbbl);
}

function seasonalityStatusLabel(month) {
  return { complete: "Complete source coverage", partial: "Partial source coverage", missing: "Missing", unverified: "Coverage unverified" }[month?.status] || "Missing";
}

function seasonalityMonthLabel(month) {
  return `${MONTH_LABELS[Number(month.date.slice(5, 7)) - 1]} ${month.date.slice(0, 4)}`;
}

function renderSeasonalityDetails(month, compact = false) {
  if (!month) return '<p class="sea-empty">Select a month to inspect its reported production and source coverage.</p>';
  const complete = month.status === "complete" && Number.isFinite(month.value);
  const amount = complete ? month.value : month.reportedTotal;
  const missing = month.missingSources || [];
  const sourceText = missing.map((source) => {
    const name = SOURCE_SHORT[source.source_id] || source.source_id || "Unknown source";
    const stream = source.stream ? ` · ${source.stream}` : "";
    const latest = source.last_date ? `latest available ${dateLabel(source.last_date)}` : "latest date unavailable";
    return `<li><strong>${escapeHtml(name + stream)}</strong> — ${escapeHtml(latest)}${source.reason ? ` · ${escapeHtml(source.reason)}` : ""}</li>`;
  }).join("");
  const warnings = (month.warnings || []).map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
  const coverage = Number.isFinite(month.expectedGroupsCount) && month.expectedGroupsCount > 0
    ? `${month.reportingGroupsCount} of ${month.expectedGroupsCount} relevant source streams reporting.`
    : "Source coverage is unavailable.";
  const assetCoverage = Number.isFinite(month.observedAssets) && Number.isFinite(month.selectedAssetCount)
    ? ` Observations for ${month.observedAssets} of ${month.selectedAssetCount} selected assets.` : "";
  const assetNote = Number.isFinite(month.unavailableAssetsCount) && month.unavailableAssetsCount > 0
    ? ` No observation for ${month.unavailableAssetsCount} selected asset${month.unavailableAssetsCount === 1 ? "" : "s"}; missing observations are not treated as zero.` : "";
  return `<div class="sea-detail-heading"><strong>${escapeHtml(seasonalityMonthLabel(month))}</strong><span class="sea-status ${escapeHtml(month.status)}">${escapeHtml(seasonalityStatusLabel(month))}</span></div>
    <p class="sea-detail-value">${complete ? "Reported production" : "Reported subtotal"}: <strong>${Number.isFinite(amount) ? kbbl(amount) : "Unavailable"}</strong></p>
    <p class="sea-detail-note">${escapeHtml(coverage + (compact ? "" : assetCoverage + assetNote))}</p>
    ${month.note && !compact ? `<p class="sea-detail-note">${escapeHtml(month.note)}</p>` : ""}
    ${missing.length ? `<div class="sea-missing-sources"><strong>Unavailable sources</strong><ul>${sourceText}</ul></div>` : ""}
    ${warnings && !compact ? `<div class="sea-warnings"><strong>Review notes</strong><ul>${warnings}</ul></div>` : ""}`;
}

async function showSeasonalityPanel(assetIds) {
  const existing = document.getElementById("seasonalityPanel");
  if (existing) { existing._seaResizeObserver?.disconnect(); existing.remove(); }

  if (!state.seasonalityIndex && !state.seasonalityIndexLoading) {
    state.seasonalityIndexLoading = true;
    const loadingPanel = document.createElement("div");
    loadingPanel.id = "seasonalityPanel";
    loadingPanel.innerHTML = `
      <div class="sea-header">
        <div><strong class="sea-title">Loading historical data…</strong>
        <span class="sea-sub">Fetching production history index (first time only)</span></div>
      </div>
      <div style="padding:24px;text-align:center;color:#6b7280;font-size:13px;">
        <div style="margin-bottom:8px">⏳ Building seasonality from production history…</div>
      </div>`;
    document.getElementById("map").appendChild(loadingPanel);
    try {
      state.seasonalityIndex = await requestJson("public/data/asset_seasonality.json");
    } catch(e) {
      console.warn("Could not load asset_seasonality.json:", e);
      state.seasonalityIndex = null;
      state.optionalDataWarnings.push("Seasonality index unavailable; only locally loaded history is shown.");
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
    const asset = state.assetById.get(id) || byAsset.get(id)?.asset;
    return asset ? asset.display_name : id;
  });
  const titleStr = names.join(", ") + (assetIds.length > 3 ? ` +${assetIds.length - 3} more` : "");

  const panel = document.createElement("div");
  panel.id = "seasonalityPanel";
  panel.setAttribute("role", "region");
  panel.setAttribute("aria-label", "Reported production history");
  const dims = SELECTION_GROUP_DIMS;
  panel.innerHTML = `
    <div class="sea-header">
      <div>
        <strong class="sea-title">${escapeHtml(titleStr)}</strong>
        <span class="sea-sub">${assetIds.length} asset${assetIds.length > 1 ? "s" : ""} · reported production, all streams per selected asset${data?.partialHistory ? " · partial history available" : ""}</span>
      </div>
      <button id="closeSeasonality" class="sea-close" title="Close" aria-label="Close production history">&#x2715;</button>
    </div>
    <div class="sea-controls">
      <div class="sea-tabs" id="seaTabs">
        <button class="sea-tab active" data-sea-tab="trend">Seasonality</button>
        <button class="sea-tab" data-sea-tab="breakdown">Breakdown</button>
      </div>
      <label class="sea-groupby" id="seaGroupWrap" hidden>Group by
        <select id="seaGroupSel">
          ${dims.map((dd) => `<option value="${dd.key}">${escapeHtml(dd.label)}</option>`).join("")}
        </select>
      </label>
    </div>
    <div id="seaTrend">
      <div class="sea-chart-wrap">
        <canvas id="seasonalityCanvas" width="580" height="240" role="img" aria-label="Reported production by calendar month. Solid lines show complete source coverage; hollow points show partial or unverified subtotals; missing months leave gaps. Monthly values and source details are available below."></canvas>
        <div id="seaTooltip" class="sea-tooltip" role="tooltip" hidden></div>
      </div>
      <div class="sea-legend" id="seaLegend"></div>
      <div id="seaMonthControls" class="sea-month-controls" hidden>
        <label for="seaMonthSelect">Inspect a month</label><select id="seaMonthSelect"></select>
      </div>
      <div id="seaMonthDetail" class="sea-month-detail" aria-live="polite"></div>
      <details id="seaMonthlyValues" class="sea-monthly-values" hidden>
        <summary>View monthly values and source coverage</summary>
        <div id="seaHistoryTable" class="sea-history-table-scroll"></div>
      </details>
    </div>
    <div id="seaBreakdown" class="sea-breakdown" hidden></div>
  `;
  document.getElementById("map").appendChild(panel);

  document.getElementById("closeSeasonality").addEventListener("click", () => {
    panel._seaResizeObserver?.disconnect();
    panel.remove();
    state.selectedAssets = [];
  });

  const trendEl = panel.querySelector("#seaTrend");
  const bdEl = panel.querySelector("#seaBreakdown");
  const groupWrap = panel.querySelector("#seaGroupWrap");
  const view = { tab: "trend", dim: dims[0].key };

  function renderBreakdown() {
    const groups = computeSelectionBreakdown(assetIds, view.dim);
    const dimLabel = dims.find((dd) => dd.key === view.dim).label;
    const point = data?.months[Number(state.selectedDate?.slice(0, 4))]?.[Number(state.selectedDate?.slice(5, 7))];
    if (!groups.length) {
      bdEl.innerHTML = point?.status === "complete" && point.reportedTotal === 0
        ? '<p class="sea-empty">Reported production is zero for this month.</p>'
        : '<p class="sea-empty">No reported observations for this selection at the selected date. Missing records do not confirm zero production.</p>';
      return;
    }
    const total = groups.reduce((a, g) => a + g.kbbl, 0) || 1;
    const maxV = groups[0].kbbl || 1;
    const rows = groups.map((g, i) => `<tr>
      <td class="sea-rank">${i + 1}</td>
      <td><i class="sea-swatch" style="background:${g.color}"></i>${escapeHtml(g.label)}</td>
      <td class="num"><strong>${kbbl(g.kbbl)}</strong></td>
      <td class="num">${(g.kbbl / total * 100).toFixed(1)}%</td>
      <td class="num">${g.count.toLocaleString("en-CA")}</td>
      <td class="barcell"><span class="sea-bar"><span class="sea-bar-fill" style="width:${Math.max(2, g.kbbl / maxV * 100)}%;background:${g.color}"></span></span></td>
    </tr>`).join("");
    bdEl.innerHTML = `
      <p class="sea-section-note">${groups.length} ${escapeHtml(dimLabel.toLowerCase())} group${groups.length > 1 ? "s" : ""} · ${kbbl(total)} reported ${point?.status === "complete" ? "production" : "subtotal · partial reporting"} at ${escapeHtml(state.selectedDate || "selected date")}.</p>
      ${point && point.status !== "complete" ? `<p class="sea-section-note">${escapeHtml(point.note)}</p>` : ""}
      <div class="sea-table-scroll"><table class="sea-table">
        <thead><tr><th>#</th><th>${escapeHtml(dimLabel)}</th><th class="num">kbbl/d</th><th class="num">Share</th><th class="num">Assets</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>`;
  }

  panel.querySelector("#seaTabs").addEventListener("click", (e) => {
    const b = e.target.closest("[data-sea-tab]"); if (!b) return;
    view.tab = b.dataset.seaTab;
    panel.querySelectorAll(".sea-tab").forEach((t) => t.classList.toggle("active", t === b));
    const isBd = view.tab === "breakdown";
    trendEl.hidden = isBd; bdEl.hidden = !isBd; groupWrap.hidden = !isBd;
    if (isBd) renderBreakdown();
  });
  panel.querySelector("#seaGroupSel").addEventListener("change", (e) => { view.dim = e.target.value; renderBreakdown(); });

  if (!data) {
    trendEl.insertAdjacentHTML("beforeend",
      '<p style="padding:10px 12px;color:#6b7280;font-size:12px">No monthly history for this selection — use the Breakdown tab for current-date splits.</p>');
  } else {
    drawSeasonalityChart(data, assetIds.length);
    if (typeof ResizeObserver === "function") {
      const canvas = panel.querySelector("#seasonalityCanvas");
      panel._seaResizeObserver = new ResizeObserver(() => {
        if (!panel.isConnected) { panel._seaResizeObserver.disconnect(); return; }
        const pixelRatio = Number(window.devicePixelRatio) || 1;
        if (canvas.clientWidth > 0 && Math.round(canvas.clientWidth) !== Math.round(canvas.width / pixelRatio)) drawSeasonalityChart(data, assetIds.length);
      });
      panel._seaResizeObserver.observe(canvas);
    }
  }
}

function drawSeasonalityChart(data, assetCount) {
  const canvas = document.getElementById("seasonalityCanvas");
  if (!canvas) return;
  const previousMonth = document.getElementById("seaMonthSelect")?.value;
  // Keep axis labels legible on narrow panels and sharp on high-density screens.
  const W = Math.round(canvas.clientWidth) || canvas.width;
  const H = W < 480 ? 220 : 240;
  const pixelRatio = Number(window.devicePixelRatio) || 1;
  canvas.width = Math.round(W * pixelRatio);
  canvas.height = Math.round(H * pixelRatio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform?.(pixelRatio, 0, 0, pixelRatio, 0, 0);
  const pad = { top: 16, right: 20, bottom: 36, left: 58 };
  const cW = W - pad.left - pad.right;
  const cH = H - pad.top - pad.bottom;

  const { months, years, currentYear } = data;
  const monthAt = (year, month) => months[year]?.[month];
  const completeValue = (year, month) => {
    const observation = monthAt(year, month);
    return observation?.status === "complete" && Number.isFinite(observation.value) ? observation.value : null;
  };

  const priorYears = years.filter(y => y < currentYear);
  const fullPriorYears = priorYears.filter(y => Array.from({ length: 12 }, (_, i) => completeValue(y, i + 1)).every(Number.isFinite));
  const rangeYears = fullPriorYears.length >= 2 ? fullPriorYears : priorYears;
  const lineYears = priorYears.slice(-2);

  // A range also needs continuous complete coverage; absent observations never
  // establish a zero bound or join the complete months on either side.
  const envelope = Array.from({ length: 12 }, (_, i) => {
    const values = rangeYears.map(year => completeValue(year, i + 1));
    return values.length && values.every(Number.isFinite) ? { min: Math.min(...values), max: Math.max(...values) } : null;
  });
  const plottedYears = [...lineYears, currentYear];
  let globalMax = 0;
  for (const year of plottedYears) {
    for (let month = 1; month <= 12; month++) {
      const observation = monthAt(year, month);
      const value = observation?.status === "complete" ? observation.value : observation?.reportedTotal;
      if (Number.isFinite(value)) globalMax = Math.max(globalMax, value);
    }
  }
  for (const bounds of envelope) if (bounds) globalMax = Math.max(globalMax, bounds.max);
  globalMax = globalMax > 0 ? globalMax * 1.08 : 1;

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
    ctx.fillText(formatNumber(v, v < 10 ? 1 : 0), pad.left - 5, y + 3);
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

  let envelopeRun = [];
  const fillEnvelopeRun = () => {
    if (!envelopeRun.length) return;
    ctx.beginPath();
    envelopeRun.forEach((month, i) => {
      const x = xPos(month), y = yPos(envelope[month - 1].max);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    [...envelopeRun].reverse().forEach(month => ctx.lineTo(xPos(month), yPos(envelope[month - 1].min)));
    ctx.closePath();
    ctx.fillStyle = "rgba(156,163,175,0.28)";
    ctx.fill();
    envelopeRun = [];
  };
  for (let month = 1; month <= 12; month++) {
    if (envelope[month - 1]) envelopeRun.push(month);
    else fillEnvelopeRun();
  }
  fillEnvelopeRun();

  const lineColors = [SEA_COLORS.y0, SEA_COLORS.y1];
  const plotPoints = [];
  plottedYears.forEach((year, i) => {
    const current = year === currentYear;
    const color = current ? SEA_COLORS.yCur : lineColors[i % 2];
    ctx.beginPath();
    let continuing = false;
    for (let month = 1; month <= 12; month++) {
      const value = completeValue(year, month);
      if (!Number.isFinite(value)) { continuing = false; continue; }
      const x = xPos(month), y = yPos(value);
      continuing ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      continuing = true;
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = current ? 2.2 : 1.8;
    ctx.stroke();
    for (let month = 1; month <= 12; month++) {
      const observation = monthAt(year, month);
      if (!observation) continue;
      const complete = Number.isFinite(completeValue(year, month));
      const subtotal = ["partial", "unverified"].includes(observation.status) && Number.isFinite(observation.reportedTotal);
      if (!complete && !subtotal) continue;
      const value = complete ? observation.value : observation.reportedTotal;
      const point = { year, month, x: xPos(month), y: yPos(value), observation };
      plotPoints.push(point);
      ctx.beginPath();
      ctx.arc(point.x, point.y, subtotal ? 4 : current ? 3.5 : 2.5, 0, Math.PI * 2);
      ctx.fillStyle = subtotal ? "#f9fafb" : color;
      ctx.fill();
      if (subtotal) { ctx.strokeStyle = "#64748b"; ctx.lineWidth = 1.6; ctx.stroke(); }
    }
  });

  const legEl = document.getElementById("seaLegend");
  if (legEl) {
    const enStr = rangeYears.length ? `${rangeYears[0]}–${rangeYears[rangeYears.length - 1]} complete-month range` : "";
    legEl.innerHTML = [
      envelope.some(Boolean) ? `<span><i style="background:rgba(156,163,175,0.45)"></i>${enStr}</span>` : "",
      ...lineYears.map((y, i) => `<span><i style="background:${lineColors[i]}"></i>${y}</span>`),
      `<span><i style="background:${SEA_COLORS.yCur};border-radius:50%"></i>${currentYear}</span>`,
      '<span><i class="sea-legend-partial"></i>Partial / unverified subtotal</span>',
      '<span class="sea-legend-note">Solid lines: complete source coverage · gaps: no complete observation</span>',
    ].filter(Boolean).join("");
  }

  const entries = years.flatMap(year => Array.from({ length: 12 }, (_, i) => monthAt(year, i + 1)).filter(Boolean)).reverse();
  const selector = document.getElementById("seaMonthSelect");
  const detail = document.getElementById("seaMonthDetail");
  const controls = document.getElementById("seaMonthControls");
  const table = document.getElementById("seaHistoryTable");
  const monthlyValues = document.getElementById("seaMonthlyValues");
  const tooltip = document.getElementById("seaTooltip");
  const showMonth = (observation) => {
    if (!observation) return;
    if (selector) selector.value = observation.date.slice(0, 7);
    if (detail) detail.innerHTML = renderSeasonalityDetails(observation);
  };
  if (selector) {
    selector.innerHTML = entries.map(observation => `<option value="${escapeHtml(observation.date.slice(0, 7))}">${escapeHtml(seasonalityMonthLabel(observation))} · ${escapeHtml(seasonalityStatusLabel(observation))}</option>`).join("");
    selector.onchange = () => showMonth(entries.find(observation => observation.date.slice(0, 7) === selector.value));
  }
  if (controls) controls.hidden = false;
  if (table) {
    table.innerHTML = `<table class="sea-table sea-history-table"><caption>Reported monthly production for ${assetCount} selected asset${assetCount === 1 ? "" : "s"}. Incomplete amounts are reported subtotals.</caption>
      <thead><tr><th scope="col">Month</th><th scope="col">Reported amount</th><th scope="col">Source coverage</th><th scope="col">Details</th></tr></thead><tbody>${entries.map(observation => {
        const complete = observation.status === "complete" && Number.isFinite(observation.value);
        const amount = complete ? observation.value : observation.reportedTotal;
        return `<tr><th scope="row">${escapeHtml(seasonalityMonthLabel(observation))}</th><td class="num">${Number.isFinite(amount) ? kbbl(amount) + (complete ? "" : " subtotal") : "Unavailable"}</td>
          <td>${escapeHtml(seasonalityStatusLabel(observation))}${observation.warnings?.length ? " · review note" : ""}</td><td><button class="sea-month-button" data-sea-month="${escapeHtml(observation.date.slice(0, 7))}" aria-label="View ${escapeHtml(seasonalityMonthLabel(observation))} source details">View</button></td></tr>`;
      }).join("")}</tbody></table>`;
    table.onclick = (event) => {
      const button = event.target.closest("[data-sea-month]");
      if (button) showMonth(entries.find(observation => observation.date.slice(0, 7) === button.dataset.seaMonth));
    };
  }
  if (monthlyValues) monthlyValues.hidden = false;
  showMonth(entries.find(observation => observation.date.slice(0, 7) === previousMonth)
    || entries.find(observation => observation.date.slice(0, 7) === data.latestDate?.slice(0, 7))
    || entries.find(observation => Number(observation.date.slice(0, 4)) === currentYear && Number.isFinite(observation.reportedTotal)) || entries[0]);

  const pointerPoint = (event) => {
    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) * W / rect.width;
    const y = (event.clientY - rect.top) * H / rect.height;
    const nearest = plotPoints.reduce((best, point) => {
      const distance = Math.hypot(point.x - x, point.y - y);
      return !best || distance < best.distance ? { point, distance } : best;
    }, null);
    return { rect, x, y, nearest };
  };
  canvas.onpointermove = (event) => {
    if (!tooltip) return;
    const { rect, nearest } = pointerPoint(event);
    if (!nearest || nearest.distance > 16) { tooltip.hidden = true; canvas.style.cursor = "crosshair"; return; }
    canvas.style.cursor = "pointer";
    tooltip.innerHTML = renderSeasonalityDetails(nearest.point.observation, true);
    tooltip.hidden = false;
    tooltip.style.left = `${Math.max(8, Math.min(rect.width - tooltip.offsetWidth - 8, event.clientX - rect.left + 12))}px`;
    tooltip.style.top = `${Math.max(8, Math.min(rect.height - tooltip.offsetHeight - 8, event.clientY - rect.top + 12))}px`;
  };
  canvas.onpointerleave = () => { if (tooltip) tooltip.hidden = true; };
  canvas.onclick = (event) => {
    const { x, nearest } = pointerPoint(event);
    const month = Math.max(1, Math.min(12, Math.floor((x - pad.left) / cW * 12) + 1));
    showMonth(nearest?.distance <= 16 ? nearest.point.observation : monthAt(currentYear, month));
    if (tooltip) tooltip.hidden = true;
  };
}

// ============================================================
// REFINERY CAPACITY & REFINED-PRODUCTS MODEL
// ------------------------------------------------------------
// Estimates refined-product output for a box-selected region from each
// plant's crude (CDU) capacity and process-unit configuration.
// Yield slates are grounded in published refining references:
//  - W.L. Leffler, "Petroleum Refining in Nontechnical Language" (4th/2020),
//    Table 20-1 "Refinery Yields" (medium sour crude) -> the configuration
//    slates used below (Simple/Complex/Very-Complex).
//  - M.A. Fahim et al., "Fundamentals of Petroleum Refining", Chapter 6:
//    mild visbreaking does not imply the residue conversion of a coker.
// These are illustrative configuration scenarios, not plant production forecasts.
// Coke uses a declared barrel-equivalent convention, never a liquid volume.
// ============================================================

const BBL_TO_GAL = 42;             // US gallons per barrel
const BBL_TO_L   = 158.987294928;  // litres per barrel
const COKE_BBL_EQ_PER_SHORT_TON = 5; // EIA petroleum-coke reporting convention

// Leffler Table 20-1 -- % of crude charge, medium sour crude (WTS / Arab Light)
const REFINERY_YIELD_SLATES = {
  topping:  { label: "Topping / Hydroskimming", gasoline: 30, jet: 10, distillate: 20, resid: 35, lpg: 0, coke: 0,  sco: 0,  fuelLoss: 8,  gain: 3  },
  cracking: { label: "Cracking (FCC / hydrocracker)", gasoline: 50, jet: 10, distillate: 25, resid: 10, lpg: 3, coke: 0,  sco: 0,  fuelLoss: 12, gain: 10 },
  coking:   { label: "Coking / Deep conversion", gasoline: 60, jet: 10, distillate: 25, resid: 0,  lpg: 4, coke: 3,  sco: 0,  fuelLoss: 13, gain: 15 },
};
const CONFIG_LABEL = { topping: "Hydroskimming", cracking: "FCC cracking", coking: "FCC + coking", splitter: "Cond. splitter", upgrader: "Upgrader", hydrocracking: "Hydrocracker", conversion: "Other conversion", distillation: "Distillation / specialty", unknown: "Unknown", inactive: "Inactive" };

const REFINED_PRODUCTS = [
  { key: "gasoline",   label: "Motor gasoline",      short: "Gasoline", color: "#16a34a" },
  { key: "distillate", label: "Diesel / distillate", short: "Diesel",   color: "#2563eb" },
  { key: "jet",        label: "Jet / kerosene",      short: "Jet",      color: "#0891b2" },
  { key: "resid",      label: "Residual fuel oil",   short: "Resid",    color: "#92400e" },
  { key: "lpg",        label: "LPG",                 short: "LPG",      color: "#d97706" },
  { key: "coke",       label: "Petroleum coke (short tons)", short: "Coke (st/d)", color: "#475569" },
];

const PROCESS_UNITS = [
  { key: "crude",        label: "Crude distillation (CDU)" },
  { key: "fcc",          label: "Cat cracking (FCC)" },
  { key: "hcu",          label: "Hydrocracking" },
  { key: "coker",        label: "Coking" },
  { key: "reformer",     label: "Catalytic reforming" },
  { key: "hydrotreater", label: "Hydrotreating" },
  { key: "alky",         label: "Alkylation" },
];

// IIR keeps decommissioned units (Closed/Mothballed/Removed/Shuttered) in the
// unit list — ~4% of listed BBL/d capacity. Counting them silently inflates
// unit totals, Nelson CI, and can flip a plant's configuration class.
function refineryUnitActive(u) {
  const g = String(u.unit_status_group || "").trim().toLowerCase();
  const s = String(u.unit_status_desc || "").trim().toLowerCase();
  if (g && g !== "commissioned") return false;
  return !s || ["operational", "operating", "active"].includes(s);
}

function refineryPlantActive(props) {
  const status = String(props.plant_status_desc || "").trim().toLowerCase();
  return !status || ["operational", "operating", "active"].includes(status);
}

function refineryPositiveNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

function refineryActiveUnits(props) {
  if (!refineryPlantActive(props)) return [];
  const seen = new Set();
  return (props.refinery_units || []).filter((u) => {
    if (!refineryUnitActive(u)) return false;
    if (u.unit_id != null) {
      const id = String(u.unit_id);
      if (seen.has(id)) return false;
      seen.add(id);
    }
    return true;
  });
}

function refineryUnitKbbl(u) {
  const unit = String(u.capacity_uom || "").trim().toLowerCase();
  if (!["bbl/d", "kbbl/d"].includes(unit)) return 0;
  return refineryPositiveNumber(u.unit_capacity_feed_kbbl_d)
    || refineryPositiveNumber(u.capacity_kbbl_d)
    || refineryPositiveNumber(u.capacity) / (unit === "bbl/d" ? 1000 : 1);
}

function refineryUnitCapacities(props) {
  const cap = { crude: effectiveCrudeCharge(props).charge, fcc: 0, hcu: 0, coker: 0, reformer: 0, hydrotreater: 0, alky: 0, visbreaker: 0 };
  for (const u of refineryActiveUnits(props)) {
    const c = refineryUnitKbbl(u);
    if (!c) continue;
    const g = (u.unit_type_group || "").toLowerCase();
    const sh = (u.unit_type_short || "").toLowerCase();
    const t = `${sh} ${(u.unit_type_desc || "").toLowerCase()}`;
    if (/splitter|calciner/.test(t)) continue;
    // Hydrotreaters first: IIR leaves unit_type_group null for many of them
    // (reformer-feed, VGO/HGO, naphtha, lube, resid HT), and their names can
    // contain FCC/reformer tokens ("FCCU Gasoline Hydrotreater").
    if (g.includes("hydrotreat") || t.includes("hydrotreat") || t.includes("hydrorefin")) cap.hydrotreater += c;
    else if (g.includes("cat cracker") || g.includes("fccu") || sh === "fcc") cap.fcc += c;
    else if (g.includes("hydrocrack") || sh === "hck" || t.includes("hydrocrack")) cap.hcu += c;
    else if (g.includes("visbreak") || t.includes("visbreak")) cap.visbreaker += c;
    else if (g.includes("coking") || sh.includes("cok")) cap.coker += c;
    else if (g.includes("reform") || t.includes("reform")) cap.reformer += c;
    else if (g.includes("alky") || t.includes("alky")) cap.alky += c;
  }
  return cap;
}

function refineryThroughputUnits(props) {
  let cdu = 0, vac = 0, dru = 0, coker = 0;
  for (const u of refineryActiveUnits(props)) {
    const c = refineryUnitKbbl(u);
    if (!c) continue;
    const sh = (u.unit_type_short || "").toLowerCase();
    const t = `${sh} ${(u.unit_type_desc || "").toLowerCase()}`;
    if (sh === "cdu" || t.includes("atmospheric distill") || (t.includes("crude") && t.includes("distill"))) cdu += c;
    else if (t.includes("vacuum")) vac += c;
    else if (t.includes("diluent recovery") || /\bdru\b/.test(t)) dru += c;
    else if (t.includes("cok") && !t.includes("calciner")) coker += c;
  }
  return { cdu, vac, dru, coker };
}

function refineryIsOilSands(props) {
  const descriptor = [
    props.plant_name,
    Array.isArray(props.plant_sectors) ? props.plant_sectors.join(" ") : props.plant_sectors,
    props.plant_type,
  ].filter(Boolean).join(" ").toLowerCase();
  return /\bupgrader\b|oil[\s-]*sands|synthetic crude|\bhorizon\b|mildred lake|\bsyncrude\b|long lake/.test(descriptor);
}

// Reported crude capacity, otherwise active atmospheric distillation capacity.
// Secondary-unit capacity cannot establish fresh crude or bitumen input: streams
// may be imported, recycled, or shared with another plant. Never infer coker/0.30.
function effectiveCrudeCharge(props) {
  if (!refineryPlantActive(props)) return { charge: 0, basis: "inactive" };
  // An upgrader's bitumen/dilbit feed rating is not conventional crude capacity.
  if (refineryIsOilSands(props)) return { charge: 0, basis: "upgrader" };
  const cdus = (props.refinery_units || []).filter((u) => {
    const t = `${u.unit_type_short || ""} ${u.unit_type_desc || ""}`.toLowerCase();
    return /\bcdu\b|atmospheric distill/.test(t);
  });
  if (cdus.length && cdus.every((u) => !refineryUnitActive(u))) return { charge: 0, basis: "inactive_cdu" };
  const plant = refineryPositiveNumber(props.crud_capacity_kbbl_d)
    || refineryPositiveNumber(props.crud_capacity_bbl_d) / 1000;
  if (plant > 0) return { charge: plant, basis: "crude" };
  const u = refineryThroughputUnits(props);
  if (u.cdu > 0) return { charge: u.cdu, basis: "cdu" };
  return { charge: 0, basis: "none" };
}

function refineryConfig(props, cap, charge, basis) {
  const name = `${props.plant_name || ""} ${props.plant_sectors || ""}`.toLowerCase();
  if (basis === "inactive" || basis === "inactive_cdu") return "inactive";
  if (refineryIsOilSands(props)) return "upgrader";
  if (name.includes("condensate") || name.includes("splitter")) return "splitter";
  if (charge <= 0) return "unknown";
  // Leffler's complex/very-complex examples have an FCC. A hydrocracker-only
  // refinery is not assigned the same gasoline-heavy slate without an assay.
  if (cap.fcc / charge >= 0.05) return cap.coker / charge >= 0.05 ? "coking" : "cracking";
  if (cap.hcu / charge >= 0.05) return "hydrocracking";
  if (cap.coker / charge >= 0.05) return "conversion";
  if (cap.reformer > 0 && cap.hydrotreater > 0) return "topping";
  return "distillation";
}

// Nelson Complexity Index (Kaiser/Gary/Handwerk, "Petroleum Refining: Technology,
// Economics, and Markets" 2019, Table 7.1 -- OGJ 1998-2019 complexity factors).
// CI = 1 (atmospheric distillation, the normalizer) + Sum( CF_unit x cap_unit / crude ).
// Keyed on unit_type_short because IIR populates unit_type_group only for the major
// conversion units, leaving vacuum distillation, isomerization, several hydrotreaters,
// asphalt and lubes with a null group (their short code / capacity are still present).
function nelsonCF(u) {
  const t = `${u.unit_type_short || ""} ${u.unit_type_group || ""} ${u.unit_type_desc || ""}`.toLowerCase();
  // utilities / fractionation / non-refining -> no standard complexity factor
  if (t.includes("calciner") || t.includes("splitter") || t.includes("sulfur") ||
      t.includes("amine") || t.includes("lights ends") || t.includes("diluent recovery")) return 0;
  // Feed/service names must not override the unit's actual treatment process.
  if (t.includes("hydrorefin") || t.includes("residual hydrotreat")) return 3;
  if (t.includes("hydrotreat")) return 2;
  if (t.includes("vacuum")) return 2;                                   // vacuum distillation
  if (t.includes("visbreak") || t.includes("thermal crack")) return 2.75; // thermal cracking / visbreaking
  if (t.includes("cat crack") || /\bfcc\b/.test(t)) return 6;          // catalytic cracking
  if (t.includes("cok")) return 6;                                      // delayed / fluid coking
  if (t.includes("hydrocrack") || /\bhck\b/.test(t)) return 6;         // hydrocracking
  if (t.includes("isomeriz")) return 15;                               // isomerization
  if (t.includes("alky")) return 10;                                   // alkylation
  if (t.includes("polymeriz") || t.includes("dimeriz")) return 10;     // poly/dimerization
  if (t.includes("aromatic") || t.includes("benzene") || t.includes("hydrodealkyl")) return 15;
  if (t.includes("asphalt")) return 1.5;                              // asphalt
  if (t.includes("lube")) return 10;                                  // lubes
  if (/\breform/.test(t)) return 5;                                   // catalytic reforming
  return 0;
}

// Hydrogen plant capacity in MMcfd (from plant_capacities). The OGJ/Nelson convention
// (Kaiser/Gary/Handwerk Table 7.6 worked example) treats the MMcfd figure numerically
// as Mbpd-equivalent in the ratio, with complexity factor 1.
function refineryHydrogenMMcfd(props) {
  if (!refineryPlantActive(props)) return 0;
  let h = 0;
  for (const c of props.plant_capacities || []) {
    const pd = (c.product_desc || "").toLowerCase();
    // Purchased hydrogen (Feed) is not an installed hydrogen production unit.
    if (!pd.includes("hydrogen") || String(c.kind || "").toLowerCase() !== "output") continue;
    const cap = refineryPositiveNumber(c.design_capacity) || refineryPositiveNumber(c.actual_capacity);
    const u = (c.uom || "").toLowerCase();
    if (u.includes("k cubic")) h += cap / 1000;          // k cubic ft/day -> MMcfd
    else if (u.includes("mmscfd") || u.includes("mmcfd")) h += cap;
  }
  return h;
}


function refineryComplexity(props) {
  const crude = effectiveCrudeCharge(props).charge;
  if (crude <= 0 || refineryIsOilSands(props)) return null;
  let weighted = 0;
  for (const u of refineryActiveUnits(props)) {
    const c = refineryUnitKbbl(u);
    if (!c) continue;
    const sh = (u.unit_type_short || "").toLowerCase();
    if (sh === "cdu" || sh.includes("crude")) continue; // ADU is the normalizer (counted as 1)
    weighted += nelsonCF(u) * c;
  }
  weighted += 1 * refineryHydrogenMMcfd(props); // hydrogen plant, CF 1, MMcfd ~ Mbpd
  return 1 + weighted / crude;
}

function estimateRefineryProducts(props, utilizationPercent = 100) {
  const cap = refineryUnitCapacities(props);
  const { charge, basis } = effectiveCrudeCharge(props);
  const cls = refineryConfig(props, cap, charge, basis);
  const slate = REFINERY_YIELD_SLATES[cls];
  const requested = Number(utilizationPercent);
  const utilization = Number.isFinite(requested) ? Math.max(0, Math.min(100, requested)) / 100 : 1;
  const modeled = charge > 0 && !!slate;
  const feed = modeled ? charge * utilization : 0;
  const products = {};
  for (const p of REFINED_PRODUCTS) products[p.key] = modeled ? feed * (slate[p.key] || 0) / 100 : null;
  return { cap, cls, basis, slate, modeled, utilization, feed, crude: charge, products,
    fuelLoss: modeled ? feed * slate.fuelLoss / 100 : 0, gain: modeled ? feed * slate.gain / 100 : 0 };
}

// Volume formatting in the user-selected unit (bbl/d default).
function refVolFmt(kbbl_d, unit) {
  const bbl = (kbbl_d || 0) * 1000;
  let v = bbl, suffix = "bbl/d";
  if (unit === "gal") { v = bbl * BBL_TO_GAL; suffix = "gal/d"; }
  else if (unit === "l") { v = bbl * BBL_TO_L; suffix = "L/d"; }
  let str;
  if (v >= 1e9) str = (v / 1e9).toFixed(2) + "B";
  else if (v >= 1e6) str = (v / 1e6).toFixed(2) + "M";
  else if (v >= 1e3) str = (v / 1e3).toFixed(1) + "k";
  else str = Math.round(v).toLocaleString("en-CA");
  return { str, suffix, raw: v };
}

function refProductFmt(key, value, unit) {
  if (value == null) return { str: "—", suffix: "", raw: null };
  if (key !== "coke") return refVolFmt(value, unit);
  const raw = value * 1000 / COKE_BBL_EQ_PER_SHORT_TON;
  return { str: raw.toLocaleString("en-CA", { maximumFractionDigits: 1 }), suffix: "short ton/d", raw };
}

function showRefineryPanel(features, utilizationPercent = 100) {
  const existing = document.getElementById("refineryPanel");
  if (existing) existing.remove();

  const panel = document.createElement("div");
  panel.id = "refineryPanel";

  if (!features || !features.length) {
    panel.innerHTML = `
      <div class="ref-header">
        <div><strong class="ref-title">No refineries in selection</strong>
        <span class="ref-sub">Turn on the Refineries layer and drag the box over visible plants.</span></div>
        <button id="closeRefinery" class="ref-close" title="Close">&#x2715;</button>
      </div>`;
    document.getElementById("map").appendChild(panel);
    document.getElementById("closeRefinery").addEventListener("click", () => panel.remove());
    return;
  }

  // ---- Aggregate ----
  const seenPlants = new Set();
  const rows = features.filter((ft) => {
    const id = ft.properties.plant_id;
    if (id == null) return true;
    if (seenPlants.has(String(id))) return false;
    seenPlants.add(String(id));
    return true;
  }).map((ft) => {
    const p = ft.properties;
    const est = estimateRefineryProducts(p, utilizationPercent);
    return {
      name: p.plant_name || "Unknown",
      owner: p.parent_company || p.owner_name || p.operator_name || "Unknown",
      padd: p.country_padd || p.trading_region_name || "",
      country: p.country_name || "",
      state: p.state_name || "",
      status: p.plant_status_desc || "",
      ci: refineryComplexity(p),
      ...est,
    };
  });

  const totalCrude = rows.reduce((a, r) => a + r.crude, 0) || 0;
  const modeledRows = rows.filter(r => r.modeled);
  const modeledCrude = modeledRows.reduce((a, r) => a + r.crude, 0);
  const modeledFeed = modeledRows.reduce((a, r) => a + r.feed, 0);
  const utilization = rows[0].utilization * 100;
  const ciCrude = rows.reduce((a, r) => a + (Number.isFinite(r.ci) ? r.crude : 0), 0);
  const unitTotals = {};
  for (const u of PROCESS_UNITS) unitTotals[u.key] = rows.reduce((a, r) => a + (r.cap[u.key] || 0), 0);
  const productTotals = {};
  for (const pr of REFINED_PRODUCTS) productTotals[pr.key] = rows.reduce((a, r) => a + (r.products[pr.key] || 0), 0);
  const totalFuelLoss = rows.reduce((a, r) => a + r.fuelLoss, 0);
  const totalGain = rows.reduce((a, r) => a + r.gain, 0);
  const totalLiquidProducts = REFINED_PRODUCTS.filter(p => p.key !== "coke").reduce((a, p) => a + productTotals[p.key], 0);
  // Only show product rows/columns that are non-zero across the selection (e.g. SCO
  // appears only when upgraders are included).
  const activeProducts = REFINED_PRODUCTS.filter(p => productTotals[p.key] > 0.05);
  const shownProducts = activeProducts.length ? activeProducts : REFINED_PRODUCTS;
  const regionCI = ciCrude ? rows.reduce((a, r) => a + (Number.isFinite(r.ci) ? r.ci * r.crude : 0), 0) / ciCrude : null;
  const ciLabel = value => Number.isFinite(value) ? value.toFixed(1) : "—";

  // Owner aggregation
  const ownerMap = new Map();
  for (const r of rows) {
    const o = ownerMap.get(r.owner) || { owner: r.owner, crude: 0, count: 0, modeledCount: 0, ciw: 0, ciCrude: 0, products: {} };
    o.crude += r.crude; o.count += 1; o.modeledCount += Number(r.modeled);
    if (Number.isFinite(r.ci)) { o.ciw += r.ci * r.crude; o.ciCrude += r.crude; }
    for (const pr of REFINED_PRODUCTS) o.products[pr.key] = (o.products[pr.key] || 0) + (r.products[pr.key] || 0);
    ownerMap.set(r.owner, o);
  }
  const owners = [...ownerMap.values()].sort((a, b) => b.crude - a.crude);

  // Region descriptor + trader metrics
  const paddSet = [...new Set(rows.map(r => r.padd).filter(Boolean))];
  const countrySet = [...new Set(rows.map(r => r.country).filter(Boolean))];
  const hhi = owners.reduce((a, o) => { const sh = totalCrude ? o.crude / totalCrude : 0; return a + sh * sh; }, 0);
  const top3Share = totalCrude ? owners.slice(0, 3).reduce((a, o) => a + o.crude, 0) / totalCrude : 0;
  const configCounts = rows.reduce((a, r) => { a[r.cls] = (a[r.cls] || 0) + 1; return a; }, {});

  const regionStr = (countrySet.length ? countrySet.join(", ") : "Selection")
    + (paddSet.length ? ` · ${paddSet.join(", ")}` : "");

  panel.innerHTML = `
    <div class="ref-header">
      <div>
        <strong class="ref-title">Refining capacity &mdash; ${rows.length} plant${rows.length > 1 ? "s" : ""}</strong>
        <span class="ref-sub">${escapeHtml(regionStr)} · ${Math.round(totalCrude).toLocaleString("en-CA")} kbbl/d reported / CDU capacity · ${owners.length} owner${owners.length > 1 ? "s" : ""} · estimated CI ${ciLabel(regionCI)}</span>
      </div>
      <button id="closeRefinery" class="ref-close" title="Close">&#x2715;</button>
    </div>
    <div class="ref-controls">
      <div class="ref-tabs" id="refTabs">
        <button class="ref-tab active" data-ref-tab="products">Product scenario</button>
        <button class="ref-tab" data-ref-tab="units">Process units</button>
        <button class="ref-tab" data-ref-tab="owners">Owners</button>
        <button class="ref-tab" data-ref-tab="plants">Refineries</button>
        <button class="ref-tab" data-ref-tab="method">Method</button>
      </div>
      <div class="ref-units" id="refUnits" title="Display volume unit">
        <button class="ref-unit active" data-ref-unit="bbl">bbl/d</button>
        <button class="ref-unit" data-ref-unit="gal">gal/d</button>
        <button class="ref-unit" data-ref-unit="l">L/d</button>
      </div>
    </div>
    <div class="ref-scenario-controls">
      <label for="refUtilization">Scenario utilization</label>
      <input id="refUtilization" type="number" min="0" max="100" step="1" value="${utilization}" aria-describedby="refCoverage" />
      <span>% of capacity</span>
    </div>
    <p class="ref-section-note" id="refCoverage">${modeledRows.length} of ${rows.length} plants have a supported textbook scenario (${Math.round(modeledCrude).toLocaleString("en-CA")} kbbl/d capacity). ${rows.length - modeledRows.length} excluded: missing active crude input or unsupported configuration. See Refineries for each plant.</p>
    <div class="ref-body" id="refBody"></div>
    <div class="ref-footer">
      <span class="ref-note">Illustrative medium-crude scenario; actual yields require feed assays and operating data. Coke is always in short tons/day.</span>
      <button class="ref-csv" id="refCsv">Export CSV</button>
    </div>
  `;
  document.getElementById("map").appendChild(panel);
  document.getElementById("closeRefinery").addEventListener("click", () => panel.remove());
  panel.querySelector("#refUtilization").addEventListener("change", (event) => {
    const input = event.target;
    if (!input.reportValidity() || input.value.trim() === "") return;
    showRefineryPanel(features, Number(input.value));
  });

  const view = { tab: "products", unit: "bbl" };

  function bar(pct, color) {
    const w = Math.max(0, Math.min(100, pct));
    return `<span class="ref-bar"><span class="ref-bar-fill" style="width:${w}%;background:${color}"></span></span>`;
  }

  function renderProducts() {
    if (!modeledRows.length) return '<p class="ref-section-note">Product estimates are unavailable for this selection. Reported process capacities remain available in the Process units tab. A feed assay and plant-specific yield model are required for splitters, upgraders and other configurations.</p>';
    const u = view.unit;
    const maxV = Math.max(...shownProducts.map(p => productTotals[p.key]), 1);
    let rowsHtml = shownProducts.map(p => {
      const f = refProductFmt(p.key, productTotals[p.key], u);
      const pctCrude = modeledFeed ? (productTotals[p.key] / modeledFeed * 100) : null;
      return `<tr>
        <td><i class="ref-swatch" style="background:${p.color}"></i>${escapeHtml(p.label)}</td>
        <td class="num"><strong>${f.str}</strong> <span class="ref-u">${f.suffix}</span></td>
        <td class="num">${pctCrude == null ? "—" : pctCrude.toFixed(1) + "%"}${p.key === "coke" && pctCrude != null ? " eq." : ""}</td>
        <td class="barcell">${bar(productTotals[p.key] / maxV * 100, p.color)}</td>
      </tr>`;
    }).join("");
    const liq = refVolFmt(totalLiquidProducts, u);
    return `
      <p class="ref-section-note">Illustrative output from ${Math.round(modeledFeed).toLocaleString("en-CA")} kbbl/d scenario feed at ${utilization}% utilization. Liquid units: ${refVolFmt(0,u).suffix}; coke: short ton/d using the EIA 5 bbl-equivalent/short-ton convention. The textbook coke percentage is an equivalent-volume scenario, not a measured mass yield.</p>
      <table class="ref-table">
        <thead><tr><th>Product</th><th class="num">Scenario output</th><th class="num">% of modeled feed</th><th></th></tr></thead>
        <tbody>${rowsHtml}</tbody>
        <tfoot>
          <tr><td>Total liquid products</td><td class="num"><strong>${liq.str}</strong> <span class="ref-u">${liq.suffix}</span></td><td class="num"></td><td></td></tr>
          <tr class="memo"><td>Refinery fuel (textbook memo)</td><td></td><td class="num">${modeledFeed ? (totalFuelLoss/modeledFeed*100).toFixed(1) + "%" : "—"}</td><td></td></tr>
          <tr class="memo"><td>Processing gain (textbook memo)</td><td></td><td class="num">${modeledFeed ? "+" + (totalGain/modeledFeed*100).toFixed(1) + "%" : "—"}</td><td></td></tr>
        </tbody>
      </table>`;
  }

  function renderUnits() {
    const u = view.unit;
    const maxV = Math.max(...PROCESS_UNITS.map(x => unitTotals[x.key]), 1);
    let rowsHtml = PROCESS_UNITS.map(x => {
      const f = refVolFmt(unitTotals[x.key], u);
      const pctCrude = totalCrude && x.key !== "crude" ? (unitTotals[x.key] / totalCrude * 100) : (x.key === "crude" ? 100 : 0);
      return `<tr>
        <td>${escapeHtml(x.label)}</td>
        <td class="num"><strong>${f.str}</strong> <span class="ref-u">${f.suffix}</span></td>
        <td class="num">${unitTotals[x.key] ? pctCrude.toFixed(0) + "%" : "&mdash;"}</td>
        <td class="barcell">${bar(unitTotals[x.key] / maxV * 100, "#b4532a")}</td>
      </tr>`;
    }).join("");
    return `
      <p class="ref-section-note">Active process-unit capacity across the selection. Downstream percentages compare installed capacities; streams overlap and must not be added as fresh feed or product output. Utilization does not change installed capacity.</p>
      <table class="ref-table">
        <thead><tr><th>Process unit</th><th class="num">Capacity</th><th class="num">vs crude</th><th></th></tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>`;
  }

  function renderOwners() {
    const u = view.unit;
    const prodHead = shownProducts.map(p => `<th class="num" title="${escapeHtml(p.label)}">${p.short}</th>`).join("");
    let rowsHtml = owners.map(o => {
      const f = refVolFmt(o.crude, u);
      const share = totalCrude ? (o.crude / totalCrude * 100) : 0;
      const prodCells = shownProducts.map(p => `<td class="num">${refProductFmt(p.key, o.modeledCount ? o.products[p.key] : null, u).str}</td>`).join("");
      const avgCI = o.ciCrude ? (o.ciw / o.ciCrude) : null;
      return `<tr>
        <td>${escapeHtml(o.owner)}</td>
        <td class="num">${o.count}</td>
        <td class="num"><strong>${f.str}</strong> <span class="ref-u">${f.suffix}</span></td>
        <td class="num">${ciLabel(avgCI)}</td>
        <td class="num">${share.toFixed(1)}%</td>
        ${prodCells}
      </tr>`;
    }).join("");
    return `
      <p class="ref-section-note">Scenario output grouped by the listed parent company; joint-venture equity shares are unavailable. Liquids in ${refVolFmt(0,u).suffix}; coke in short ton/d. Capacity concentration: top 3 ${(top3Share*100).toFixed(0)}%, HHI ${Math.round(hhi*10000)}; plants with unknown capacity are excluded from shares.</p>
      <table class="ref-table">
        <thead><tr><th>Owner (parent)</th><th class="num">Plants</th><th class="num">Crude cap</th><th class="num" title="Nelson Complexity Index (capacity-weighted)">CI</th><th class="num">Share</th>${prodHead}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>`;
  }

  function renderPlants() {
    const u = view.unit;
    const sorted = [...rows].sort((a, b) => b.crude - a.crude);
    const prodHead = shownProducts.map(p => `<th class="num" title="${escapeHtml(p.label)}">${p.short}</th>`).join("");
    let rowsHtml = sorted.map(r => {
      const f = refVolFmt(r.crude, u);
      const prodCells = shownProducts.map(p => `<td class="num">${refProductFmt(p.key, r.products[p.key], u).str}</td>`).join("");
      return `<tr>
        <td>${escapeHtml(r.name)}</td>
        <td>${escapeHtml(r.owner)}</td>
        <td class="num"><strong>${r.crude ? f.str : "—"}</strong></td>
        <td class="num">${ciLabel(r.ci)}</td>
        <td><span class="ref-cfg ${r.cls}">${CONFIG_LABEL[r.cls]}</span>${r.modeled ? "" : '<br><span class="muted">No product estimate</span>'}</td>
        ${prodCells}
      </tr>`;
    }).join("");
    return `
      <p class="ref-section-note">All selected plants, largest known crude capacity first. A dash means unavailable; zero means zero modeled output. Liquids in ${refVolFmt(0,u).suffix}; coke in short ton/d. CI uses only confirmed crude capacity and active units.</p>
      <table class="ref-table">
        <thead><tr><th>Refinery</th><th>Owner</th><th class="num">Crude</th><th class="num" title="Nelson Complexity Index">CI</th><th>Config</th>${prodHead}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>`;
  }

  function renderMethod() {
    const order = ["topping", "cracking", "coking"];
    const slateRows = [...REFINED_PRODUCTS.map(p => ({ k: p.key, label: p.key === "coke" ? "Petroleum coke (barrel-equivalent %)" : p.label })),
      { k: "fuelLoss", label: "Refinery fuel", memo: true },
      { k: "gain", label: "Processing gain", memo: true }];
    const headCells = order.map(k => `<th class="num">${CONFIG_LABEL[k]}</th>`).join("");
    const slateBody = slateRows.map(r => {
      const cells = order.map(k => {
        const v = REFINERY_YIELD_SLATES[k][r.k];
        return `<td class="num">${r.k === "gain" ? "(" + v + ")" : v}</td>`;
      }).join("");
      return `<tr${r.memo ? ' class="memo-row"' : ""}><td>${escapeHtml(r.label)}</td>${cells}</tr>`;
    }).join("");

    const split = order.filter(k => (configCounts[k] || 0) > 0)
      .map(k => `${configCounts[k]} ${CONFIG_LABEL[k].toLowerCase()}`).join(" · ");

    return `
      <p class="ref-section-note"><strong>How the scenario is built.</strong> Liquid output = confirmed crude capacity × utilization% ÷ 100 × textbook yield% ÷ 100. Plant and unit status must be active. Missing plant capacity can be recovered from active CDU capacity; secondary units cannot establish crude or bitumen input. Duplicate plant/unit IDs are counted once.</p>

      <p class="ref-method-h">1 · Configuration classifier (capacity vs crude charge)</p>
      <table class="ref-table ref-method-table">
        <thead><tr><th>Configuration</th><th>Rule</th></tr></thead>
        <tbody>
          <tr><td><span class="ref-cfg coking">FCC + coking</span></td><td>FCC and coking capacity each ≥ 5% of crude; visbreaking does not qualify as coking</td></tr>
          <tr><td><span class="ref-cfg cracking">FCC cracking</span></td><td>FCC ≥ 5% of crude without a qualifying coker</td></tr>
          <tr><td><span class="ref-cfg topping">Hydroskimming</span></td><td>Reforming and hydrotreating, without qualifying conversion capacity</td></tr>
          <tr><td>Other configurations</td><td>Splitters, upgraders, hydrocracker-only, distillation-only and missing-input plants have no product estimate; a feed assay and suitable plant model are required</td></tr>
        </tbody>
      </table>
      <p class="ref-method-mini">Modeled selection: ${split || "—"}. The 5% classifier is an explicit screening assumption, not a published engineering threshold. Small cokers, FCC/hydrocracker combinations and regional crude diets can differ materially from these example slates.</p>

      <p class="ref-method-h">2 · Yield slates — % of crude charge (medium sour crude)</p>
      <table class="ref-table ref-method-table">
        <thead><tr><th>Product</th>${headCells}</tr></thead>
        <tbody>${slateBody}</tbody>
      </table>
      <p class="ref-method-mini">Refinery fuel and processing gain are textbook balance memos, not additional products. Liquid products + coke equivalent + refinery fuel = 100% + processing gain. The coke percentage is treated as barrel-equivalent solely for this scenario; it is not a weight percentage or liquid volume. No density-free mass conversion is applied to weight yields.</p>

      <p class="ref-method-h">3 · Unit conversions</p>
      <table class="ref-table ref-method-table">
        <thead><tr><th>From</th><th class="num">Factor</th></tr></thead>
        <tbody>
          <tr><td>1 barrel → US gallons</td><td class="num">× ${BBL_TO_GAL}</td></tr>
          <tr><td>1 barrel → litres</td><td class="num">× ${BBL_TO_L}</td></tr>
          <tr><td>kbbl/d → bbl/d</td><td class="num">× 1,000</td></tr>
          <tr><td>Coke bbl-equivalent → short tons</td><td class="num">÷ ${COKE_BBL_EQ_PER_SHORT_TON}</td></tr>
        </tbody>
      </table>

      <p class="ref-method-h">4 · Estimated Nelson Complexity Index (this selection: ${ciLabel(regionCI)})</p>
      <p class="ref-method-mini">Installed capital-intensity measure: <strong>CI = 1 + &Sigma;(CF<sub>unit</sub> × capacity<sub>unit</sub> ÷ crude capacity)</strong>. It is independent of scenario utilization and is not a margin or yield measure. Owner/region averages use known-CI crude capacity only; unavailable values are not treated as zero.</p>
      <table class="ref-table ref-method-table">
        <thead><tr><th>Process unit</th><th class="num">Complexity factor</th></tr></thead>
        <tbody>
          <tr><td>Atmospheric distillation (base)</td><td class="num">1</td></tr>
          <tr><td>Catalytic cracking (FCC)</td><td class="num">6</td></tr>
          <tr><td>Hydrocracking</td><td class="num">6</td></tr>
          <tr><td>Delayed / fluid coking</td><td class="num">6</td></tr>
          <tr><td>Catalytic reforming</td><td class="num">5</td></tr>
          <tr><td>Alkylation</td><td class="num">10</td></tr>
          <tr><td>Aromatics / petrochemical</td><td class="num">15</td></tr>
          <tr><td>Thermal cracking / visbreaking</td><td class="num">2.75</td></tr>
          <tr><td>Hydrotreating</td><td class="num">2</td></tr>
          <tr><td>Hydrorefining / residual hydrotreating</td><td class="num">3</td></tr>
          <tr><td>Vacuum distillation</td><td class="num">2</td></tr>
          <tr><td>Isomerization</td><td class="num">15</td></tr>
          <tr><td>Hydrogen production (MMcfd)</td><td class="num">1</td></tr>
        </tbody>
      </table>
      <p class="ref-method-mini">Hydrogen production in MMcfd is compared numerically with crude capacity in kbbl/d per Kaiser's worked example; this is a complexity convention, not a physical gas-to-oil conversion. Purchased hydrogen feed is excluded. Hydrotreaters are classified by process before feed names (VGO, FCC gasoline or lube). Coverage and calendar-day versus stream-day capacity bases may differ from operator-reported CI; no accuracy benchmark is claimed.</p>

      <p class="ref-method-h">5 · Sources</p>
      <ul class="ref-method-cites">
        <li><strong>Leffler, <em>Petroleum Refining in Nontechnical Language</em> (2020), Table 20-1</strong> — configuration yield slates above (primary).</li>
        <li><strong>Fahim et&nbsp;al., <em>Fundamentals of Petroleum Refining</em>, Chapter 6</strong> — visbreaking and coking are distinct processes.</li>
        <li><strong>Kaiser, de&nbsp;Klerk, Gary &amp; Handwerk, <em>Petroleum Refining: Technology, Economics, and Markets</em> (2019), Tables 7.1 and 7.6</strong> — Nelson factors and a worked hydrogen-inclusive example.</li>
        <li><a href="https://www.eia.gov/dnav/pet/tbldefs/pet_pnp_capfuel_tbldef2.asp" target="_blank" rel="noopener noreferrer">EIA petroleum definitions</a> — coke reporting conversion, 5 barrels per short ton.</li>
        <li><a href="https://www.eia.gov/tools/glossary/index.php?id=R" target="_blank" rel="noopener noreferrer">EIA refinery-yield definitions</a> — reported yields also account for other inputs and product adjustments; this simplified scenario is not an EIA production estimate.</li>
      </ul>
      <p class="ref-method-mini">The default 100% utilization is a nameplate scenario. The selected production month does not establish refinery runs. Turnarounds, crude assays, unit constraints, imports, blending components and changing product specifications are not modeled. Refinery capacity is a dated snapshot, not a live measurement.</p>
    `;
  }

  function render() {
    const body = document.getElementById("refBody");
    if (!body) return;
    body.innerHTML = view.tab === "units" ? renderUnits()
      : view.tab === "owners" ? renderOwners()
      : view.tab === "plants" ? renderPlants()
      : view.tab === "method" ? renderMethod()
      : renderProducts();
  }

  panel.querySelector("#refTabs").addEventListener("click", (e) => {
    const b = e.target.closest("[data-ref-tab]"); if (!b) return;
    view.tab = b.dataset.refTab;
    panel.querySelectorAll(".ref-tab").forEach(t => t.classList.toggle("active", t === b));
    render();
  });
  panel.querySelector("#refUnits").addEventListener("click", (e) => {
    const b = e.target.closest("[data-ref-unit]"); if (!b) return;
    view.unit = b.dataset.refUnit;
    panel.querySelectorAll(".ref-unit").forEach(t => t.classList.toggle("active", t === b));
    render();
  });
  panel.querySelector("#refCsv").addEventListener("click", () => {
    const csvCell = value => {
      let s = String(value ?? "");
      if (/^[\s]*[=+@-]/.test(s)) s = "'" + s;
      return '"' + s.replace(/"/g, '""') + '"';
    };
    const numeric = value => Number.isFinite(value) ? value.toFixed(3) : "";
    const lines = [["Refinery","Owner","PADD","Country","Status","Config","Model_available","Capacity_basis","Estimated_Nelson_CI","Crude_capacity_kbbl_d","Scenario_utilization_pct","Modeled_feed_kbbl_d","Gasoline_kbbl_d","Distillate_kbbl_d","Jet_kbbl_d","Resid_kbbl_d","LPG_kbbl_d","Coke_short_ton_d","Coke_bbl_equivalent_per_short_ton"].map(csvCell).join(",")];
    for (const r of rows) {
      lines.push([
        r.name, r.owner, r.padd, r.country, r.status, CONFIG_LABEL[r.cls], r.modeled ? "yes" : "no", r.basis,
        numeric(r.ci), r.crude ? numeric(r.crude) : "", numeric(utilization), r.modeled ? numeric(r.feed) : "",
        numeric(r.products.gasoline), numeric(r.products.distillate), numeric(r.products.jet),
        numeric(r.products.resid), numeric(r.products.lpg), numeric(refProductFmt("coke", r.products.coke, "bbl").raw),
        COKE_BBL_EQ_PER_SHORT_TON,
      ].map(csvCell).join(","));
    }
    const blob = new Blob(["\uFEFF" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "refinery_selection.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  });

  render();
}

// ============================================================
// AESO / ATCO POWER STATUS OVERLAY  (auto-refreshed snapshot)
// ------------------------------------------------------------
// Data: public/data/aeso_power_status.json, rebuilt every 30 min by the
// refresh-aeso-power GitHub Actions workflow from the public AESO Current
// Supply Demand report. Site cogeneration output (TNG vs MC) is a
// power-status proxy for the linked production site — dashed halos on the
// map — plus a panel with grid metrics and the ATCO-heritage fleet.
// ============================================================

const POWER_DATA_PATH = "public/data/aeso_power_status.json";

Object.assign(state, {
  powerEnabled: false,
  powerData: null,
  powerLoading: false,
  powerError: null,
  powerLayer: null,
});

function powerStatusColor(u) {
  if (u === null || u === undefined) return "#6b7280";
  if (u >= 0.7) return "#16a34a";   // running strong
  if (u >= 0.3) return "#d97706";   // reduced
  if (u > 0)    return "#dc2626";   // barely running
  return "#dc2626";                 // offline
}

function powerStatusLabel(u) {
  if (u === null || u === undefined) return "no data";
  if (u >= 0.7) return "running";
  if (u >= 0.3) return "reduced";
  if (u > 0)    return "low";
  return "zero reported output";
}

function powerSnapshotStale(data = state.powerData, now = Date.now()) {
  const published = Date.parse(data?.observed_at || "");
  return !Number.isFinite(published) || now - published > 90 * 60000 || published > now + 5 * 60000;
}

async function fetchPowerData() {
  if (state.powerLoading) return false;
  state.powerLoading = true;
  state.powerError = null;
  updatePowerToggleUI();
  try {
    // Cache-bust so the 30-minute snapshots come through GitHub Pages caching.
    const data = await requestJson(`${POWER_DATA_PATH}?t=${Math.floor(Date.now() / 60000)}`);
    if (!Array.isArray(data.site_cogen) || !data.generated_at || !data.system) throw new Error("Invalid AESO snapshot");
    state.powerData = data;
  } catch (err) {
    state.powerError = err.message || String(err);
  }
  state.powerLoading = false;
  updatePowerToggleUI();
  return !state.powerError;
}

function powerHaloTooltip(s) {
  const u = s.utilization;
  const rows = [
    ["Observed", `${formatDateTime(state.powerData?.observed_at)}${powerSnapshotStale() ? " · STALE OR UNTIMED SNAPSHOT" : ""}`],
    ["Status", s.net_to_grid ? "Net export reading; site generation is not established" : `${powerStatusLabel(u)}${Number.isFinite(u) ? ` · ${(u * 100).toFixed(0)}% of capability` : ""}`],
    [s.net_to_grid ? "Net export / gross MC" : "Cogen output / capability", `${Number.isFinite(s.tng_mw) ? s.tng_mw : "—"} / ${Number.isFinite(s.mc_mw) ? s.mc_mw : "—"} MW`],
    ["AESO asset", `${s.aeso_name} (${s.aeso_code})`],
    ["Operator", s.operator],
    s.atco_heritage ? ["Fleet", "ATCO-heritage (Heartland)"] : null,
  ].filter(Boolean)
    .map(([l, v]) => `<span class="pt-route-label">${escapeHtml(l)}</span><span class="pt-route-val">${escapeHtml(String(v))}</span>`)
    .join("");
  return `<div><strong>${escapeHtml(s.site)}</strong>` +
    `<div class="pt-sub">Site cogeneration — power-status proxy, not metered site load</div>` +
    `<div class="pt-route">${rows}</div></div>`;
}

// Snap each halo to the app's own asset marker coordinates (matched by
// display name), so the ring sits exactly around the site's circle on the
// map. The JSON's baked lat/lon is only a fallback for non-production sites
// (e.g. Strathcona Refinery).
let _powerAssetLookup = null;
function powerAssetLookup() {
  if (_powerAssetLookup) return _powerAssetLookup;
  _powerAssetLookup = new Map();
  for (const asset of state.assets || []) {
    const name = String(asset.display_name || "").trim().toLowerCase();
    const lat = Number(asset.latitude), lon = Number(asset.longitude);
    if (!name || asset.latitude == null || asset.longitude == null || !Number.isFinite(lat) || !Number.isFinite(lon)) continue;
    if (!_powerAssetLookup.has(name)) _powerAssetLookup.set(name, [lat, lon]);
  }
  return _powerAssetLookup;
}

function powerHaloLatLng(s) {
  const lookup = powerAssetLookup();
  for (const name of s.asset_names || []) {
    const hit = lookup.get(String(name).trim().toLowerCase());
    if (hit) return hit;
  }
  return [s.lat, s.lon];
}

function renderPowerLayer() {
  if (!state.map || !window.L) return;
  if (state.powerLayer) {
    state.map.removeLayer(state.powerLayer);
    state.powerLayer = null;
  }
  if (!state.powerEnabled || !state.powerData?.site_cogen?.length) return;
  const markers = state.powerData.site_cogen.map((s) => {
    const color = powerSnapshotStale() || s.net_to_grid ? "#6b7280" : powerStatusColor(s.utilization);
    const halo = L.circleMarker(powerHaloLatLng(s), {
      radius: 15,
      color,
      weight: 2,
      dashArray: "5 4",
      fill: false,
      opacity: 0.9,
      interactive: true,
    });
    halo.bindTooltip(powerHaloTooltip(s), { sticky: true, opacity: 0.96, className: "pipeline-tip railway-tip" });
    return halo;
  });
  state.powerLayer = L.layerGroup(markers).addTo(state.map);
}

function renderPowerPanel() {
  const existing = document.getElementById("powerPanel");
  if (existing) existing.remove();
  if (!state.powerEnabled || !state.powerData) return;
  const d = state.powerData;
  const sys = d.system || {};
  const fmtMW = (v) => (v === null || v === undefined ? "–" : `${Math.round(v).toLocaleString("en-CA")} MW`);
  const cogenRows = (d.site_cogen || []).map((s) => `
    <tr>
      <td><i class="pw-dot" style="background:${powerSnapshotStale(d) || s.net_to_grid ? "#6b7280" : powerStatusColor(s.utilization)}"></i>${escapeHtml(s.site)}${s.net_to_grid ? " (net export)" : ""}</td>
      <td class="num">${Number.isFinite(s.tng_mw) ? s.tng_mw : "—"}</td>
      <td class="num">${Number.isFinite(s.mc_mw) ? s.mc_mw : "—"}</td>
      <td class="num">${s.net_to_grid || !Number.isFinite(s.utilization) ? "—" : (s.utilization * 100).toFixed(0) + "%"}</td>
    </tr>`).join("");
  const atcoRows = (d.atco_fleet || []).map((a) => `
    <tr>
      <td><i class="pw-dot" style="background:${powerSnapshotStale(d) ? "#6b7280" : powerStatusColor(a.utilization)}"></i>${escapeHtml(a.name)}</td>
      <td>${escapeHtml(a.fuel || "")}</td>
      <td class="num">${Number.isFinite(a.tng_mw) ? a.tng_mw : "—"}</td>
      <td class="num">${Number.isFinite(a.mc_mw) ? a.mc_mw : "—"}</td>
    </tr>`).join("");
  const panel = document.createElement("div");
  panel.id = "powerPanel";
  panel.innerHTML = `
    <div class="pw-header">
      <div>
        <strong>Alberta grid & site power</strong>
        <span class="pw-sub">AESO ${escapeHtml(d.aeso_last_update || "")} · refresh scheduled every 30 min</span>
      </div>
      <button id="powerPanelClose" class="ref-close" title="Close">&#x2715;</button>
    </div>
    <div class="pw-stats">
      <span><em>Alberta load</em>${fmtMW(sys.alberta_internal_load_mw)}</span>
      <span><em>Generation</em>${fmtMW(sys.total_net_generation_mw)}</span>
      <span><em>Interchange</em>${fmtMW(sys.net_actual_interchange_mw)}</span>
    </div>
    <div class="pw-body">
      ${powerSnapshotStale(d) ? '<p class="pw-stale">Stale snapshot. These values do not establish current site conditions.</p>' : ""}
      ${state.powerError ? `<p class="pw-stale">Refresh failed: ${escapeHtml(state.powerError)}</p>` : ""}
      <p class="pw-note">Oil-sands / refining site cogeneration (map halos) — output vs capability:</p>
      <table class="pw-table"><thead><tr><th>Site</th><th class="num">TNG</th><th class="num">MC</th><th class="num">Util</th></tr></thead>
        <tbody>${cogenRows}</tbody></table>
      <p class="pw-note">ATCO-heritage fleet (Heartland Generation):</p>
      <table class="pw-table"><thead><tr><th>Unit</th><th>Fuel</th><th class="num">TNG</th><th class="num">MC</th></tr></thead>
        <tbody>${atcoRows}</tbody></table>
      <p class="pw-foot">Cogeneration output does not establish a refinery or production-site outage. Net-to-grid units can report zero export while serving local demand. Source: AESO Current Supply Demand.</p>
    </div>`;
  document.getElementById("map").appendChild(panel);
  document.getElementById("powerPanelClose").addEventListener("click", () => {
    state.powerEnabled = false;
    panel.remove();
    renderPowerLayer();
    updatePowerToggleUI();
  });
}

function updatePowerToggleUI() {
  const btn = document.getElementById("powerToggle");
  if (!btn) return;
  if (state.powerLoading) {
    btn.textContent = "Loading...";
    btn.className = "railway-toggle-btn loading";
  } else if (state.powerEnabled) {
    btn.textContent = powerSnapshotStale() ? "Power (stale)" : "Power (on)";
    btn.className = "railway-toggle-btn active";
  } else {
    btn.textContent = state.powerError ? "Power unavailable · retry" : "Power";
    btn.className = "railway-toggle-btn";
    if (state.powerError) btn.title = `Power status unavailable: ${state.powerError}`;
  }
}

(function initPowerToggle() {
  const btn = document.getElementById("powerToggle");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    if (state.powerEnabled) {
      state.powerEnabled = false;
      renderPowerLayer();
      renderPowerPanel();
      updatePowerToggleUI();
      return;
    }
    const ok = await fetchPowerData();
    if (!ok) return;
    state.powerEnabled = true;
    renderPowerLayer();
    renderPowerPanel();
    updatePowerToggleUI();
  });
  setInterval(async () => {
    if (!state.powerEnabled || document.hidden) return;
    await fetchPowerData();
    renderPowerLayer();
    renderPowerPanel();
  }, 5 * 60000);
})();
