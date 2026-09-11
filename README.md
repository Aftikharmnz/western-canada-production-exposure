# Western Canada Production Exposure

An interactive map of production, pipelines, rail and terminals, refineries, wildfire proximity, weather, and Alberta power output.

## Automatic official-data updates

GitHub Actions now discovers regulator publications, downloads their source files, rebuilds a separate candidate dataset, validates it, archives changed official inputs, and publishes the app. The analyst forecast spreadsheet is no longer read. Its derived history and forecasts have been removed from the app; the original personal file remains untouched on disk.

See the [ELT design and operating guide](docs/ELT_PIPELINE.md), [official source discovery contracts](docs/OFFICIAL_SOURCE_DISCOVERY.md), and [reference-source automation](docs/REFERENCE_SOURCE_AUTOMATION.md).

| Update | Schedule in UTC | Result |
| --- | --- | --- |
| Production | Daily at 07:17 | Official actuals; the latest three published months are checked for revisions |
| Historical revisions | Sunday production run | Annual AER reports and historical publication revision tokens are rechecked; changed historical files are fetched |
| AER feeder pipelines and installations | Sunday at 08:37 | Official SHP/CSV archives update the full geometry, categories, tiles, and index together; any family failure blocks publication |
| Market-access pipelines and railways | Sunday at 08:37 | Validated service geometry; unavailable upstream refreshes preserve the prior layer with a warning |
| Refinery and tariff publications | Production and infrastructure checks | Independent EIA annual crude-capacity observations update automatically; changed reviewed facts are flagged for review |
| AESO power | Every 30 minutes | Existing power snapshot and alert workflow |

These are best-effort polling schedules. Data appears after the regulator publishes it and a successful scheduled run completes; reporting lags are visible in **Data status**. The job requires GitHub Actions and the repository's built-in token, with no additional production-data API keys or separate hosting service. Private-repository Actions usage is subject to the account's allowance and billing settings.

A failed candidate does not replace published observations. The previous Git commit is the durable normalized history. Changed raw production inputs, AER pipeline and installation SHP/CSV ZIP archives, and imported EIA capacity reports are saved as checksummed GitHub Release attachments before the corresponding data commit. Market-access and railway geometry remain normalized Git snapshots. Replay uses a baseline commit plus subsequent source packages; older historical raw files were not all archived before this automation existed.

## Run or inspect a refresh

Use the **Refresh official application data** workflow's **Run workflow** button in GitHub Actions and choose production or infrastructure mode. Run logs, validation results, changed-file lists, and source archive links explain each release. A manual run follows the same validation and publication rules as a scheduled run.

For local development, install Python 3.12+ and R (the workflow uses R 4.5.2), then install the workflow's Python dependencies and pinned `readxl` 1.4.5 reader:

```powershell
python -m pip install -r scripts/requirements-elt.txt
Rscript scripts/install_elt_r.R
```

Use a fresh work directory for each candidate:

```powershell
python scripts/elt_pipeline.py --mode production --work-dir data/processed/review-001
```

This command builds and validates a candidate without publishing it. To exercise only AER using already downloaded official inputs:

```powershell
python scripts/elt_pipeline.py --mode production --sources aer --offline --skip-references --work-dir data/processed/review-002
```

The lower-level importer accepts source groups `aer`, `petrinex-ab`, `petrinex-sk`, `bcer`, `ndic`, `manitoba`, and `montana`. An explicit historical refresh uses `--history-start YYYY-MM`; older source formats must pass the same schema checks. Do not point candidate output at `public/data`.

```powershell
python scripts/run_etl.py --sources aer --download --history-start 2017-01 --output-dir data/processed/aer-review --result-json data/processed/aer-review-result.json
```

Check a candidate using its actual directory:

```powershell
python scripts/validate_production_data.py --data-dir data/processed/review-001/candidate
python scripts/validate_infrastructure_layers.py --data-dir data/processed/review-001/candidate
```

## Run the app and tests

```powershell
python -m http.server 8766 --bind 127.0.0.1
```

Open `http://localhost:8766/index.src.html` for the source interface, or `/` to test the existing encrypted entry page.

```powershell
node --check src/main.js
node --test scripts/test_app_runtime.cjs scripts/test_refinery_model.cjs
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/validate_production_data.py
python scripts/validate_infrastructure_layers.py
```

The offline tests make no live requests or alert deliveries. R extraction fixtures require `readxl`. `python scripts/audit_live_apis.py` separately checks the public browser endpoints without sending alerts.

GitHub Pages deploys encrypted `index.html` from `main`. For HTML changes, edit `index.src.html`, regenerate the protected wrapper with `scripts/encrypt_site.sh`, and commit both files. Data-only refreshes preserve the existing password and require no encryption secret. The deployment artifact excludes plaintext HTML, raw downloads, private inputs, and source books. JavaScript and map data remain assets of the existing static hosting design.

## Source and interpretation notes

- AER ST53/ST39 production is imported directly from current and annual publications. Publicly linked AER history starts in 2017; analyst-derived 2015-2016 history and Saskatchewan upgrader forecasts are removed. ST53 is in m³ per calendar day; ST39 is in monthly m³.
- Monthly Petrinex AB/SK, BCER, and Manitoba m³ become bbl/d using 6.28981077 bbl/m³ and the month's calendar-day count. NDIC and Montana monthly barrels are divided by calendar days. The app displays kbbl/d.
- Alberta conventional crude excludes explicitly classified CR-BIT wells to reduce overlap with ST53. BCER provides well oil and condensate. Saskatchewan uses OIL/PROD rows. Montana is limited to Bakken and Three Forks formations.
- AER footprints and ST44/ST102 references locate oil-sands assets. Well layers use published coordinates or labelled DLS approximations. These are not surveyed pipeline alignments or exhaustive inventories of every gathering pipe, private spur, and facility.
- AER feeder pipelines and installations update automatically from the regulator's mapped SHP/CSV archives. The feeder map preserves its Operating/Permitted liquid-substance classes; installation menus retain their existing types and Operating/Permitted/Suspended scope. Source geometry, menu categories, tiles, and index are validated together before publication.
- Compact monthly files reference the matching `assets.json`. The asset table, month shards, manifest, seasonality, and geometry must be published together.
- Gross stream sums can include the same material at multiple processing stages, such as bitumen and synthetic crude, or raw and finished NGLs. They measure selected activity, not net regional supply.
- Refinery product outputs are utilization scenarios using supported configurations and reviewed capacities. Missing inputs remain unavailable. The independent EIA January 1 survey is not automatically joined to IIR plant identities or substituted for more recent operating-status evidence.
- Named market-access routes use CER/EIA geometry where available and labelled approximations elsewhere. Optional EIA reference switches expose crude, product, and HGL networks. Railway service failures preserve the last validated geometry and remain visible as a limitation.
- Tariff rows preserve operator currencies, effective dates, included/additive charges, and document links. New or changed tariff/operator publications require factual review before their rates, ownership, or status replace the reviewed values. Rebuilding `scripts/build_market_access_tariffs.py` exports the reviewed snapshot; it does not by itself verify a new tariff document.

The [production audit](docs/PRODUCTION_AUDIT.md), [infrastructure audit](docs/INFRASTRUCTURE_AUDIT_2026_09.md), [refinery methodology](docs/REFINERY_PRODUCTS_MODEL.md), and [application audit](docs/APP_AUDIT_2026_09.md) document the earlier audit and its corrections. Historical workbook descriptions in those audit reports are superseded by the ELT design above.

## Existing power and email alerts

The **Power** overlay uses AESO-reported generation versus capability as a site power-status proxy, not metered facility consumption. Its separate 30-minute workflow remains in place.

`scripts/check_alerts.py` retains the existing transition-based power and nearby wildfire alerts, configured in `data/alerts/config.json`. Delivery uses the existing optional repository secrets `RESEND_API_KEY`, `ALERT_EMAILS`, and `ALERT_FROM`. The new production/infrastructure jobs do not send emails or change recipients. Do not run the alert script merely to validate a data release.
