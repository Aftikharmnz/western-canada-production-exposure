# Refined-Products Yield Model

This document describes the model behind the **Select → Refineries** mode, which
estimates how much refined product a box-selected region would produce.

## What it does

After drawing a selection box over **visible** (filtered) refineries, the app:

1. Reads each plant's crude (CDU) capacity and its installed process units.
2. Classifies each plant's configuration from those units.
3. Applies a published yield slate to the plant's crude charge.
4. Aggregates the region: finished products, process-unit capacity, owner
   breakdown (refinery basis and owner basis), and trader metrics.

Volumes can be shown in **bbl/d, gal/d, or L/d** (42 US gal/bbl; 158.987 L/bbl).

## Configuration classifier

For each refinery, capacity (BBL/d) is summed by unit type and compared to crude
charge:

- **Deep conversion (Coking)** — coking (or visbreaking) capacity ≥ 5% of crude.
- **Cracking** — FCC or hydrocracker capacity ≥ 5% of crude.
- **Hydroskimming / Topping** — neither (crude distillation, reforming,
  hydrotreating only).

## Yield slates (% of crude charge)

From **Leffler, _Petroleum Refining in Nontechnical Language_ (2020), Table 20-1**
("Refinery Yields", medium sour crude such as West Texas Sour / Arab Light):

| Product            | Hydroskimming | Cracking | Deep conversion |
|--------------------|:-------------:|:--------:|:---------------:|
| Motor gasoline     | 30            | 50       | 60              |
| Jet / kerosene     | 10            | 10       | 10              |
| Diesel / distillate| 20            | 25       | 25              |
| Residual fuel oil  | 35            | 10       | 0               |
| LPG                | 0             | 3        | 4               |
| Petroleum coke     | 0             | 0        | 3               |
| Refinery fuel & loss (memo) | 8    | 12       | 13              |
| Processing gain (memo) | (3)       | (10)     | (15)            |

Output volume for a plant = crude charge × yield% / 100, summed across the region.
"Processing gain" is volumetric expansion from cracking/hydrogen addition;
"refinery fuel & loss" is internal consumption — both shown as memo items, not
salable product.

## Grounding & benchmarks

- **Leffler (2020), Table 20-1** — configuration slates (primary source).
- **Maples, _Petroleum Refinery Process Economics_ (2000), Table 4-2** — U.S.
  refinery product slate as % of crude charge (gasoline ≈ 55–57%, jet ≈ 11%,
  distillate ≈ 23–24%, resid ≈ 6%) used as a sanity benchmark.
- **Fahim et al., _Fundamentals of Petroleum Refining_** — per-unit yields used
  to justify the configuration split (FCC ≈ 55 vol% gasoline from gas oil;
  delayed coker ≈ 30 wt% coke; visbreaking; catalytic reforming).

**Validation:** running the model over PADD III (U.S. Gulf Coast) yields
gasoline 56.8%, distillate 24.7%, jet 10.0%, resid 3.5% of a ~9.5 MMbbl/d crude
charge — consistent with the Maples U.S. benchmark and the region's heavy
coking/deep-conversion mix.

## Nelson Complexity Index

Each refinery (and the region, owner-weighted) also carries a **Nelson Complexity
Index** — the standard measure of refinery sophistication / capital intensity:

> CI = 1 + Σ ( CF_unit × capacity_unit ÷ crude charge )

Complexity factors (CF) are the cost of each unit per barrel relative to crude
distillation, from **Kaiser, de Klerk, Gary & Handwerk, _Petroleum Refining:
Technology, Economics, and Markets_ (2019), Table 7.1** (OGJ 1998–2019 values):

| Unit | CF |
|---|--:|
| Atmospheric distillation (base) | 1 |
| Catalytic cracking (FCC) | 6 |
| Hydrocracking | 6 |
| Delayed / fluid coking | 6 |
| Catalytic reforming | 5 |
| Alkylation | 10 |
| Aromatics / petrochemical | 15 |
| Thermal cracking / visbreaking | 2.75 |
| Hydrotreating | 2 |

A crude-only plant ≈ 1; complex coking refineries publish ≈ 9–14. CI is computed
from each plant's reported units keyed on `unit_type_short` (IIR leaves the
`unit_type_group` rollup blank for vacuum distillation, isomerization, several
hydrotreaters, asphalt and lubes, so a group-based read would miss them), plus
hydrogen-plant capacity from `plant_capacities` (MMcfd treated as Mbpd-equivalent,
CF 1, per the OGJ/Nelson convention). Only utility units with no standard Nelson
factor (sulfur recovery, amine, splitters, calciners) are excluded.

This is the **standard Nelson calculation with no calibration factor** — exactly
`CI = 1 + Σ(CF × capacity ÷ crude)`. Benchmarked against 13 refineries that publicly
report Nelson CI (PBF, CVR, Delek, Marathon, Motiva, Irving, Suncor), it runs ~15–20%
below the published figures (mean absolute error ~2.2 points), because the commercial
methodology draws on fuller/proprietary per-unit coverage. Use it for ranking and
relative comparison rather than as an exact published value.

## Data handling (IIR quirks)

- **Decommissioned units are excluded.** IIR keeps Closed/Mothballed/Removed/
  Shuttered units in the unit list (~4% of listed BBL/d capacity). The model
  counts only commissioned/operational units for unit totals, configuration
  classification, and Nelson CI — otherwise a closed coker could flip a plant
  into deep conversion and inflate CI.
- **Conventional plants with no CDU rows are not upgraders.** The SCO upgrader
  slate applies only to oil-sands plants (name/sector match, or Alberta/
  Saskatchewan). A conventional refinery missing both plant-level crude capacity
  and CDU unit rows (e.g. CITGO Corpus Christi West) recovers its charge from
  coker capacity ÷ 0.30 (coking is ~30% of crude at a deep-conversion plant)
  and classifies normally, instead of silently taking an 80% SCO yield.

- **Effective crude charge.** Some plants leave the plant-level crude-capacity field
  blank even though they have crude (CDU) units (e.g. Preemraff, Wilhelmshaven,
  condensate splitters). The model recovers the charge from CDU unit capacity, then
  falls back to a bitumen-throughput proxy for upgraders.
- **Bitumen upgraders (SCO).** Oil-sands upgraders (Suncor, Syncrude/Mildred Lake,
  Horizon, Lloydminster) have no atmospheric crude unit — they convert bitumen to
  **synthetic crude (SCO)** via coking/hydroconversion. They're detected, charged
  from their vacuum/coker/diluent-recovery capacity, and given an SCO-dominant slate,
  so they show realistic SCO output instead of zero.
- **Condensate splitters** get a light slate (naphtha/distillate-heavy, ~no resid).
- **Vacuum distillation & secondary units** are present in the IIR data but carry a
  null `unit_type_group`; reads are keyed on `unit_type_short` so they're not lost
  (this drives both the unit summary and the Nelson CI).
- **Coverage.** The dataset also contains Mexican and European refineries; the
  Mexico and "European refineries" filter groups are enabled by default.

## Limitations

- **Nameplate, not actual:** assumes plants run at full crude capacity; real
  output depends on utilization, turnarounds, and economics.
- **Medium-crude slates:** the slates assume a medium sour crude. Heavier or
  lighter crude diets shift the slate (heavier → more resid/coke for a given
  configuration).
- **Coke** is reported on the table's volumetric basis; petroleum coke is
  commonly quoted in short tons, so treat it as an order-of-magnitude figure.
- Configuration thresholds (5% of crude) are a pragmatic cut, not a plant-by-plant
  engineering review.
