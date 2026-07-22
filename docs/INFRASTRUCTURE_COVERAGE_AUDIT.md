# Infrastructure Coverage Audit

Audit date: 2026-07-22

This note records what “complete” means for each map layer, what was verified,
and what remains outside the public datasets. It is deliberately conservative:
an operator-published or government-service inventory is not described as “all”
when the source itself is partial, old, or differently scoped.

## Canada

### Refineries and refined-products plants

The map contains all 16 conventional Canadian crude refineries in the current
Canada Energy Regulator provincial count (2 BC, 5 Alberta, 2 Saskatchewan,
4 Ontario, 2 Quebec, and 1 New Brunswick). The richer plant layer also includes
oil-sands upgraders and specialty-processing sites, so its Canadian marker total
is intentionally larger than 16.

The HF Sinclair / Petro-Canada Lubricants Mississauga Centre was missing from
the logistics context. It is now included as a specialty-lubricants refinery and
marine product terminal, where it will not be mistaken for a conventional crude
refinery in the refinery-yield model.

Primary reference:
[CER Canadian refinery snapshot](https://www.cer-rec.gc.ca/en/data-analysis/energy-markets/market-snapshots/2026/market-snapshot-canadian-crude-refinery-runs-held-steady-in-2025.html?=undefined&wbdisable=true).

### Canadian terminals

The previous layer had 21 manually maintained Canadian points: 14 crude/rail and
only 7 product facilities. The rebuilt source contains 75 reviewed facilities:

- 49 refined-product/specialty terminals;
- 14 crude pipeline, storage, or marine terminals;
- 11 crude or multi-product rail/transload terminals; and
- 1 inactive terminal retained for historical context.

The added tranche includes the complete 14-location Suncor network, reviewed
Imperial and Shell facilities with NPRI coordinates, all five current Trans
Mountain terminal locations, six material Enbridge terminal hubs, Irving's main
Canadian marine terminals, Valero Quebec facilities, Gibson storage terminals,
and HF Sinclair Mississauga. Each Canadian record now carries country, status,
last-verified date, modes, scope, source, and coordinate-confidence fields.

The Edmonton Rail Terminal is no longer shown as active. Pembina reports that it
was decommissioned in Q2 2024, so it is retained only in the off-by-default
inactive category. The two confusing Keyera ADT/KACT markers were consolidated
into one Edmonton complex pending a newer operator-level facility breakdown.

This is still not an exhaustive current national registry. The Canadian Fuels
Association's 2016 baseline counted 85 *primary* terminals, but that listing is
too old to ingest uncritically. Canada does not publish a current open national
point registry equivalent to EIA's U.S. service. Highest-priority next work is:

1. reconcile the remaining Imperial locations (Imperial says “more than 20”;
   15 high-confidence sites are currently included);
2. verify the three Shell locations not present in the NPRI-confirmed 12-point
   tranche (Shell says it owns 15 distribution terminals);
3. review current Parkland/Sunoco, Norcan/IMTT, Vopak, FCL/Co-op, Irving bulk,
   northern, aviation-fuel, and independent marine terminals; and
4. assign shared site IDs where a refinery and terminal occupy one complex.

Primary references:
[Suncor terminals](https://www.suncor.com/en-ca/what-we-do/refining/terminals),
[Imperial distribution](https://www.imperialoil.ca/en-ca/company/operations/pipelines-and-distribution),
[Shell Canada operations](https://www.shell.ca/en_ca/about-us/what-we-do.html),
[Trans Mountain terminals](https://www.transmountain.com/terminals),
[Irving facilities](https://www.irvingoil.com/en-CA/discover-irving/irving-oil-facilities),
[HF Sinclair Mississauga](https://www.hfsinclair.com/operations/facilities/canada/mississauga-on/default.aspx), and
[Environment Canada NPRI GIS](https://maps-cartes.ec.gc.ca/arcgis/rest/services/STB_DGST/NPRI/MapServer/0).

## United States

### Refineries

All five U.S. PADD groups are now selected by default. That makes every U.S.
record in the local refinery extract visible without requiring the user to know
that PADD I, III, and IV were previously hidden.

The local layer has 130 U.S. markers, but that does **not** make it identical to
EIA's 130-facility 2026 roster. The IIR extract splits several EIA complexes
(for example Catlettsburg, El Paso, Los Angeles, Galveston Bay/Texas City, and
Corpus Christi), includes specialty/component-processing assets, omits several
EIA non-CDU reporters, and labels every point operational. EIA reports 128
operating and 2 idle facilities as of 2026-01-01; the Benicia refinery then
ceased operations in 2026. The map now states this limitation instead of making
a count-based completeness claim.

A safe future reconciliation must use the EIA-820 workbook as the canonical
facility roster and preserve IIR unit detail under one or more `plant_parts` for
each EIA facility. Merely adding missing points would worsen double-counting.

Primary references:
[EIA 2026 Refinery Capacity Report](https://www.eia.gov/petroleum/refinerycapacity/),
[EIA refcap26 workbook](https://www.eia.gov/petroleum/refinerycapacity/refcap26.xlsx), and
[EIA 2026 closure discussion](https://www.eia.gov/todayinenergy/detail.php?id=67807).

### U.S. terminals

Every valid-geometry point returned by the EIA crude-by-rail service is included
(94 points; five source rows have no geometry). Product-terminal queries no
longer use the Canada/continental-U.S. bounding box, so Alaska, Hawaii, Puerto
Rico, the U.S. Virgin Islands, and Guam service points are not silently omitted.

The EIA petroleum-product terminal GIS service is an older snapshot whose data
edit is 2020. The app includes the full public service snapshot, but it must not
be described as a current all-U.S. ownership/capacity inventory. The service
also identifies bulk terminals generally; it does not prove that every point is
rail-served.

Primary services:
[EIA crude-by-rail terminals](https://services.arcgis.com/8df8p0NlLFEShl0r/ArcGIS/rest/services/CrudeOil_RailTerminals_US_EIA_3340393128070186484/FeatureServer/0) and
[EIA petroleum-product terminals](https://services2.arcgis.com/wx8u046p68e0iGuj/arcgis/rest/services/PetroleumProduct_Terminals_US_EIA/FeatureServer/0).

## Pipelines

The previous market layer contained 16 named routes and only a small fraction of
U.S. EIA pipeline systems. The rebuilt layer has 22 route features, including:

- all previously named Canadian market-access routes;
- Imperial Sarnia Products Pipeline, Sun-Canadian Pipe Line, and Valero Pipeline
  Saint-Laurent as off-by-default, clearly labelled approximate corridors; and
- off-by-default aggregate reference features containing all linework returned
  by EIA's crude-trunk (236 source features), petroleum-products (329), and HGL
  (133) services.

EIA's layers are major/trunk and selected intrastate context, not every gathering,
connector, private plant, or regulated hazardous-liquid pipe. The AER layer
separately provides detailed Alberta feeder context. Important non-pipeline
refined-product context still worth adding is marine import/export terminals and
petroleum waterways. The 2026 Western Gateway product-pipeline proposal was not
added because it is planned, not operating; if future projects are mapped, they
need a distinct planned/dashed status.

Primary services:
[EIA crude pipelines](https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Crude_Oil_Trunk_Pipelines_1/FeatureServer/0),
[EIA product pipelines](https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Petroleum_Products_Pipelines_1/FeatureServer/0), and
[EIA HGL pipelines](https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Hydrocarbon_Gas_Liquids_Pipelines_1/FeatureServer/0).

## Rail

The BTS/FRA NARN audit exactly matched the intended filter: main (`NET=M`) and
major-industrial (`NET=I`) segments across Canada and the U.S. That is complete
for this defined scope, not for every active rail track. Minor industrial leads,
long sidings, yards, inactive track, and private last-mile spurs are omitted.

The source 110,109 segments are grouped by category, country, and owner into
about 1,261 rendered features. This retains the source geometry/cardinality while
avoiding the previous freeze/OOM risk from constructing roughly 100,000 Leaflet
paths at once. If last-mile detail is needed later, minor/yard tracks should be
queried only near terminals and rendered at high zoom rather than added nationally.

Primary reference:
[BTS/FRA North American Rail Network](https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0).

## QA changes

The app now has a global HTML `[hidden]` rule, consistent legend-filtered totals,
non-fatal optional overlay loading, independent market-hub visibility, safe
URL/color handling, escaped distance labels, all-PADD refinery defaults, and an
explicit oil-sands/upgrader classifier that no longer treats every Alberta or
Saskatchewan refinery as an upgrader. The scheme builder drops invalid polygon
rings that collapse below four positions after simplification. Run
`python scripts/validate_infrastructure_layers.py` after rebuilds to catch
geometry, provenance, route-ID, terminal-country, and performance regressions.
