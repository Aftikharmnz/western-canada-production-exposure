const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'src/main.js'), 'utf8');
const start = source.indexOf('const BBL_TO_GAL =');
const end = source.indexOf('function showRefineryPanel(', start);
assert.ok(start >= 0 && end > start, 'Find production model without booting the map');
const model = vm.runInNewContext(source.slice(start, end) + `\n({
  REFINERY_YIELD_SLATES, REFINED_PRODUCTS, estimateRefineryProducts,
  effectiveCrudeCharge, refineryUnitCapacities, refineryComplexity,
  nelsonCF, refineryHydrogenMMcfd, refVolFmt, refProductFmt
})`);

function unit(type, capacity, extra = {}) {
  return { unit_type_short: type, unit_type_desc: type, capacity_uom: 'BBL/d',
    capacity_kbbl_d: capacity, unit_status_group: 'Commissioned',
    unit_status_desc: 'Operational', ...extra };
}
function plant(units = [], extra = {}) {
  return { plant_name: 'Test refinery', plant_status_desc: 'Operational',
    crud_capacity_kbbl_d: 100, refinery_units: units, ...extra };
}
const coking = plant([unit('FCC', 40), unit('Delayed Coking', 30)]);
function near(actual, expected, tolerance = 1e-9) {
  assert.ok(Math.abs(actual - expected) < tolerance, `${actual} should equal ${expected}`);
}

test('Leffler scenarios close the equivalent balance without treating memos as products', () => {
  for (const slate of Object.values(model.REFINERY_YIELD_SLATES)) {
    const products = model.REFINED_PRODUCTS.reduce((n, p) => n + (slate[p.key] || 0), 0);
    near(products + slate.fuelLoss, 100 + slate.gain);
  }
  const full = model.estimateRefineryProducts(coking);
  assert.equal(full.cls, 'coking');
  near(full.products.gasoline, 60); near(full.products.coke, 3);
});

test('utilization scales feed/products while preserving capacity and zero semantics', () => {
  const a = model.estimateRefineryProducts(coking, 80);
  near(a.crude, 100); near(a.cap.crude, 100); near(a.feed, 80);
  near(a.products.gasoline, 48); near(a.products.coke, 2.4);
  const zero = model.estimateRefineryProducts(coking, 0);
  assert.equal(zero.modeled, true); assert.equal(zero.products.gasoline, 0);
  near(model.estimateRefineryProducts(coking, 120).feed, 100);
  near(model.estimateRefineryProducts(coking, -1).feed, 0);
  near(model.estimateRefineryProducts(coking, NaN).feed, 100);
});

test('liquid conversions are exact; coke never becomes gallons or litres', () => {
  near(model.refVolFmt(1, 'gal').raw, 42000);
  near(model.refVolFmt(1, 'l').raw, 158987.294928);
  for (const units of ['bbl', 'gal', 'l']) {
    const coke = model.refProductFmt('coke', 3, units);
    near(coke.raw, 600); assert.equal(coke.suffix, 'short ton/d');
  }
  assert.equal(model.refProductFmt('gasoline', null, 'bbl').raw, null);
});

test('secondary units cannot invent crude input; CDU fallback reaches capacity totals', () => {
  const missing = plant([unit('Delayed Coking', 30), unit('Vacuum Distillation', 50)], { crud_capacity_kbbl_d: null });
  assert.equal(model.effectiveCrudeCharge(missing).charge, 0);
  assert.equal(model.estimateRefineryProducts(missing).products.gasoline, null);
  assert.equal(model.refineryComplexity(missing), null);
  const cdu = plant([unit('CDU', 90), unit('FCC', 40)], { crud_capacity_kbbl_d: null });
  near(model.effectiveCrudeCharge(cdu).charge, 90);
  near(model.refineryUnitCapacities(cdu).crude, 90);
  const bbl = plant([], { crud_capacity_kbbl_d: null, crud_capacity_bbl_d: 85000 });
  near(model.effectiveCrudeCharge(bbl).charge, 85);
});

test('inactive plants/CDUs and duplicate unit IDs cannot inflate capacity or yield', () => {
  const duplicate = unit('FCC', 40, { unit_id: 1 });
  const p = plant([duplicate, { ...duplicate }, unit('Delayed Coking', 30, { unit_status_desc: 'Mothballed' })]);
  const r = model.estimateRefineryProducts(p);
  near(r.cap.fcc, 40); near(r.cap.coker, 0); assert.equal(r.cls, 'cracking');
  const closed = { ...coking, plant_status_desc: 'Closed' };
  assert.equal(model.estimateRefineryProducts(closed).modeled, false);
  assert.equal(model.refineryUnitCapacities(closed).fcc, 0);
  const idle = plant([unit('CDU', 100, { unit_status_group: 'Decommissioned', unit_status_desc: 'Mothballed' })]);
  assert.equal(model.effectiveCrudeCharge(idle).charge, 0);
});

test('visbreaking is not coking; unsupported splitters/upgraders have no invented products', () => {
  const r = model.estimateRefineryProducts(plant([unit('FCC', 40), unit('Visbreaker', 30)]));
  assert.equal(r.cls, 'cracking'); near(r.products.resid, 10); near(r.products.coke, 0);
  for (const name of ['Condensate Splitter', 'Scotford Upgrader']) {
    const r = model.estimateRefineryProducts(plant([unit('CDU', 100)], { plant_name: name }));
    assert.equal(r.modeled, false); assert.equal(r.products.gasoline, null);
    if (name === 'Scotford Upgrader') near(r.crude, 0);
  }
  assert.equal(model.estimateRefineryProducts(plant([unit('HCK', 50)])).modeled, false);
  assert.equal(model.estimateRefineryProducts(plant([unit('CDU', 100)])).modeled, false);
  assert.equal(model.estimateRefineryProducts(plant([unit('Reformer', 20), unit('Naphtha Hydrotreater', 20)])).cls, 'topping');
  assert.equal(model.refineryUnitCapacities(plant([unit('Reformate Splitter', 20)])).reformer, 0);
});

test('Nelson factors follow the process before its feed/service name', () => {
  for (const desc of ['Vacuum Gas Oil Hydrotreater', 'Lube Oil Hydrotreater', 'FCC Gasoline Hydrotreater', 'Reformer Feed Hydrotreater']) {
    assert.equal(model.nelsonCF(unit(desc, 10)), 2, desc);
  }
  assert.equal(model.nelsonCF(unit('Catalytic Hydrorefining', 10)), 3);
  assert.equal(model.nelsonCF(unit('Reformate Splitter', 10)), 0);
});

test('purchased hydrogen is excluded and Kaiser Table 7.6 reproduces 12.9 CI', () => {
  const units = [['Vacuum Distillation',102],['FCC',82],['Hydrotreating',160],
    ['HCK',18],['Reformer',43],['Benzene extraction',15],['Butane Isomerization',6],
    ['Alkylation',11],['Polymerization',16],['Fluid Coking',47]].map(([t,c]) => unit(t,c));
  const p = plant(units, { crud_capacity_kbbl_d: 190, plant_capacities: [
    { product_desc: 'Hydrogen', kind: 'Output', design_capacity: 62000, uom: 'k cubic ft/day' },
    { product_desc: 'Hydrogen', kind: 'Feed', design_capacity: 999000, uom: 'k cubic ft/day' },
  ] });
  near(model.refineryHydrogenMMcfd(p), 62);
  near(model.refineryComplexity(p), 1 + 2268 / 190);
  assert.equal(model.refineryComplexity(p).toFixed(1), '12.9');
});

test('current refinery records yield finite nonnegative scenarios or explicit unavailable values', () => {
  const data = JSON.parse(fs.readFileSync(path.join(root, 'public/data/refineries.geojson'), 'utf8'));
  let modeled = 0, unavailable = 0;
  for (const { properties: p } of data.features) {
    const r = model.estimateRefineryProducts(p, 90);
    assert.ok(Number.isFinite(r.crude) && r.crude >= 0, p.plant_name);
    for (const n of Object.values(r.cap)) assert.ok(Number.isFinite(n) && n >= 0, p.plant_name);
    for (const n of Object.values(r.products)) assert.ok(n === null || (Number.isFinite(n) && n >= 0), p.plant_name);
    const ci = model.refineryComplexity(p);
    assert.ok(ci === null || (Number.isFinite(ci) && ci >= 1), p.plant_name);
    if (r.modeled) {
      modeled++;
      const output = Object.values(r.products).reduce((a, n) => a + n, 0);
      near(output + r.fuelLoss, r.feed + r.gain, 1e-7);
    } else unavailable++;
  }
  assert.ok(modeled > 0 && unavailable > 0);
});
