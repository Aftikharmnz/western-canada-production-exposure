# Refinery capacity and product scenarios

Audited September 10, 2026 against the supplied refining references and EIA definitions.

**Select > Refineries** describes installed capacity and illustrative product
scenarios. It does not measure refinery production for the selected production
month. Capacity records are a dated infrastructure snapshot.

Nine Canadian plant capacities have operator-reviewed overrides in
`data/refinery_capacity_overrides.json`, applied by
`python scripts/apply_refinery_capacity_overrides.py` and the R refinery builder.
Original IIR capacity values, unit rows and timestamps are retained. Each override
records source, observation/effective date and capacity basis; newer IIR releases
are skipped for renewed review. Jean Gaulin's differing published capacity bases
and Scotford's diluted-bitumen rating remain explicitly unresolved.

## Inputs and coverage

- Use positive, finite reported crude capacity, or active atmospheric crude-unit
  (CDU) capacity when the plant total is missing. Convert bbl/d to kbbl/d once.
- Explicitly inactive plants and units contribute no operating capacity. If all
  known CDUs are inactive, a stale positive plant crude total is not used.
- Duplicate plant IDs and duplicate unit IDs within a plant count once.
- Prefer reported unit feed capacity. Process capacities describe overlapping
  streams; their sum is not crude input or finished production.
- Never infer crude capacity from vacuum units or `coker capacity / 0.30`, or
  bitumen input from a presumed diluent fraction. Imported intermediates, recycle
  and integrated-plant boundaries are unknown.
- Missing capacity and unsupported products are unavailable, not zero output.

## Supported configurations

Leffler Chapter 20 defines a simple refinery as crude distillation, catalytic
reforming and hydrotreating; a complex refinery adds an FCC and associated
processing; a very complex refinery adds a coker. The screening rules are:

| Scenario | Rule |
|---|---|
| FCC + coking | FCC and coker capacity each at least 5% of crude capacity |
| FCC cracking | FCC at least 5%, without a qualifying coker |
| Hydroskimming | Reformer and hydrotreater, without qualifying conversion units |

The 5% threshold is an application assumption, not a published engineering
criterion. Small cokers, combined FCC/hydrocracker configurations and different
crude diets can differ materially from the textbook examples.

Visbreaking is mild thermal cracking with unconverted residue; it does not
trigger the zero-residual-fuel coking scenario (Fahim, Chapter 6).

Splitters, upgraders, hydrocracker-only plants, other conversion plants,
distillation-only/specialty facilities and missing-input plants have no product
estimate. Splitter naphtha cannot be labeled finished gasoline. No generic SCO or
bitumen yield is assumed. These plants remain in capacity/plant tables, and the
panel reports scenario coverage separately.

## Yield and utilization

Example yields are verified against **Leffler, Petroleum Refining in Nontechnical
Language (2020), Table 20-1**, printed p.192 (PDF p.199), for medium crude.

| Product / memo (%) | Hydroskimming | FCC cracking | FCC + coking |
|---|---:|---:|---:|
| Gasoline | 30 | 50 | 60 |
| Jet / kerosene | 10 | 10 | 10 |
| Distillate | 20 | 25 | 25 |
| Residual fuel | 35 | 10 | 0 |
| LPG | 0 | 3 | 4 |
| Coke, declared barrel-equivalent convention | 0 | 0 | 3 |
| Refinery fuel, memo | 8 | 12 | 13 |
| Processing gain, memo | 3 | 10 | 15 |

```
scenario feed = eligible crude capacity * utilization_pct / 100
liquid product = scenario feed * product_yield_pct / 100
liquids + coke equivalent + refinery fuel = feed + processing gain
```

Utilization defaults to the 100% nameplate scenario and can range from 0% to 100%.
Yield percentages use modeled feed, excluding plants without product estimates.
Utilization does not change installed capacity or Nelson CI. At 0% utilization,
modeled output is zero and feed-based percentages are unavailable.

Fuel and gain are textbook balance memos, never additional salable products.
Fuel is the table's refinery-fuel line, not a separately measured loss. The UI
shows these percentages without assigning liquid gallons or litres.

### Coke and unit conversions

Liquid conversions: 1 bbl = 42 US gallons = 158.987294928 litres.

Coke is solid. For this scenario only, the table's coke percentage is interpreted
as barrel-equivalent using the [EIA convention of five barrels per short
ton](https://www.eia.gov/dnav/pet/tbldefs/pet_pnp_capfuel_tbldef2.asp):

```
coke short ton/d = coke kbbl-equivalent/d * 1000 / 5
```

This is a declared reporting convention, not a plant-specific density or measured
mass yield. Coke always displays/exports in short tons/day regardless of liquid
unit selection and is excluded from total liquids. A mass-percent coker yield
cannot be multiplied by crude volume without feed density; no such conversion is
performed here.

[EIA refinery yields](https://www.eia.gov/tools/glossary/index.php?id=R) account for
other hydrocarbons, unfinished oils and product-specific adjustments. Textbook
percentages do not substitute for reported yields or measured production.

## Estimated Nelson Complexity Index

```
CI = 1 + sum(complexity_factor * active_unit_capacity / crude_capacity)
```

Factors are verified against **Kaiser, de Klerk, Gary and Handwerk, Petroleum
Refining: Technology, Economics, and Markets (2019), Table 7.1**, printed p.156
(PDF p.189): vacuum distillation 2; visbreaking 2.75; coking, FCC and
hydrocracking 6; reforming 5; hydrorefining 3; hydrotreating 2; alkylation and
polymerization 10; aromatics/isomerization 15; lubes 10; asphalt 1.5; hydrogen 1.

Treatment processes take precedence over feed names: VGO, lube, FCC gasoline and
reformer-feed hydrotreaters use the hydrotreating factor. Reformate splitters are
not reformers. Utilities without a supported factor are excluded.

Hydrogen production in MMcfd is compared numerically to crude capacity in kbbl/d,
following **Table 7.6**, printed p.161 (PDF p.194). This is a Nelson normalization,
not a physical gas-to-oil conversion. Purchased hydrogen feed does not count as
installed production capacity. The historic Delaware City example calculates
12.9368 from unrounded capacities, rounding to the published 12.9; it is a test
fixture, not a claim about today's plant.

Unknown crude capacity and bitumen-upgrader configurations have unavailable CI.
Weighted averages exclude unavailable values and their capacities. Unit coverage
and calendar-day versus stream-day capacity bases may differ from operator
indices. No empirical calibration or accuracy bound is claimed.

## Ownership, export and limits

- Parent-company grouping is not equity attribution; JV shares are unavailable.
- HHI = sum(capacity share squared) * 10,000. HHI and top-three shares use known
  capacity and exclude plants with missing capacity from the denominator.
- CSV records model availability, capacity basis, utilization, modeled feed,
  estimated CI and explicit product units. Missing estimates are blank. Coke is
  `Coke_short_ton_d` with the equivalent conversion recorded. Text is escaped and
  protected against spreadsheet formula interpretation.
- No live runs, crude assay, mass/energy balance, unit constraints, downtime,
  imported blendstocks, specification optimization or margin model is available.
- Prior arbitrary splitter/upgrader yields, secondary-unit-derived crude inputs
  and unverified historical accuracy/benchmark claims were removed. Maples and
  the supplied derivatives books do not provide current physical inputs and are
  not presented as validation of current production.

## Verification

The September 2026 status reconciliation identifies both idle entries in
[EIA Table 3, PDF p.10 / printed p.14](https://www.eia.gov/petroleum/refinerycapacity/table3.pdf#page=10):
CPI Operations LLC at Paulsboro, NJ (IIR `1516659`), and Foreland/Eagle Springs
at Ely, NV (IIR `1026495`). On January 1, 2026, their idle crude capacities were
32,000 and 2,000 bbl/calendar-day respectively (35,000 and 5,000 bbl/stream-day).
CPI is a separate facility from operating Paulsboro Refining Co LLC (`1008919`).
Their original IIR capacity and unit rows remain available; the EIA day bases
are recorded separately rather than silently replacing those capacities.

Eagle Springs had announced a July restart, but Sky Quarry's
[Q2 2026 Form 10-Q, signed August 12, Note 3](https://www.sec.gov/Archives/edgar/data/1812447/000109690626001217/skyq-20260630_10q.htm)
states that operations had not restarted by the report date. Its
[undated homepage](https://skyquarry.com/) describes active processing. No later
dated restart confirmation was verified, so the app retains a dated idle status
with explicit restart uncertainty. Neither status is presented as a September
operating observation. Both plants are excluded from active modeled capacity,
process-unit totals and product scenarios. The reviewed override file and
reconciler retain source dates and original IIR status, and skip future IIR
releases newer than the review for renewed reconciliation.

Run `node --test scripts/test_refinery_model.cjs`. It covers source-table balance,
utilization, coke presentation, unavailable versus zero, inactive plants/units,
duplicate units, missing CDU inputs, process classification, purchased hydrogen,
the published Nelson example, and the current refinery dataset.
Where subprocess spawning is restricted, use
`node --test --test-isolation=none scripts/test_refinery_model.cjs`.
