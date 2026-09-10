# Production data audit — 10 September 2026 UTC

The audit refreshes published regulator observations. Reporting periods differ by source; a recent refresh timestamp does not mean every jurisdiction has reported the latest calendar month.

## Corrections

- **Removed bitumen from the Alberta conventional crude series.** Battery subtype alone was insufficient: primary/EOR bitumen wells can report through ordinary crude batteries. The ETL now also excludes wells explicitly classified `CR-BIT` in Petrinex's well reference. December 2024 previously included 236.212 kbbl/d from these bitumen wells in its conventional category. This is material overlap with ST53, not an increase in conventional crude production. The reference is current infrastructure, so historical reclassifications cannot be reconstructed from this snapshot.
- Alberta downloads now advance independently of the analyst workbook. Previously, the refresh stopped at the workbook's January 2026 date even while Saskatchewan and North Dakota advanced.
- `--download` refreshes mutable current files and recent monthly revisions. Downloads validate file signatures before atomically replacing a good cache; failed downloads retain the prior cache and record the failure.
- AER ST53 current data now enters the production store directly from its `BITUMEN` worksheet. Its values are **m³ per calendar day**, so only the 6.28981077 bbl/m³ conversion applies.
- AER ST39 current data now replaces both mined bitumen and synthetic crude observations, including reported zero production, for all published months in the current issue. Its values are **m³ per month**, so the conversion also divides by calendar days. Future zero-filled columns are excluded using the issue date. Saskatchewan upgrader observations are preserved because ST39 covers Alberta.
- Official current observations replace overlapping workbook forecasts. The workbook actual cutoff remains January 2026. Its dashboard date cell is blank, so `data/workbook_provenance.json` pins the reviewed cutoff to the workbook SHA-256. A changed workbook with no usable cutoff fails rather than having its forecasts relabelled as actuals.
- Repeated workbook contributions with the same asset/month/stream/scenario are aggregated once, with their source column references retained. This preserves volume while removing duplicate exported records.
- Current ST53 approvals resolve against refreshed AER scheme footprints and ST44 2026 Q2 locations. Multiple approvals for one project retain their combined footprint. Coordinates represent scheme or township centroids where stated, rather than surveyed plant coordinates.
- The opening month requires all regularly reported crude source/stream series to reach that month. One jurisdiction's conventional crude can no longer conceal another jurisdiction's missing data.
- Seasonality uses actual observations only, excludes rollups and aggregate markers, and preserves reported zeros. It sums the available streams for each selected asset; it is not a net crude supply model.
- Public manifest metadata contains the workbook filename, not its private workstation path. Derived Petrinex sources have readable names.
- Date parsing accepts complete ISO date strings; nonfinite numeric values are rejected.
- Manitoba's refreshed workbook changed `WELL_NAME` and `FLUID_TYPE` to `WELL NAME` and `FLUID TYPE`. Header normalization now accepts both formats; the current archive contributes 119,601 observations across 4,623 wells. A regression fixture protects against silently losing the province again.

## Source definitions and availability

| Source | Official definition / endpoint | Coverage and interpretation |
| --- | --- | --- |
| AER ST53 | [Current XLS](https://www.aer.ca/documents/sts/ST53/ST53_Current.xls) | July 2026 issue, January–July observations; bitumen m³/day, including commercial, enhanced and primary schemes. |
| AER ST39 | [Current XLS](https://www.aer.ca/documents/sts/ST39.xls) | May 2026 issue, January–May observations; mined bitumen and synthetic crude m³/month. AER lists this report [three months in arrears](https://www.aer.ca/whats-new). |
| AER ST44 | [2026 Q2 XLSX](https://static.aer.ca/prd/documents/sts/ST44_2026-Q2.xlsx) | Active approval/operator/location bridge, replacing 2025 Q4. |
| Petrinex AB / SK | [Public data](https://www.petrinex.gov.ab.ca/publicdata/) | OIL/PROD monthly m³. AB excludes identified oil-sands reporting subtypes and known CR-BIT wells to reduce overlap with AER oil sands. July 2026 files downloaded successfully. August AB returned HTTP 500; August SK returned HTTP 404. |
| BCER | [Production downloads](https://www.bc-er.ca/data-reports/data-centre/?category=2769) | Oil and condensate monthly m³ at well/completion/zone, aggregated to well authority, through July 2026. Refreshed production, well index and 34,400 surface location features. |
| NDIC | [Monthly report index](https://www.dmr.nd.gov/oilgas/mprindex.asp) | Oil worksheet monthly barrels divided by calendar days, through June 2026. The official index explains that amended Excel files can differ from the released PDFs. [July figures are scheduled for September 21](https://www.dmr.nd.gov/dmr/oilgas/directorscut). |
| Manitoba | [Monthly well production archive](https://www.gov.mb.ca/iem/petroleum/reports/wmp_2023_2026_excel.zip) | OIL monthly m³ divided by calendar days; refreshed archive reports through May 2026. |
| Montana BOGC | [Historical production archive](https://bogfiles.dnrc.mt.gov/Reporting/Production/Historical/MT_Historical_Production.zip) | `BBLS_OIL_COND` monthly barrels; Bakken and Three Forks only, through June 2026. Current production and complete well reference archives refreshed. Trailing months can have very sparse submissions. |

The January 2026 Alberta Petrinex revision endpoint returned HTTP 500 on two attempts. Its previously downloaded January cache is retained. Earlier monthly caches are retained as historical snapshots; this audit does not claim to re-download every historical revision.

The conventional classification check was prompted by AER's [reported 2024 crude oil average of 530 kbbl/d](https://www.aer.ca/data-and-performance-reports/statistical-reports/alberta-energy-outlook-st98/crude-oil/crude-oil-production), versus the former app series averaging roughly 760 kbbl/d. Exact regulator totals and this location layer can still differ because the layer requires usable locations and relies on current well classifications; it is not adjusted or scaled to match a target total.

After excluding known CR-BIT wells, the location layer's calendar-day-weighted 2024 average is 539.224 kbbl/d. The remaining difference from the published provincial figure is retained transparently rather than removed through arbitrary scaling.

Gross mined bitumen and synthetic crude are different stages of some of the same barrels. Adding these streams together measures selected production activity, not net marketable crude supply. Condensate, pentanes plus, propane and butane are separate product categories. The map and source filters should retain those distinctions.

Historical ST53/ST39 observations before the current issues remain analyst workbook data. Approval splits, acquisitions, renamed projects and generic historical buckets can interrupt individual asset histories. New current approvals are preserved rather than inventing a historical project-level allocation. DLS approximations remain labelled as lower confidence; neither this map nor public regulator GIS is a survey of every well and facility.

An independent review of the July ST53 locations found 217 approval-centroid rows, 30 ST44 fallback rows and one unmapped positive approval: Baytex 12640, 11.05 m³/day (about 69.5 bbl/day). Its volume remains in the data without an invented point. Every resolved current ST53 coordinate falls within Alberta.

## Rebuild and validation

Use Python with `openpyxl`, and R with `readxl` for AER XLS extraction. `Rscript` is resolved from the installed workstation path or `PATH`.

```powershell
python scripts/run_etl.py --download
python scripts/test_production_etl.py
```

`--offline` rebuilds from the raw cache without HTTP requests and retains the saved refresh audit. `scripts/build_seasonality_index.py` and `scripts/validate_production_data.py` can also be run separately for existing browser exports. Raw downloads, source workbooks, SQLite, and intermediate extraction/validation files stay outside Git. The browser assets, date shards, seasonality, geometry, source registry and manifest are committed together because compact monthly asset references depend on the matching asset table.

Validation checks every compact asset reference, coordinate pair, numerical value, unit conversion, record count, source coverage boundary, monthly total, and duplicate/forecast overlap. Current AER source totals are reconciled independently to the extracted source worksheet values. Source lag and incomplete submissions remain visible instead of being filled by extrapolation.

The ETL also refuses to publish an unrecognized ST39 facility with positive production until its approval mapping is reviewed, and automatically rebuilds seasonality and runs the export validator after a successful refresh.

## Verified output

The September 10 rebuild contains **3,703,496 records**, **122,420 assets** (122,408 with coordinates), **139 monthly shards** and **315 production footprints**. The opening month is **May 2026**, the latest month with broad actual-source coverage; the newest actual observations are **July 2026**. May is a mixed month: the Saskatchewan Lloydminster Upgrader retains a separately labelled **17.0000 kbbl/d workbook forecast**, because Alberta ST39 does not cover that asset. All ten production regression tests pass. The export validator passes every shard and independently reconciles all 17 current AER series/month combinations. There are zero duplicate asset/date/source/stream groups and no overlapping actual/forecast records.

| Selected series | Latest reported month | Published layer, kbbl/d |
| --- | --- | ---: |
| Alberta in-situ bitumen (ST53) | July 2026 | 2,056.2721 |
| Alberta mined bitumen (ST39) | May 2026 | 1,673.5483 |
| Alberta synthetic crude (ST39) | May 2026 | 1,251.0611 |
| Alberta conventional crude | July 2026 | 591.3580 |
| Saskatchewan conventional crude | July 2026 | 423.9039 |
| BC crude | July 2026 | 11.0199 |
| BC condensate | July 2026 | 37.2723 |
| North Dakota crude | June 2026 | 1,012.6661 |
| Manitoba crude | May 2026 | 35.1240 |
| Montana Bakken / Three Forks | June 2026 | 50.7472 |

These observations have different reporting periods and include successive processing stages. They must not be summed as a synchronized net supply figure. Seasonality now contains 3,686,511 actual asset/month entries across 122,381 eligible mapped assets. All producing BC, North Dakota and Montana records match their respective regulator coordinate references; Alberta and Manitoba DLS locations retain their stated approximation confidence. The final manifest and source registry contain no private workstation paths.
