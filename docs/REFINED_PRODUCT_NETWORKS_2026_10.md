# Refined-product network identity review — 10 October 2026

The pipeline menu now separates the published product network identities. The
builder retains all 329 records from the public EIA-attributed copy in 118
`Opername` + `Pipename` groups. Each archived feature ID belongs to exactly one
group. Buckeye and Colonial are independent selections with different colours;
Laurel, Connecticut, Norco, Plantation, SFPP North/South and the other named
source systems are separate selections. The former nationwide products
catch-all is removed. The source does not establish a complete inventory of
every private pipeline or connector.

`source_operator_names`, `source_pipeline_names` and `source_feature_ids` retain
the original identities. Stable route IDs depend on those identities rather
than source row order, nearby terminals or inferred geography. Missing labels
remain explicitly unknown. The record groups can include branches or a source
spelling variant; they are not asserted to be separate legal owners.

## Geometry publication and date limits

The service formerly described as direct EIA is a
[public Esri-hosted EIA-attributed copy](https://www.arcgis.com/home/item.html?id=c745d9f4b81e42f3a54aee7aaa396975)
owned by `Federal_User_Community`. Its description identifies it as a cached
service periodically checked against the federal source. Its data-service edit
is **1 July 2025**, and its schema edit is **9 June 2026**. Neither date establishes
the underlying inventory or survey date.

The builder first tries the
[canonical EIA organization service](https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/PetroleumProduct_Pipelines_US_EIA/FeatureServer/0).
That service returned **499 Token Required** during this review; its original
catalog item returned **403**. When the canonical publisher is inaccessible, the
builder explicitly records the copy publisher, access limitation, source service
edits and an unavailable underlying inventory date. A successful copy download
does not establish current operation or ownership.

Buckeye's [official map](https://www.buckeye.com/map) provides direct operator
linework in its [published pipeline layer](https://gis.buckeye.com/hosting/rest/services/Hosted/PublicWebsiteData_PublicView/FeatureServer/2).
The exact reviewed name crosswalk is:

| Archived identity | Operator-published identity |
| --- | --- |
| `BUCKEYE PARTNERS` / `Buckeye` | `BUCKEYE PIPE LINE` |
| `BUCKEYE PARTNERS` / `Laurel Pipeline` | `LAUREL PIPE LINE` |
| `WEST SHORE PIPELINE CO` / `West Shore Pipeine` | `WEST SHORE PIPE LINE` |

These three selections display the operator geometry. Archived EIA IDs remain
reconciliation IDs, while `geometry_source_feature_ids` identifies the operator
geometry records. Wood River and Buckeye Texas Partners are additional distinct
operator selections because the archive does not supply a defensible exact-name
match. Buckeye Texas Partners' published crude/LPG/component service is placed
under other liquids rather than presented as gasoline/diesel-only transport.
The operator service's last edit is **6 March 2023**; its inventory/survey date is
not supplied. This is currently published operator evidence, not a 2026 survey.

BDL's separate layer publishes one natural-gas system and one unspecified
non-high-volatility liquid system. Those records are not relabelled as verified
refined-product networks or company-owned assets.

## Reviewed identity facts

The dated overrides in `data/pipeline_route_facts.json` are limited to reviewed
identities. [Buckeye's operator description](https://www.buckeye.com/what-we-do/pipelines-terminals/)
supports its network identity; its throughput and mileage are not converted into
an installed capacity. [ONEOK's completion announcement](https://ir.oneok.com/news-and-events/press-releases/2023/09-25-2023-134815200)
supports the Magellan alias while preserving the archive's `MIDSTREAM PARTNERS`
attribute. [Sunoco's completion announcement](https://www.sunocolp.com/press-release/item/sunoco-lp-completes-acquisition-of-nustar-energy-l.p.-announces-a-4-increase-in-quarterly-distribution-2024)
supports the legacy NuStar corporate identity; it does not independently verify
2026 ownership of every historical segment.

[Brookfield's Q2 2025 letter](https://bip.brookfield.com/bip/reports-filings/letters-unitholders/bip-q2-2025-letter-unitholders)
supports the Colonial acquisition and its explicitly dated 2.5 million bbl/d
system disclosure. That rating is neither present throughput nor a capacity for
each branch. Other unreviewed source groups retain unknown capacity/endpoints
and have no synthetic human review date.

The final layer contains 143 pipeline selections and 27 market-area hubs.
Regression checks cover independent identities at identical coordinates,
complete source-ID retention, missing labels, exact-name operator geometry,
canonical-source fallback, date distinctions and rejected incomplete downloads.
