# Western Canada Production Exposure

Local ETL and map dashboard for Western Canada crude production exposure work.

## Run The ETL

```powershell
& 'C:\Users\aftik\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\run_etl.py
```

To refresh raw public-source files into `data/raw` first:

```powershell
& 'C:\Users\aftik\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\run_etl.py --download
```

The ETL keeps records from `2015-01-01` onward, writes `data/processed/production.db`, and exports app-ready files under `public/data`.

## Rebuild Market Access Pipelines

```powershell
python scripts\build_market_access_pipelines.py
```

This writes `public/data/market_access_pipelines.geojson`, a compact route-level layer for major Canadian crude export/import and diluent corridors plus named market hubs. Canadian federally regulated liquids are selected from the public CER pipeline systems FeatureServer (including Milk River and the Aurora border segment). U.S. continuations are selected from public EIA ArcGIS FeatureServers, including the Seaway JV leg from Cushing to the Gulf Coast; EIA does not expose the Trans Mountain Puget Sound line under any name, so the Sumas-to-Ferndale/Cherry Point and Anacortes legs use a clearly labelled curated approximate corridor. Gulf Coast (Nederland/Port Arthur, Houston) and Flanagan hubs are included.

To refresh current public crude tariff rows shown in market hub tooltips:

```powershell
python scripts\build_market_access_tariffs.py
```

This writes `public/data/market_access_tariffs.json`. It keeps operator-published currencies, fixed and variable toll components where available, additive and included charges, conditional charges, loss allowances, per-barrel conversions for cubic-metre tariffs, effective dates, status, and PDF page links with the document name.

## Rebuild Railways

```powershell
python scripts\build_railway_layer.py
```

This writes `public/data/railways.geojson`. It covers Canadian and U.S. main rail and major industrial-lead linework from the BTS/FRA North American Rail Network. It also adds all EIA crude-by-rail terminals and EIA petroleum/refined-product terminals, plus curated Canadian crude/diluent/transload and refined-product terminals from public Suncor, Torq, Gibson, USDG, Keyera, and Bruderheim/Cenovus terminal references.

By default the ETL caches Petrinex AB monthly volumetric API files from
`2022-01` through the workbook's latest actual month. `2022-01` is the earliest
public monthly API period verified by this ETL; older `2017-01` through
`2021-12` volume URLs returned 404 in testing. To override the Petrinex window:

```powershell
& 'C:\Users\aftik\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\run_etl.py --petrinex-start 2022-01
```

## AESO / ATCO Power Status (auto-refreshed)

The map's **Power** button overlays dashed status halos on oil-sands and refining
sites from their AESO-reported cogeneration output (TNG vs max capability), plus a
panel with Alberta grid metrics and the ATCO-heritage (Heartland) fleet.

`public/data/aeso_power_status.json` is rebuilt automatically every 30 minutes by
`.github/workflows/refresh-aeso-power.yml`, which runs
`scripts/build_aeso_power_status.py` against the public AESO Current Supply Demand
report and commits the snapshot — no manual refresh needed. Run the script locally
to refresh on demand. Cogen output is a public power-status proxy for each site,
not metered facility consumption.

## Email Alerts (power drops & fires near assets)

`scripts/check_alerts.py` runs in the same 30-minute workflow and emails a
recipient list when something changes:

- **Power down** — a monitored site's cogen output falls below **20%** of
  capability for 2 consecutive checks (~1 h); a **recovery** email is sent when
  it climbs back above **50%**. Thresholds: `data/alerts/config.json`.
- **Fires** — a new active wildfire within **10 km** of any mapped asset, using
  Government of Alberta (Alberta Wildfire) and Government of B.C. (BC Wildfire
  Service) feeds only (no satellite hotspot data). Escalation email if it goes
  Out of Control; close-out email when contained.

Alerts fire on transitions only (state in `data/alerts/state.json`, committed by
the bot); the first run baselines existing conditions without emailing. To enable
sending, add repo **Actions secrets**: `RESEND_API_KEY` (from resend.com) and
`ALERT_EMAILS` (comma-separated recipients); optional `ALERT_FROM`. Without
secrets the workflow still runs and logs alerts without sending.

## Run The App



```powershell
& 'C:\Users\aftik\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m http.server 5173
```

Then open `http://localhost:5173`.

## Notes

- ST53/ST39 are the oil-sands source layers: ST53 in-situ schemes, ST39 mined bitumen, and ST39 Section 5 synthetic crude by upgrader. Historical ST53/ST39 rows are still normalized from the analyst workbook; current-month ST39 synthetic crude is reconciled from the cached official AER ST39 XLS when local R/readxl is available.
- ST53/ST39 oil-sands assets are located from AER data first: Scheme Approval Spatial Data centroids for in-situ and mined project footprints, ST44 active schemes as the approval/name bridge, and ST102 facility points for upgrader/facility locations. Non-specific workbook buckets such as `Other`/`Assets` are kept in the database but excluded from map markers.
- Petrinex AB OIL/PROD rows are converted from m3/month to bbl/d and mapped by operator plus DLS site using the current public well-to-facility link where available. Zero or negative site-months are not exported to the monthly conventional map layer.
- Petrinex AB, Saskatchewan, BCER, NDIC, Manitoba, and Montana BOGC well-level history is exported as date-specific compact JSON under `public/data/monthly/`, so the browser loads the conventional layer only for the selected month instead of loading all well records up front. Monthly files use integer asset references into `assets.json` to keep GitHub Pages storage small.
- BC Petrinex reference files are cached, but the public BC page does not expose a tested monthly volumetric endpoint equivalent to Alberta's `/AB/Vol/YYYY-MM/CSV` API. BC production volumes come from BCER well production data; the app now exports both `Oil_prod_vol (m3)` as conventional crude and `Cond_prod_vol (m3)` as condensate production.
- Saskatchewan crude oil comes from Petrinex SK monthly volumetric API files, OIL/PROD rows only, mapped by current Petrinex SK well infrastructure DLS where available. The default SK cache starts at 2024-01 and runs through the latest completed public month.
- North Dakota crude oil comes from the NDIC Monthly Production Report Excel files, Oil sheet only. The default ETL cache starts at 2024-01 so the seasonality panel can compare 2024, 2025, and 2026-to-date while staying under the GitHub storage budget; use `--nd-start YYYY-MM` to shrink or expand that well-level history.
- Manitoba crude oil comes from the Province of Manitoba monthly well production Excel ZIP, OIL rows only, mapped from the UWI DLS. The default Manitoba cache starts at 2024-01.
- Montana Bakken crude oil comes from Montana Board of Oil and Gas Conservation bulk reporting files: Historical Well Production for monthly `BBLS_OIL_COND` and Complete Well List for coordinates. The ETL filters to Bakken and Three Forks formation rows only and defaults to 2024-01 to match the NDIC-style recent history window.
- `data/sources.json` records the official AER and Petrinex URLs used by the raw-cache refresh.
- `data/asset_registry.csv` remains as a fallback for assets not resolved from AER spatial sources.
- `public/data/aer_scheme_approvals.geojson` is generated from the cached AER Scheme Approval shapefile and is used by the map's AER Sites overlay. It replaces the earlier rough hand-drawn Athabasca/Cold Lake/Peace River basin polygons.
- `public/data/aer_st102_oil_sands_facilities.geojson` is generated from the cached AER ST102 Facility List Shapefile and adds active oil-sands facility dots to the AER Sites overlay.
- `public/data/market_access_pipelines.geojson` is generated by `scripts/build_market_access_pipelines.py`. It stays intentionally small for GitHub Pages and separates major market-access routes and hubs from the much larger AER feeder pipeline context.
- `public/data/market_access_tariffs.json` is generated by `scripts/build_market_access_tariffs.py` and powers the tariff-rich market hub hover tooltips and click-to-pin market hub popups.
- `public/data/railways.geojson` is generated by `scripts/build_railway_layer.py` and lazy-loaded by the Railways button. The rail layer includes all Canadian main/industrial rail corridors, connected U.S. supply-chain rail corridors, U.S. EIA crude/product terminals, and curated Canadian crude/product rail terminals (including the Pembina/Imperial Edmonton Rail Terminal and the Pembina/Keyera Alberta Crude Terminal) while staying within the GitHub storage budget. Rail lines are coloured by owning railroad (RROWNER1): CN, CPKC (incl. KCS), BNSF, UP, CSX, NS, passenger/commuter, and regional/short lines.
- `data/processed/dls_centroids.csv` caches DLS-to-lat/lon conversions. The ETL uses the AGS ATS v4.1 web converter for the highest-volume Alberta DLS sites it has not seen before, then uses a clearly labelled approximate DLS centroid fallback for the rest.
- Values are stored in `bbl/d` and also exported as `kbbl/d` for dashboard display. Petrinex AB/SK, BCER, and Manitoba monthly m3 volumes are converted using 6.28981077 bbl per m3 divided by calendar days in the production month. NDIC and Montana BOGC monthly crude barrels are divided by calendar days. Workbook-normalized ST39/ST53 rows are already bbl/d.
- `public/data/manifest.json` includes source coverage, filter-aware date totals, and data-quality warnings so the app can flag partial source coverage instead of silently treating every month as equally complete. The ETL flags trailing coverage gaps (a source whose cache ends while other sources continue, e.g. Petrinex AB after its final cached month), and the app also derives the same warning client-side from `source_coverage`, so months like 2026-02+ show a partial-coverage warning instead of silently dropping from ~8,200 to ~3,600 kbbl/d.
- If a public endpoint is unavailable during `--download`, the ETL logs the failure in `public/data/manifest.json` and still rebuilds the local store from the workbook seed.
