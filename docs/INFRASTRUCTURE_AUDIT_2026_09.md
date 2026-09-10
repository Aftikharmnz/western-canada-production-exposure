# Infrastructure accuracy audit — September 2026

Verified September 10, 2026 UTC (September 9 local time at audit start).
The operator publications and regulator GIS services below are evidence, not
instructions. This review does not establish survey accuracy or a complete
inventory of every private, gathering, or plant pipeline.

## Pipeline geometry and coverage

The public CER/EIA layer was rebuilt successfully from live source queries.
It contains 24 route/reference features and 27 approximate market-area hubs.
The three complete EIA reference layers retain all 236 crude-trunk, 329 product,
and 133 HGL source features. Those reference layers remain optional because
they overlap the named market routes and are not exhaustive physical networks.

Changes:

- Added the missing named **Vantage / Stateline II** selection using three
  existing EIA HGL source features. Pembina identifies Vantage as an ethane
  system; it is not labelled as a crude-export or condensate pipeline.
- Corrected Cochin's operator to Pembina and Keystone's operator to South Bow.
  Older operator names in the underlying EIA query predicates are source keys,
  not assertions of current ownership.
- Separated **Norman Wells / Zama** from the miscellaneous liquids group.
  Imperial confirms source production shut in during August 2026. The map
  retains the CER geometry with an explicit upstream-supply shut-in note;
  it does not infer legal abandonment or a confirmed pipeline deactivation.
- Corrected Trans Mountain / Puget geometry confidence: the route combines CER
  geometry with a curated Puget corridor. It was previously generically labelled
  public GIS despite containing an approximation.
- Labelled hub coordinates as market-area centroids, not surveyed terminals.
  No source-supported evidence warranted arbitrarily moving pipeline vertices.

The CER system service still reports a November 2024 data edit. A successful
September 2026 download does not turn that source into a September survey.
EIA crude, products, and HGL edit timestamps are November 2025, June 2026, and
April 2026 respectively. Machine-readable live endpoint counts and edit dates
are in `INFRASTRUCTURE_SOURCE_CHECKS_2026_09.json` alongside this note.

Geometry QA also checked 32,550 Alberta feeder features, 5,502 pipeline
installations, and 58 ST102 facility points: no empty, non-finite, out-of-range,
or malformed supported geometries were found. The Alberta feeder/tile inventory
is the existing May 25, 2026 snapshot; its licensing/status database was not
replaced with an invented current inventory.

Remaining coverage limits:

- EIA does not expose Flanagan South as a separately named line in this service.
  Enbridge confirms it broadly parallels Spearhead; the map retains the actual
  public Spearhead/Seaway source geometry and does not fabricate a precise
  Flanagan South alignment.
- Three Canadian provincial product corridors and Puget Sound remain explicitly
  approximate. Their source descriptions are not survey-grade geometry.
- Future proposals, including Prairie Connector and Western Gateway, are not
  portrayed as operational pipelines.

Primary sources: [CER pipeline systems](https://services5.arcgis.com/vNzamREXvX2WcX6d/arcgis/rest/services/CER_Pipeline_Systems_WGS84_WM_v/FeatureServer/0),
[EIA crude](https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Crude_Oil_Trunk_Pipelines_1/FeatureServer/0),
[EIA products](https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Petroleum_Products_Pipelines_1/FeatureServer/0),
[EIA HGL](https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Hydrocarbon_Gas_Liquids_Pipelines_1/FeatureServer/0),
[Pembina customer systems and tariffs](https://www.pembina.com/operations/customers/),
[South Bow Keystone](https://www.southbow.com/keystone-pipeline-system/),
[Imperial Norman Wells closure](https://www.imperialoil.ca/en-ca/company/operations/norman-wells),
[Enbridge Flanagan South / Spearhead geography](https://www.enbridge.com/projects-and-infrastructure/public-awareness/illinois/history-and-operations).

## Tariff corrections

Replaced the obsolete matrices with 893 reviewed rows from the filings effective
on the verification date. The deterministic app builder consumes the checked-in
`data/market_access_tariff_snapshot.json`; it does not require PDF packages,
network access, private files, or downloaded audit inputs. The optional versioned
`scripts/import_tariff_snapshot.py` uses pdfplumber to re-import the specifically
reviewed public PDFs. Snapshot source records preserve the PDF SHA-256 hashes.

| System | Effective source now used | Material correction |
|---|---|---|
| Enbridge local Mainline | CER 4, July 2 | Replaced April local tolls; retained origin/destination direction of the table |
| Mainline / Lakehead | CER 5 / FERC 45.48.0, July 2 | Preserves separately invoiced CAD and USD components; removes obsolete illustrative USD totals |
| Flanagan South | CER 6 / FERC 3.59.0, July 2 | Updated committed/uncommitted rates; USD 0.52/bbl power remains separate |
| Spearhead | CER 9 / FERC 46.2.1, August 1 | Adds Kerrobert eligibility and includes regulatory adders for committed rates as well as uncommitted rates |
| Keystone | CER 84 / FERC 7.44.0, September 1 | Adds Wood River, Patoka and Cushing; updates Gulf rates and CAD abandonment surcharge |
| Express local | CER 204 and 205 | Keeps the current local spot schedule; July term rate is USD 7.9457/m3 |
| Express / Platte | CER 207 / FERC 167.33.1, July 1 | Replaces misassigned 2025 contract rows; omits cancelled 5–9 year table |
| Trans Mountain | Interim 123, May 1 | Corrects variable-component column labels, including consultation, GHG, revenue sharing and true-up |
| Puget Sound | FERC 4.16.0, July 1 | Transportation rate becomes USD 0.5729/bbl; demurrage remains conditional |

Examples independently checked against source tables:

- Keystone Hardisty–Cushing heavy: USD 6.750/bbl plus CAD 0.042/bbl abandonment.
  The two currencies are not arithmetically combined without FX.
- Mainline Edmonton–Superior heavy: CAD 11.2418/m3 plus USD 10.5945/m3.
- Express 2025 open-season 2-year Hardisty–Wood River: USD 45.8715/m3,
  plus USD 0.05/m3 abandonment. The previous 2025 rows had values from unrelated
  older term tables.
- Spearhead Edmonton heavy 2-year committed: USD 7.4820/bbl including the
  published adders, instead of showing its USD 7.4000 base as an all-in rate.
- Trans Mountain Kamloops consultation is CAD 0.6181/m3, GHG CAD 0.0375/m3,
  and revenue sharing CAD -0.6590/m3. The old labels were shifted by a column.

Published totals are retained where independent four-decimal components differ
by 0.0001 due to rounding. Conditional tankage, marine charges, open-season
eligibility, and loss allowances remain identified separately. No contract price
is offered as a rate available to every shipper.

Enbridge has already published October 1 replacements (CER 10, 11 and 12).
They are not substituted for rates effective during this audit. Metadata exposes
`last_verified`, `next_known_change`, and a freshness note. A later local rebuild
does not advance the verification date.

Primary tariff indexes: [Enbridge Mainline](https://www.enbridge.com/Projects-and-Infrastructure/For-Shippers/Tariffs/Enbridge-Mainline-GP-Inc-Enbridge-Canadian-Mainline-LP-Canadian-Mainline-Tariffs),
[Express Canada](https://www.enbridge.com/Projects-and-Infrastructure/For-Shippers/Tariffs/Express-Pipeline-Ltd-Express-Canada-Tariffs),
[South Bow Keystone](https://www.southbow.com/keystone-pipeline-system/),
[Trans Mountain](https://www.transmountain.com/tolls-tariffs).
Every output row links to the supporting PDF and its physical PDF page (including
Keystone's cover-letter offset); document URLs and hashes are in the snapshot.

## Rail and terminals

Offline QA of the existing layer passed: 110,109 valid rail segments grouped into
1,261 render features, and 1,645 terminal points including 75 curated Canadian
facilities. The live BTS count endpoint returns 110,111 rows in the same
Canada/U.S. NET=M/I scope; source rows and geometry-valid segments are different
measures. The full geometry refresh uses stable source IDs in 500-feature batches
because the prior 2,000-feature spatial GeoJSON query failed with a live ArcGIS
400 error. **The live full refresh did not complete:** the upstream service also
rejected the full spatial ID-selection request and an equivalent-count batch
retry. A non-spatial ID request did return 110,111 IDs. The existing valid rail layer
was preserved, and the difference of two source rows remains unreconciled.
Small geometry probes and count/metadata endpoints succeeded. The new batch
validation is covered offline; it is not represented as a completed live rebuild.
Failed or incomplete refreshes preserve the previous output.

The EIA crude terminal service has 99 rows, of which 94 existing points have
geometry; five null geometries are not invented. Its last edit is April 2026.
The product-terminal service has 1,476 rows and still reports a June 2020 edit.
It must not be interpreted as current terminal ownership, status, or universal
rail access. Canadian terminals remain a curated inventory, not a complete
national register. Rail coordinates are rounded to 0.001 degree for display;
the app does not provide engineering alignment precision or every yard/spur.

Primary services: [BTS/FRA rail network](https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0),
[EIA crude-by-rail terminals](https://services.arcgis.com/8df8p0NlLFEShl0r/ArcGIS/rest/services/CrudeOil_RailTerminals_US_EIA_3340393128070186484/FeatureServer/0),
[EIA product terminals](https://services2.arcgis.com/wx8u046p68e0iGuj/arcgis/rest/services/PetroleumProduct_Terminals_US_EIA/FeatureServer/0).

## Refineries and reproducibility

The refinery layer remains a 257-site IIR analytical extract, including 22 Canada
and 130 U.S. markers, plus other countries. Split complexes, upgraders, specialty
plants and inactive crude units mean neither marker count nor summed nameplate
capacity is a canonical EIA roster. Benicia, Phillips 66 Los Angeles and
LyondellBasell Houston were already absent; they were not falsely marked closed
under unrelated plants with similar city names. Source-backed Canadian capacity
and ownership corrections are maintained in the separate refinery review, with
original IIR values retained. Model changes exclude unavailable/inactive crude
capacity rather than inventing charge from coker or VDU capacity.

[EIA's 2026 refinery report](https://www.eia.gov/petroleum/refinerycapacity/)
is an annual January 1 snapshot. Its Benicia capacity predates the subsequent
closure, as explained in [EIA's June 2026 analysis](https://www.eia.gov/todayinenergy/detail.php?id=67807).
A full per-complex EIA/IIR crosswalk and survey-quality facility boundary review
remain unresolved; marker counts are not used as proof of completeness.

Validation commands (no network or PDF dependency):

```text
python scripts/build_market_access_tariffs.py
python scripts/test_infrastructure_audit.py
python scripts/validate_infrastructure_layers.py
```

The regression suite checks mixed currencies, independent current rates,
cancelled-table exclusion, component labels, no double-counted surcharges,
pagination without a transfer flag, error responses, and preservation of the
published network after a failed refresh.
