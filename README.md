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

By default the ETL caches Petrinex AB monthly volumetric API files from
`2022-01` through the workbook's latest actual month. `2022-01` is the earliest
public monthly API period verified by this ETL; older `2017-01` through
`2021-12` volume URLs returned 404 in testing. To override the Petrinex window:

```powershell
& 'C:\Users\aftik\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\run_etl.py --petrinex-start 2022-01
```

## Run The App

```powershell
& 'C:\Users\aftik\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m http.server 5173
```

Then open `http://localhost:5173`.

## Notes

- ST53/ST39 are the oil-sands source layers: ST53 in-situ schemes, ST39 mined bitumen, and ST39 Section 5 synthetic crude by upgrader. Historical ST53/ST39 rows are still normalized from the analyst workbook; current-month ST39 synthetic crude is reconciled from the cached official AER ST39 XLS when local R/readxl is available.
- ST53/ST39 oil-sands assets are located from AER data first: Scheme Approval Spatial Data centroids for in-situ and mined project footprints, ST44 active schemes as the approval/name bridge, and ST102 facility points for upgrader/facility locations. Non-specific workbook buckets such as `Other`/`Assets` are kept in the database but excluded from map markers.
- Petrinex AB OIL/PROD rows are converted from m3/month to bbl/d and mapped by operator plus DLS site using the current public well-to-facility link where available. Zero or negative site-months are not exported to the monthly conventional map layer.
- Petrinex AB history is exported as date-specific JSON under `public/data/monthly/`, so the browser loads the conventional layer only for the selected month instead of loading all 1.49 million conventional records up front.
- BC Petrinex reference files are cached, but the public BC page does not expose a tested monthly volumetric endpoint equivalent to Alberta's `/AB/Vol/YYYY-MM/CSV` API. BC production volumes come from BCER well production data; the app now exports both `Oil_prod_vol (m3)` as conventional crude and `Cond_prod_vol (m3)` as condensate production.
- `data/sources.json` records the official AER and Petrinex URLs used by the raw-cache refresh.
- `data/asset_registry.csv` remains as a fallback for assets not resolved from AER spatial sources.
- `public/data/aer_scheme_approvals.geojson` is generated from the cached AER Scheme Approval shapefile and is used by the map's AER Sites overlay. It replaces the earlier rough hand-drawn Athabasca/Cold Lake/Peace River basin polygons.
- `public/data/aer_st102_oil_sands_facilities.geojson` is generated from the cached AER ST102 Facility List Shapefile and adds active oil-sands facility dots to the AER Sites overlay.
- `data/processed/dls_centroids.csv` caches DLS-to-lat/lon conversions. The ETL uses the AGS ATS v4.1 web converter for the highest-volume Alber