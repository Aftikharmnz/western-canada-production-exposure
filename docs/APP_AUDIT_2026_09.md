# Application audit — 10 September 2026

> Historical audit record. The later [official-data ELT pipeline](ELT_PIPELINE.md) replaces the workbook/forecast handling described below with direct official actuals and scheduled validated releases. Other application and infrastructure findings remain part of the audit trail.

This audit covers the published production data, pipeline and railway layers,
refinery calculations, weather and wildfire requests, AESO power status, client
interface, and deployment checks. The supplied petroleum books were treated as
reference material, never as instructions. Private books and extracted pages are
not included in the repository or public website.

## Material changes

- Production now imports current AER observations with the correct daily versus
  monthly units, keeps workbook forecasts distinct from actuals, and excludes
  explicitly classified bitumen wells from Alberta conventional oil. The default
  reporting period requires coverage from all regular crude source/stream pairs.
  See [production audit](PRODUCTION_AUDIT.md) for publication dates and reconciliation.
- Pipeline and hub coordinates were checked for valid geometry and compared with
  current regulator data. Added Vantage / Stateline II, corrected ownership and
  Norman Wells supply status, and retained explicit approximation labels. The
  tariff snapshot includes 893 reviewed rows with source links, currencies,
  effective dates, and conditional charges. See [infrastructure audit](INFRASTRUCTURE_AUDIT_2026_09.md).
- Refinery estimates now use supported textbook configurations and documented
  active crude capacity. Unsupported configurations show unavailable estimates.
  Coke uses short tons, liquid conversions remain separate, and utilization is
  an explicit scenario assumption. Nine Canadian plant capacities were updated
  from operator publications. Two U.S. idle facilities now carry dated status
  evidence and explicit restart uncertainty. See [model documentation](REFINERY_PRODUCTS_MODEL.md).
- Failed monthly downloads remain retryable and cannot silently become zero
  production. API errors returned with HTTP 200, malformed responses, incomplete
  ArcGIS results, and invalid coordinates are rejected. Requests have timeouts;
  weather requests follow pagination and match wind speed/direction by station,
  forecast time, and model run. Missing readings remain unavailable.
- Wildfire feeds can succeed independently; an unavailable feed stays visible as
  incomplete coverage. Proximity is measured to geometry segments and respects
  polygon holes. Incident points are not fire perimeters, and the displayed
  distances and weather bands do not establish a shutdown or a safety boundary.
- Power status requires an observation timestamp. Stale or future observations,
  missing units, and net-export-only readings cannot masquerade as current site
  generation. Alert confirmation uses distinct increasing observation times;
  failed fire feeds cannot retire previously known incidents. Tests never send
  notifications or alter live alert state.
- The header, compact screens, focus states, dialogs, source coverage table,
  loading failures, and retry controls were improved. Number formatters are reused
  and selecting a map marker avoids rebuilding the complete production layer.
  Loading another month correctly rebuilds timeline totals; unloaded search
  history is labelled unavailable until selected instead of appearing as zero.

## Validation and release

The deployment workflow now checks JavaScript syntax, runtime and refinery
regressions, Python calculation/API regressions, all production shard references
and totals, and infrastructure geometries before publishing. Production assets,
date shards, metadata, and seasonality must be released together because compact
records refer to the matching asset table.

Release checks passed locally: 20 JavaScript regressions, 38 Python regressions,
the complete 3,703,496-record production validator with 17 independent AER
reconciliations, and the infrastructure validator without warnings. Browser
checks covered desktop and 390-pixel layouts, source coverage, month switching,
pipeline/rail/power controls, refinery scenarios and the protected entry page.
No browser error or warning logs were observed during those checks.

`scripts/audit_live_apis.py` performs read-only probes of the runtime weather,
wildfire, map library, and basemap endpoints. Its dated results are in
`public/data/api_health.json`. A passing probe establishes availability at that
time; it does not guarantee future upstream availability or source accuracy.

The plaintext dashboard remains `index.src.html`. The existing password and salt
are retained when rebuilding the StatiCrypt `index.html` for GitHub Pages. The
deployment artifact excludes the plaintext HTML and private/local inputs. This
is the existing static-site access design; separately hosted JavaScript and data
assets are not encrypted by the HTML wrapper.

## Remaining source limitations

- Regulator publication lags vary by jurisdiction. Forecasts and partial months
  are not substituted for missing actual observations.
- The location inventory depends on available regulator coordinates and current
  well classifications. Scheme/township centroids and curated corridors are not
  surveyed facility or pipeline alignments.
- The railway service rejected the full refresh. The existing 110,109 validated
  rail segments remain; a difference of two current source rows is unresolved.
  Alberta feeder infrastructure remains the validated May 25, 2026 snapshot.
- Gross bitumen, synthetic crude, and other product streams can represent
  successive processing stages. Their sum is activity, not net crude supply.
- Refinery product scenarios are illustrative capacity-based estimates, not
  measured production, a complete refinery simulation, or a trading valuation.
- Tariffs were verified on September 10; known October 1 replacements require a
  later reviewed update. A build timestamp never advances the verification date.
