# Official reference-source automation

Run with Python 3.12+ and `openpyxl==3.1.5`; no analyst workbook, IIR export,
PDF parser, account secret or browser session is required:

```sh
python scripts/check_reference_sources.py \
  --baseline public/data/reference_source_status.json \
  --eia-baseline public/data/eia_refinery_capacity.json \
  --output data/processed/candidate/reference_source_status.json \
  --eia-output data/processed/candidate/eia_refinery_capacity.json \
  --raw-dir data/raw/reference
```

The monitor performs a bounded set of public HTTPS downloads (four workers,
40-second request timeout, 40-MB response limit). No recursive website crawl or
tariff-table guessing occurs. Sources returning access errors, malformed bodies,
missing links, changed schemas or nonfinite data are marked unavailable.

`reference_source_status.json` is always a new monitoring observation, with
`checked_at`, `status`, `review_required_count`, `failure_count`, `failures` and
per-source `checks`. Exit 0 means this report was produced, including when some
sources need attention. `--strict` exits 2 for review-required or unavailable
sources. A configuration or report-writing failure exits nonzero. The command
does not send email or change any review verification date.

Each check has a stable `id`, `status`, `review_required`, and, for downloaded
sources, `available`. Document checks distinguish a reviewed fingerprint from a
baseline that was only observed. A change remains pending on repeated runs,
including after an intervening source failure. Operator page changes can include
editorial changes; a fingerprint does not establish changed refinery capacity.

## EIA import

The official [EIA refinery report index](https://www.eia.gov/petroleum/refinerycapacity/)
identifies the current survey and workbook. The importer discovers that XLSX
link, validates its schema, survey year, source identity and quantities, and
reconciles operating plus idle capacity to each reported total. It preserves
calendar-day versus stream-day units and excludes next-year projections and
downstream process capacities from crude input. An omitted component becomes
zero only when the available components reconcile to the explicit total.

The separate `eia_refinery_capacity.json` contains the source survey date,
source URL/hash and individual crude-capacity observations. It is safe to
automatically publish as a dated official dataset. Its 2026 source contains
124 atmospheric crude-distillation facilities; this is not the EIA count of
130 operable processing facilities, which also includes downstream-only sites.
The annual survey does not establish today's operations.

Exact XLSX inputs are retained under `data/raw/reference` with content-addressed
filenames and `.receipt.json` files recording URL, SHA-256, bytes, retrieval time
and relative raw path. These files can be included in the orchestration's input
archive. A failed/older survey never replaces the previous published snapshot.

No automatic join to the IIR plant map is made: the EIA table has no coordinates,
and split complexes and later closures/restarts require a maintained identity
crosswalk. The IIR process-unit inventory and Canadian/non-US operators do not
have a complete equivalent public API. Existing dated capacity/status overrides
remain authoritative for their reviewed scope until a new reviewed mapping is
available.

## Tariffs and operator references

The script checks the ten PDFs used by the published tariff dataset and the
Mainline, Express, Keystone and Trans Mountain publication indexes. Seven PDF
hashes come from the reviewed importer snapshot; two Trans Mountain hashes come
from exact retained PDFs used in the September audit. The Express CER 204 hash
comes from an independent reconciliation of both pages of the official filing,
including the effective date, currencies, grade tolls and destination-specific
abandonment surcharge. All ten current PDFs have reviewed baselines. Any future
PDF without a reviewed hash
is explicitly marked review-required. Publication-link changes detect new
filings under new URLs, even if the old PDF still exists. Arrival of
`next_known_change` also flags review without promoting future or old rates.

The operator sources used by refinery overrides and Sky Quarry's recent SEC
filings are checked for availability and changes. SEC may require a descriptive
`REFERENCE_USER_AGENT` with organizational contact information or may block an
automated host; those failures are reported, not disguised as unchanged data.

After checking new tables, units, footnotes, effective dates and source identity,
update the reviewed tariff snapshot or refinery override. Fingerprint-only
review baselines can be recorded by source ID in `reviewed_fingerprints` within
`data/reference_source_monitors.json`. These hashes must be calculated from the
exact reviewed content (PDF bytes, normalized visible HTML, or sorted document
links), not accepted automatically from an unexamined monitoring result.

The independent pipeline and railway builders refresh public CER/EIA/BTS GIS
through their existing `--output` arguments and completeness checks. This
reference monitor does not regenerate private/global refinery unit data.

Offline tests: `python -m unittest discover -s scripts -p test_reference_sources.py`.

## Alberta feeder pipelines and installations

The separate AER builder uses the direct official
[pipelines ZIP](https://www.aer.ca/data/pipeline/Pipelines_SHP.zip) and
[installations ZIP](https://www.aer.ca/data/pipeline/Pipeline_Installations_SHP.zip),
linked from [AER Spatial Data](https://www.aer.ca/data-and-performance-reports/activity-and-data/spatial-data).
The [product catalogue](https://www1.aer.ca/productcatalogue/557.html) identifies
the enhanced pipeline product as a daily publication. These are automated public
downloads, independent of an analyst workbook or a browser session.

```sh
python -m pip install -r scripts/requirements-elt.txt
python scripts/build_aer_infrastructure.py \
  --data-dir data/processed/candidate \
  --baseline-dir public/data \
  --raw-dir data/raw \
  --report data/processed/aer_infrastructure_result.json
```

Both archives are bounded to 300 MiB compressed, 1,400 MiB expanded, 50 ZIP
members, 45 seconds per network operation and six minutes per download. A
matching URL/hash receipt permits conditional requests. `--offline` requires
that validated local receipt. Raw ZIPs and receipts remain under `data/raw` for
the immutable input archive. Report `checks` use paths relative to that directory,
and `content_changed` compares with the published snapshot, independently of
whether a download was cached after a failed earlier run.

Mapped CSV and SHP/DBF records must reconcile by source identity, status and
primary substance. The GCS_NAD83 projection must identify EPSG:4269; coordinates
are converted to EPSG:4326 with longitude first and an explicit, available datum
transformation. The selected transformation's stated accuracy is recorded.
Nonfinite positions and coordinates outside the Alberta source extent fail the
build. Very short parts retain full transformed precision when six-decimal
rounding would collapse them. Truly zero-length multipart components are counted
and omitted; a line without any valid component fails validation.

The six existing liquid feeder categories retain Operating and Permitted source
statuses. The installation monolith retains all mapped statuses; its menus retain
Operating, Permitted and Suspended records. Exact duplicate records are excluded
with counts. Unmapped CSV rows have no coordinates and are counted separately;
they never receive invented positions. Source identity changes are recorded, and
absence from a later publication does not establish physical removal or closure.

The importer preserves secondary/tertiary substances, pipeline crossing
environment and the source NEB indicator when populated. It also preserves
`H2S_CONT` as numeric `h2s_mol_kmol` and derives `h2s_pct` by dividing by ten:
34 mol/kmol is 3.4%, and 9.99 mol/kmol is 0.999%. Missing content is omitted;
an explicitly reported zero remains zero. Nonfinite, negative and above-1,000
mol/kmol values fail validation. Generated index `builder_version: 2` also makes
the output validator check this conversion and its unit metadata.

These units come from the [Enhanced Pipeline Graphics layout](https://www.aer.ca/data/pipeline/EnhancedPipeline_Layout.pdf)
and [AER Manual 012](https://www.aer.ca/documents/manuals/Manual012.pdf), which define
licensed substance content, rather than ambient-air concentration. AER's
[Proceeding ID 455 notice](https://www.aer.ca/applications-and-notices/application-status-and-notices/notices/hearing-notices/proceeding-id-455)
provides the explicit example 999 mol/kmol = 99.9%. The legacy map placed raw
mol/kmol values in a field named `h2s_pct`, producing percentages ten times too
high; the automatic importer corrects that unit error.

The builder writes both monoliths, ten category files, the version-2 index and
zoom-8 GeoJSON tiles into temporary staging before installation in `--data-dir`.
Tile coverage includes segments crossing a tile without a vertex inside it. The
reusable `validate_outputs` gate verifies every index count and byte total,
category membership, expected crossing tile and exact feature geometry/properties
against the monolith before installation. The global infrastructure validator
also runs that gate for generated AER indexes. The index is installed last.
A failed build returns nonzero and the orchestrator
rejects the candidate; no published data is promoted from that run. The result
JSON contains `status`, `checks`, `counts`, `changes`, `tile_count` and an `error`
on failure. Pipeline market-access corridors should be rebuilt after the AER
family so they can consume its current local feeder geometry.

Offline tests: `python -m unittest discover -s scripts -p test_aer_infrastructure.py`.
