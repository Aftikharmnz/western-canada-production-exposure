# Terminal and storage inventory audit — October 2026

The layer now contains **1,790 terminal/storage source observations**: 1,702 U.S. observations, including Puerto Rico, and 88 Canadian observations. This is **145 more observations** than the previous layer: 128 Buckeye map points, three Colonial sites, 13 Canadian facilities, and one Cushing storage complex. These are not a count of unique physical sites or a complete national storage registry.

The review date is **2026-10-10 in Edmonton**. Public GIS snapshots were retrieved at **2026-10-11 05:11:32 UTC**; the Census address responses were retrieved at **05:24:18 UTC**. An observation/review date does not refresh the underlying inventory, establish that a facility is operating, or establish survey accuracy.

## Datasets and dates

| Dataset / committed snapshot | Source date or limitation | Raw observations | Retained observations |
| --- | --- | ---: | ---: |
| [Buckeye public terminal layer 1](https://gis.buckeye.com/hosting/rest/services/Hosted/PublicWebsiteData_PublicView/FeatureServer/1), `data/terminal_sources/buckeye_terminals.json` | Operator GIS last edited 2023-03-06; not a 2026 facility-status inventory | 128 | 126 |
| [Buckeye propane terminal layer 4](https://gis.buckeye.com/hosting/rest/services/Hosted/PublicWebsiteData_PublicView/FeatureServer/4), `buckeye_propane_terminals.json` | Operator GIS last edited 2023-03-06 | 2 | 2 |
| [ECCC NPRI facility layer](https://maps-cartes.ec.gc.ca/arcgis/rest/services/STB_DGST/NPRI/MapServer/0), `npri_2024.json` | Report year 2024; published facility coordinate columns, not surveyed tank/cavern boundaries | 41 selected records | 36 reviewed records, replacing 23 legacy points and adding 13 |
| [EIA-attributed product terminal copy](https://services2.arcgis.com/wx8u046p68e0iGuj/arcgis/rest/services/PetroleumProduct_Terminals_US_EIA/FeatureServer/0), `eia_products_archive.json` | Copy item description explicitly says EIA-815, **as of January 2020**; copy edited June 2020 | 1,476 | 1,476 |
| [EIA-attributed crude rail copy](https://services.arcgis.com/8df8p0NlLFEShl0r/ArcGIS/rest/services/CrudeOil_RailTerminals_US_EIA_3340393128070186484/FeatureServer/0), `eia_crude_rail_archive.json` | Underlying inventory date unavailable; a copy's 2026 edits do not establish current facilities | 99 | 94 valid points |
| [Census public address geocoder](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html), `colonial_census.json` | Public_AR_Current benchmark queried on the review date; underlying address-range vintage not independently established | 3 exact full-address matches | 3 street interpolations |
| [Oklahoma DEQ Grandstaff memorandum](https://applications.deq.ok.gov/permitspublic/storedpermits/8122.pdf), page 1 | **Draft**, dated 2022-11-02; explicitly gives office-location coordinates and FAC ID 1105 | 1 manually reviewed record | 1 office point |

The operator-hosted Buckeye layers are linked by the [current Buckeye asset-map page](https://www.buckeye.com/what-we-do/asset-map), through its public embedded web map. They provide facility names, street addresses, products and coordinates. The Bahamas BBH point (`state=GB`) and Saint Lucia point (no U.S. state) are excluded. The Yabucoa, Puerto Rico point remains U.S. with published `state=PR`; its territory is not concealed.

### Canonical EIA origin versus publicly accessible copies

The canonical ArcGIS organization `FGr1D95XCGALKXqM` identifies itself as the U.S. Energy Information Administration. Its [product terminal layer](https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/PetroleumProduct_Terminals_US_EIA/FeatureServer/36) and [crude rail service](https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/CrudeOil_RailTerminals_US_EIA/FeatureServer) returned **499 Token Required** to unauthenticated metadata requests during this review.

The public product copy is hosted in the UC Merced organization `wx8u046p68e0iGuj`, with item owner `remysfranklin`, item ID `0d931960e2aa4247b45f2346fdfb2851`. The crude rail copy is hosted in the University of Minnesota organization `8df8p0NlLFEShl0r`, with observed item owner `priho011_UMN`, item ID `6dc1c02ed2e44d72805848a2faef9493`. The downloaded files retain item metadata. **Neither public copy is described as a current authoritative EIA service.** A row-for-row comparison against the protected canonical services was not possible.

Historical EIA `Site`, `Company`, and `FID` values are preserved. They do not become current facility names, current owners, or current operating-status assertions. Crude rail records without operator information remain unknown rather than acquiring an operator from a nearby pipeline.

## Reviewed additions and corrections

The 13 Canadian additions include nine storage facilities: Keyera Fort Saskatchewan, Edmonton NGL and Josephburg; Pembina Redwater, Corunna, Prince Rupert, Edmonton North and North 40; and Base Line. Four additional Enbridge terminal records are Athabasca, Cheecham, Kirby Lake and Gretna. The Enbridge additions remain inventory observations from NPRI rather than a claim of a separately verified current operator.

Identity and storage descriptions use the [2025 Pembina AIF](https://www.pembina.com/getattachment/c2ad1c87-26a9-49a3-88e9-4fd066351a86/aif-ppc-q4-2025-sedar-filing-version-.pdf), [2025 Keyera AIF](https://www.keyera.com/assets/Attachments/KEY-2025-Annual-Information-Form.pdf), and the individual [Keyera Edmonton](https://www.keyera.com/what-we-do/featured-assets/edmonton-terminal/) and [Josephburg](https://www.keyera.com/what-we-do/featured-assets/josephburg-terminal/) pages. Facility coordinates come separately from NPRI. One facility point represents each complex; individual underground caverns are not positioned or counted as separate assets.

Twenty-three explicit legacy identity replacements correct or corroborate NPRI points. These include the [Suncor terminal network](https://www.suncor.com/en-ca/what-we-do/refining/terminals), Gibson storage sites, the [Hardisty DRU](https://www.gibsonenergy.com/operations/dru-at-hardisty/), six Enbridge terminals, and Keyera ADT. Burrard's previous approximate point and the previous Hardisty DRU point were materially displaced from the reported facility points. The historical combined ADT/ACT reported name remains separate from current ADT identity. The genuine Keyera Edmonton NGL terminal is a different reported facility and is now represented separately.

The [Colonial own-terminal page](https://www.colpipe.com/our-operations/terminals/) supports Austell, Charlotte and Chattanooga identities, products and explicit site storage capacities. Their points use government **street-address interpolation**, labeled low confidence. They are not operator-published tank centroids or surveyed boundaries. Colonial's connected third-party terminals are not presumed Colonial-owned. “Colonial Terminals Inc.” in the old Savannah EIA inventory is not silently renamed Colonial Pipeline.

The existing Buckeye map point at 7002 Marvin L. Berry Road is classified as mixed petroleum/crude storage because a [TCEQ technical review](https://records.tceq.texas.gov/cs/idcplg?IdcService=TCEQ_EXTERNAL_SEARCH_GET_FILE&Rendition=Web&dID=8196830) explicitly identifies the Buckeye Texas Hub storage/marine facility at the exact address. Its coordinates remain the operator-map point; the regulatory description and coordinate source are distinct.

The Cushing addition is Grandstaff Terminal, Enbridge Storage Cushing LLC as reported by the dated DEQ draft. The [current TransMontaigne listing](https://www.transmontaignepartners.com/operations/) and [fact sheet hosted in 2024](https://www.transmontaignepartners.com/wp-content/uploads/2024/01/Cushing-.pdf) corroborate the exact street address and crude storage service. The regulator's point is explicitly an **office location**, and current operator and permit status remain unverified. TransMontaigne is not assumed to own or operate the entire Grandstaff complex. Its commercial 1,005,056-barrel figure is deliberately not applied to the larger complex.

The final storage categories contain seven crude storage points, seven NGL/LPG storage points, and sixteen refined-product storage points. Category assignment does not imply rail access, network connectivity, exclusive commodity handling, operating status, or available capacity.

## Evidence states and capacity

`operator_verified` means reviewed identity evidence from an operator source, not a surveyed location or a certification that the facility is currently operating. `inventory_only` and `historical_unverified` keep older observations visibly distinguishable. Final counts are 157 operator-reviewed observations, 1,487 inventory observations, and 146 historical/unverified observations. Fifty-two Canadian legacy points were not newly verified; their approximate/unknown coordinate basis and unknown current status are retained. The documented Edmonton Rail Terminal decommissioning is preserved.

`source_as_of`, `coordinate_as_of`, and `reviewed_at` have separate meanings. Undated operator pages have no fabricated publication date. Legacy “last verified” labels do not become new survey dates. Facility points retain five decimal places for display; this numerical precision is not an accuracy claim.

Only three Colonial site capacities and the explicitly stated Keyera Edmonton storage capacity are supplied in barrels, with basis notes. Buckeye's numeric GIS `capacity` field lacks a declared unit in the layer metadata, so it is **not** relabeled barrels. No complex capacity is summed from individual tanks, applied across ownership shares, inferred from throughput, or described as currently available storage.

## Holdouts and deduplication

- Colonial Fredericksburg is withheld: the operator page uses postal code 22401, while the Census match returned 22408. Its street location needs independent corroboration.
- NPRI 6907, “Enbridge Edmonton Terminal,” is withheld: its published longitude `-117.7979` conflicts with the Edmonton location by about 300 km. Official provenance alone does not make an anomalous coordinate reliable.
- The co-located Gibson Hardisty West record is not added as another whole terminal without evidence that it represents a distinct facility scope.
- Natural-gas storage and waste-disposal caverns are excluded from the liquid-petroleum storage categories.
- The DOE's [four Strategic Petroleum Reserve sites](https://www.energy.gov/hgeo/opr/spr-storage-sites) are confirmed identities but no point is added without verified facility-location evidence. EPA outfalls, NOAA water-monitoring stations and oil-field place names are not substituted for storage-facility coordinates. Strategic reserve sites would also need a distinct strategic-reserve scope.
- This expansion does not claim comprehensive Cushing, Gulf Coast, Canadian cavern, third-party Colonial-connected, or U.S. crude-storage coverage.

An old point is replaced only through an explicit reviewed facility-identity mapping. **A shared city, operator, nearby coordinate, pipeline name or product is insufficient to merge records.** EIA and operator-map observations retain separate stable source identifiers unless exact facility identity and location evidence establish equivalence. Consequently overlapping observations can remain visible, and the layer does not publish unique-site totals or aggregate storage capacity.

## Reproduction and checks

`scripts/terminal_inventory.py` uses committed source snapshots and `data/terminal_facility_reviews.json`. Source identifiers and expected snapshot counts are checked; truncated inventories, duplicate identifiers, changed Colonial coordinate evidence and the Edmonton anomaly fail rather than producing an apparently successful partial inventory. A source refresh requires an explicit review of source dates, identities, scope and expected counts before updating these files. Scheduled railway rebuilds do not silently replace the historical terminal inventory with mutable university copies.

Run `python scripts/build_railway_layer.py --terminals-only` to rebuild the point inventory while retaining existing matching rail geometry. Run without that flag to refresh BTS/FRA rail geometry as well. Terminal SQL filters are rejected for the reviewed static inventory rather than applying unchecked live-copy observations. The point-only rebuild preserves all 1,264 railway geometries and their 2026-10-04 source-generation date.

Validation includes `scripts/test_terminal_inventory.py`, `scripts/test_railway_layer.py`, the infrastructure audit tests and `scripts/validate_infrastructure_layers.py`. Checks cover source completeness, country scope, exact point corrections, genuine historical identity retention, explicit geocoder uncertainty, unsupplied capacity units, and preservation of distinct inventory observations.
