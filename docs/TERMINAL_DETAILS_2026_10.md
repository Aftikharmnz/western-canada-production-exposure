# Facility roles, products and storage capacity — October 2026

This review enriches 205 existing source observations: 40 Canadian records and 165 U.S. records. It adds no points and merges no observations. The inventory retains 1,790 source records, which can overlap at one physical site. Review date is October 11, 2026 in Edmonton; publication, identity-review and coordinate dates remain separate.

## Role filters

The role facet works alongside existing commodity/infrastructure categories and independently of railroad-owner visibility. All five roles start enabled:

| Role | Meaning |
| --- | --- |
| Storage sites | Storage documented; separate terminal handling not established. |
| Terminals | Handling documented; storage not established. This does not assert that tanks are absent. |
| Storage + terminal | Storage and terminal handling documented. |
| Processing / other | Refinery, processing facility or another documented role rather than a separately identified terminal. |
| Role unverified | No independent role review, or ambiguous physical facility scope. |

Names, commodities, coordinates and inventory categories do not establish roles by themselves. The normalized records retain source evidence and role limitation notes. Unreviewed historical records remain unverified rather than becoming a current operating-facility registry.

Search matches reviewed stored/handled products and services. Results precede the role controls on small screens. Choosing a locator enables its category and role. Role changes preserve cached railroad geometry and owner choices. Core and All restore every role; Hide facilities clears only facility roles.

## Capacity evidence

There are 176 positive capacity observations, one for each of 176 reviewed source records. They are not a unique-site count and are not summed. Values retain explicitly published units, individual scope, basis and dates. An empty capacity list means unavailable, never measured zero. Throughput/loading rates are not converted into storage.

U.S. capacities comprise 126 Buckeye liquid-terminal records, three Colonial, 28 TransMontaigne, three Kinder Morgan/BOSTCO and two Vopak. Buckeye's two propane terminals and Grandstaff retain unavailable capacity.

The earlier Buckeye unit holdout is resolved by its [official web-map configuration](https://gis.buckeye.com/portal/sharing/rest/content/items/87dea43f3ff049ddae960eb116d828b7/data?f=json): the layer-1 popup and field alias explicitly say **Capacity (bbls)**. Existing object IDs, names and addresses were compared with live operator records. GIS edit date remains March 6, 2023; popup configuration date is November 13, 2023. Neither establishes the measurement date, current operation, inventory or available space. Working/shell basis is unspecified. Its generic Products field supports handling, not product-specific stored inventories or tank allocations.

The Canadian review supplies 14 site capacities: Gibson Hardisty/Edmonton, Pembina Base Line/North 40/Edmonton North/Redwater/Corunna, Keyera KFS/Edmonton/ADT and four Trans Mountain terminals. The [2025 Keyera AIF](https://www.keyera.com/wp-content/uploads/2026/03/2025-Keyera-Annual-Information-Form.pdf) gives KFS gross storage of 16.683 million barrels, approximate working capacities for Edmonton and ADT, and shell capacity for Base Line. Base Line's 4.8-million-barrel gross total is not added to the partners' 2.4-million-barrel shares. Trans Mountain capacities retain shell basis.

Published conflicts remain explicit, including older/rounded Gibson webpage values versus dated filings, BOSTCO's undated TransMontaigne total versus the dated Kinder Morgan sheet, and the older Galena Park sheet versus the edition linked from the current operator index. Every selected value has its own scope, source and note.

Canaport/East Saint John and Lévis marine/refinery combined points retain unverified roles and no capacity because broad complex figures cannot be assigned confidently to those point scopes. Grandstaff's commercial-subset figure is withheld from its regulator office-location observation. Ambiguous TransMontaigne duplicate/aggregate listings remain unassigned.

## Products, services and provenance

Stored products require explicit storage statements. Handled products are separate. Generic product lists do not establish that every product is stored, simultaneously available or allocated particular tank volumes. Normalized empty handling lists remain unavailable in the main card; retained historical commodity wording is under source details.

When supported, services include blending, loading/offloading, marine/rail handling, fractionation and tank/cavern counts. Modes and pipeline connections require explicit statements, not proximity or shared ownership. Detail reviews preserve coordinate provenance and do not certify current operation. Long tap/click cards scroll; sources and review evidence can be expanded.

## Reproduction and safeguards

Facts in `data/terminal_details_canada.json` and `data/terminal_details_us.json` join only by existing facility ID. The builder rejects unmatched/duplicate IDs, unsupported fields, invalid role/product arrays, unsafe sources, invalid dates and unsourced/nonpositive/nonfinite capacities. It performs no unit inference, conversion, scope aggregation or geometry changes.

Rebuild with `python scripts/build_railway_layer.py --terminals-only`. Original evidence remains in `data/terminal_facility_reviews.json` and committed snapshots. All 1,264 rail render features retain their geometry and geometry date. The moved Keyera AIF URL was corrected without changing the original identity-review date.

Validation covers exact source-ID joins, rail/point preservation, scope/unit guards, missing versus zero, escaped evidence, safe links, role/category combinations, cached rail context and desktop/mobile cards. HTTP(S) links reject embedded credentials.
