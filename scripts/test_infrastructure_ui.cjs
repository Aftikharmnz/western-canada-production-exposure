const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

function app(globals = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../src/main.js'), 'utf8').replace(/^boot\(\);/m, '');
  const context = { window: { location: { href: 'https://example.com/app/' } },
    document: { querySelector: () => null, getElementById: () => null },
    console, URL, URLSearchParams, AbortController, setTimeout, clearTimeout, setInterval, clearInterval,
    fetch: async () => { throw new Error('Infrastructure UI tests must not make network requests'); }, ...globals };
  return vm.runInNewContext(source + '\n({state,RAIL_OWNER_META,DEFAULT_RAILWAY_CATEGORIES,infrastructureMatchesSearch,marketPipelineFeatures,selectedMarketPipelineFeatures,selectedRailwayFeatures,railwayTooltipHtml,terminalCardHtml,terminalSearchResultsHtml,buildMarketPipelineMenu,buildRailwayMenu,handleRailwayMenuChange,handleRailwayMenuClick,renderMarketHubTooltip,renderMarketPipelineTooltip,renderRailwayLayer})', context);
}

function feature(id, properties, geometryType = 'Point') {
  return { type: 'Feature', properties: { facility_id: id, ...properties },
    geometry: { type: geometryType, coordinates: geometryType === 'Point' ? [-76.5, 39.1] : [[-76.5, 39.1], [-76.4, 39.2]] } };
}

const terminal = (id, operator, extra = {}) => feature(id, {
  feature_kind: 'terminal', category: 'product-terminal', name: 'Baltimore', operator,
  state: 'Maryland', country: 'US', status: 'unknown', review_status: 'inventory_only',
  source_as_of: '2020', source: 'EIA terminal inventory',
  source_url: 'https://example.com/identity', coordinate_source_url: 'https://example.com/coordinates',
  location_confidence: 'Source inventory point; accuracy not established', ...extra,
});

const rail = (id, owner, category = 'rail-main') => feature(id, {
  feature_kind: 'rail_line', category, name: 'Rail corridor', owner,
}, 'LineString');

function railOwnerEvent(key, checked) {
  const input = { dataset: { railwayOwner: key }, checked };
  return { target: { closest: selector => selector === 'input[data-railway-owner]' ? input : null } };
}

function railCategoryEvent(key, checked) {
  const input = { dataset: { railwayCategory: key }, checked };
  return { target: { closest: selector => selector === 'input[data-railway-category]' ? input : null } };
}

function railActionEvent(action) {
  return { target: { closest: selector => selector === '[data-railway-action]' ? { dataset: { railwayAction: action } } : null } };
}

function railTestMap() {
  const removed = [];
  const fakeL = { geoJSON: (collection, options) => {
    collection.features.forEach(feature => {
      const item = { feature, bindTooltip() { return this; }, bindPopup() { return this; }, on() { return this; } };
      options.onEachFeature(feature, item);
    });
    return { features: collection.features, addTo() { return this; }, bringToBack() {} };
  } };
  const a = app({ window: { L: fakeL, location: { href: 'https://example.com/' } }, L: fakeL });
  a.state.map = { removeLayer(layer) { removed.push(layer); } };
  a.state.railwayEnabled = true;
  a.state.selectedRailwayCategories = new Set(['rail-main', 'product-terminal']);
  return { a, removed };
}

test('every railroad owner legend entry has a checkbox selected by default, including fallback owners', () => {
  const options = { innerHTML: '' };
  const a = app({ document: { querySelector: () => null, getElementById: id => id === 'railwayOptions' ? options : null } });
  a.state.railwayData = { features: [rail('cn', 'CN'), rail('unknown-owner', 'UNLISTED'), terminal('facility', 'Operator')] };
  a.buildRailwayMenu();
  const inputs = options.innerHTML.match(/<input[^>]*data-railway-owner=[^>]*>/g);
  assert.equal(inputs.length, 8);
  for (const key of ['cn', 'cpkc', 'bnsf', 'up', 'csx', 'ns', 'passenger', 'other']) {
    const input = inputs.find(html => html.includes(`data-railway-owner="${key}"`));
    assert.ok(input, `${key} must be independently selectable`);
    assert.match(input, /\bchecked\b/);
    assert.equal(a.state.selectedRailwayOwners.has(key), true);
  }
});

test('owner checkboxes use the colour grouping and hide only the corresponding railroad geometry', () => {
  const a = app();
  a.state.railwayData = { features: [
    rail('cn-alias', 'GTW'), rail('cp', 'CP'), rail('kcs', 'KCS'), rail('joint-cpkc-first', 'CPKC, UP'),
    rail('up-first', 'UP, CP'), rail('passenger', 'AMTK'), rail('regional', 'UNLISTED'), rail('no-owner', ''),
    terminal('cn-terminal', 'CN', { owner: 'CN' }),
  ] };
  a.handleRailwayMenuChange(railOwnerEvent('cpkc', false));
  assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id),
    ['cn-alias', 'up-first', 'passenger', 'regional', 'no-owner', 'cn-terminal']);
  a.handleRailwayMenuChange(railOwnerEvent('cn', false));
  assert.equal(a.selectedRailwayFeatures().some(feature => feature.properties.facility_id === 'cn-terminal'), true,
    'A terminal owner or operator must not be treated as a rail-line owner');
  a.handleRailwayMenuChange(railOwnerEvent('other', false));
  assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id),
    ['up-first', 'passenger', 'cn-terminal']);
  a.handleRailwayMenuChange(railOwnerEvent('cpkc', true));
  assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id),
    ['cp', 'kcs', 'joint-cpkc-first', 'up-first', 'passenger', 'cn-terminal']);
});

test('owner filtering invalidates cached lines, combines with categories, and preserves facility selections', () => {
  const { a, removed } = railTestMap();
  a.state.railwayData = { features: [rail('cn-main', 'CN'), rail('cp-main', 'CP'), rail('cn-lead', 'CN', 'rail-industrial'),
    terminal('buckeye', 'Buckeye'), terminal('colonial', 'Colonial')] };
  a.renderRailwayLayer();
  const allLines = a.state.railwayLineLayer;
  a.handleRailwayMenuChange(railOwnerEvent('cn', false));
  assert.ok(removed.includes(allLines), 'Owner changes must invalidate the cached rail layer');
  assert.deepEqual(Array.from(a.state.railwayLineLayer.features, feature => feature.properties.facility_id), ['cp-main']);
  assert.deepEqual(Array.from(a.state.railwayLayer.features, feature => feature.properties.facility_id), ['buckeye', 'colonial']);
  const cpLines = a.state.railwayLineLayer;
  a.state.railwaySearch = 'Buckeye';
  a.renderRailwayLayer();
  assert.equal(a.state.railwayLineLayer, cpLines, 'Facility search must retain the filtered rail instance');
  a.handleRailwayMenuChange(railCategoryEvent('rail-industrial', true));
  assert.deepEqual(Array.from(a.state.railwayLineLayer.features, feature => feature.properties.facility_id), ['cp-main']);
  a.handleRailwayMenuChange(railOwnerEvent('cn', true));
  assert.deepEqual(Array.from(a.state.railwayLineLayer.features, feature => feature.properties.facility_id), ['cn-main', 'cp-main', 'cn-lead']);
  a.handleRailwayMenuChange(railCategoryEvent('rail-main', false));
  assert.deepEqual(Array.from(a.state.railwayLineLayer.features, feature => feature.properties.facility_id), ['cn-lead']);
  a.handleRailwayMenuChange(railCategoryEvent('rail-main', true));
  assert.deepEqual(Array.from(a.state.railwayLayer.features, feature => feature.properties.facility_id), ['buckeye']);
  for (const { key } of a.RAIL_OWNER_META) a.handleRailwayMenuChange(railOwnerEvent(key, false));
  assert.equal(a.state.railwayLineLayer, null);
  assert.deepEqual(Array.from(a.state.railwayLayer.features, feature => feature.properties.facility_id), ['buckeye'],
    'Hiding every railroad must leave the selected facility points visible');
});

test('rail owner checkbox state survives basemap, facility search and menu redraws', () => {
  const options = { innerHTML: '' };
  const a = app({ document: { querySelector: () => null, getElementById: id => id === 'railwayOptions' ? options : null } });
  a.state.railwayData = { features: [rail('cn', 'CN'), rail('cp', 'CP'), terminal('buckeye', 'Buckeye')] };
  a.handleRailwayMenuChange(railOwnerEvent('cn', false));
  for (const [basemap, search] of [['dark', 'Buckeye'], ['light', ''], ['satellite', 'no matching facility']]) {
    a.state.basemapKey = basemap;
    a.state.railwaySearch = search;
    a.buildRailwayMenu();
    const cnInput = options.innerHTML.match(/<input[^>]*data-railway-owner="cn"[^>]*>/)[0];
    const cpInput = options.innerHTML.match(/<input[^>]*data-railway-owner="cpkc"[^>]*>/)[0];
    assert.doesNotMatch(cnInput, /\bchecked\b/);
    assert.match(cpInput, /\bchecked\b/);
    assert.equal(a.state.selectedRailwayOwners.has('cn'), false);
  }
});

test('Core and All restore every owner while None clears categories without resetting owner choices', () => {
  const a = app();
  a.handleRailwayMenuChange(railOwnerEvent('cn', false));
  a.handleRailwayMenuClick(railActionEvent('none'));
  assert.equal(a.state.selectedRailwayCategories.size, 0);
  assert.equal(a.state.railwayEnabled, false);
  assert.equal(a.state.selectedRailwayOwners.has('cn'), false);
  a.handleRailwayMenuChange(railOwnerEvent('cpkc', false));
  assert.equal(a.state.railwayEnabled, false, 'An owner checkbox alone must not enable an unselected rail category');
  a.handleRailwayMenuClick(railActionEvent('defaults'));
  assert.deepEqual(Array.from(a.state.selectedRailwayCategories), Array.from(a.DEFAULT_RAILWAY_CATEGORIES));
  assert.equal(a.state.selectedRailwayOwners.size, 8);
  assert.equal(a.state.railwayEnabled, true);
  a.handleRailwayMenuChange(railOwnerEvent('other', false));
  a.handleRailwayMenuClick(railActionEvent('all'));
  assert.equal(a.state.selectedRailwayOwners.size, 8);
  assert.equal(a.state.selectedRailwayCategories.has('rail-industrial'), true);
  assert.equal(a.state.selectedRailwayCategories.has('inactive-terminal'), true);
});

test('infrastructure search matches all case/accent-insensitive tokens across names and identity fields', () => {
  const a = app();
  const properties = { name: 'Montréal East', operator: 'Énergie Valero', province: 'Québec',
    reported_name: 'Former terminal name', reported_operator: 'Historic operator',
    facility_id: 'ca-valero-montreal', address: '123 Terminal Road', commodity: 'Refined products' };
  assert.equal(a.infrastructureMatchesSearch(properties, 'VALERO montreal'), true);
  assert.equal(a.infrastructureMatchesSearch(properties, 'quebec terminal'), true);
  assert.equal(a.infrastructureMatchesSearch(properties, 'historic former'), true);
  assert.equal(a.infrastructureMatchesSearch(properties, 'ca-valero-montreal'), true);
  assert.equal(a.infrastructureMatchesSearch(properties, '123 products'), true);
  assert.equal(a.infrastructureMatchesSearch(properties, 'valero sherbrooke'), false);
  assert.equal(a.infrastructureMatchesSearch(properties, 'colonial'), false, 'An operator or place does not imply an unsourced pipeline connection');
  assert.equal(a.infrastructureMatchesSearch(properties, '   '), true);
  assert.equal(a.infrastructureMatchesSearch({ name: 'Corunna Storage', city: 'Corunna', search_aliases: 'Sarnia Corunna' }, 'sarnia storage'), true);
});

test('named pipeline selection keeps Buckeye distinct from Colonial and other product networks', () => {
  const options = { innerHTML: '' };
  const a = app({ document: { querySelector: () => null, getElementById: id => id === 'marketPipelineOptions' ? options : null } });
  a.state.marketPipelineData = { features: [
    feature('unused', { feature_kind: 'pipeline', route_id: 'us-products-buckeye', route_name: 'Buckeye product network', operator: 'Buckeye' }, 'MultiLineString'),
    feature('unused', { feature_kind: 'pipeline', route_id: 'us-products-colonial', route_name: 'Colonial product network', operator: 'Colonial' }, 'MultiLineString'),
    feature('unused', { feature_kind: 'pipeline', route_id: 'us-products-explorer', route_name: 'Explorer product network', operator: 'Explorer' }, 'MultiLineString'),
  ] };
  a.state.selectedMarketPipelineIds.add('us-products-buckeye');
  a.state.marketPipelineSearch = 'Colonial';
  assert.deepEqual(Array.from(a.selectedMarketPipelineFeatures(), feature => feature.properties.route_id), ['us-products-buckeye'],
    'A menu search must not hide or replace routes already selected on the map');
  const matching = a.marketPipelineFeatures().filter(feature => a.infrastructureMatchesSearch(feature.properties, a.state.marketPipelineSearch));
  assert.deepEqual(Array.from(matching, feature => feature.properties.route_id), ['us-products-colonial']);
  a.buildMarketPipelineMenu();
  assert.match(options.innerHTML, /data-market-pipeline-id="us-products-colonial"/);
  assert.doesNotMatch(options.innerHTML, /data-market-pipeline-id="us-products-buckeye"/);
  assert.equal(a.state.selectedMarketPipelineIds.has('us-products-buckeye'), true);
});

test('terminal search separates shared place names while retaining selected rail line context', () => {
  const a = app();
  const rail = feature('rail-main', { feature_kind: 'rail_line', category: 'rail-main', name: 'Rail corridor' }, 'LineString');
  a.state.railwayData = { features: [rail, terminal('buckeye-baltimore', 'Buckeye Terminals'), terminal('colonial-baltimore', 'Colonial Pipeline')] };
  a.state.selectedRailwayCategories = new Set(['rail-main', 'product-terminal']);
  a.state.railwaySearch = 'colonial baltimore';
  assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id), ['rail-main', 'colonial-baltimore']);
  a.state.railwaySearch = 'buckeye';
  assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id), ['rail-main', 'buckeye-baltimore']);
  a.state.railwaySearch = 'unmatched terminal';
  assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id), ['rail-main']);
});

test('crude, product and NGL storage categories select their own facilities without implying rail service', () => {
  const a = app();
  a.state.railwayData = { features: [
    terminal('product-terminal', 'Operator'),
    terminal('crude-tanks', 'Storage Operator', { category: 'crude-storage', facility_type: 'Crude oil tank storage', modes: 'Pipeline / truck' }),
    terminal('product-tanks', 'Storage Operator', { category: 'product-storage', facility_type: 'Product tank storage' }),
    terminal('ngl-cavern', 'Storage Operator', { category: 'ngl-storage', facility_type: 'NGL cavern storage' }),
  ] };
  for (const [category, expected] of [['crude-storage', 'crude-tanks'], ['product-storage', 'product-tanks'], ['ngl-storage', 'ngl-cavern']]) {
    a.state.selectedRailwayCategories = new Set([category]);
    assert.deepEqual(Array.from(a.selectedRailwayFeatures(), feature => feature.properties.facility_id), [expected]);
  }
  const html = a.railwayTooltipHtml(a.state.railwayData.features[1].properties);
  assert.match(html, /Crude oil tank storage/);
  assert.match(html, /Pipeline \/ truck/);
  assert.doesNotMatch(html, /Rail-served|Rail loading confirmed/i);
});

test('inventory-only terminal cards preserve the source snapshot and do not claim current verified status', () => {
  const a = app();
  const properties = terminal('historical-terminal', 'Source-record operator', {
    reported_name: 'Historical terminal', reported_operator: 'Old operator',
    reviewed_at: null, status: 'unknown', review_status: 'historical_unverified',
  }).properties;
  const html = a.railwayTooltipHtml(properties);
  assert.match(html, /2020/);
  assert.match(html, /unknown|unverified|not verified|historical/i);
  assert.match(html, /Old operator/);
  assert.match(html, /historical-terminal/);
  assert.doesNotMatch(html, /Currently operating|Current verified|Operator verified|Survey-grade|Exact location/i);
});

test('a review timestamp on an unverified inventory does not certify facility identity', () => {
  const a = app();
  const html = a.terminalCardHtml(terminal('inventory-review', 'Historical operator', {
    reviewed_at: '2026-10-11', last_verified: '2026-10-11', review_status: 'inventory_only', status: 'unknown',
  }).properties);
  assert.match(html, /not independently verified/i);
  assert.doesNotMatch(html, /<span class="pt-route-label">Identity reviewed<\/span>/);
});

test('facility search keeps distinct source records with the same name and operator', () => {
  const a = app();
  a.state.railwayData = { features: [terminal('record-a', 'Buckeye'), terminal('record-b', 'Buckeye')] };
  a.state.railwaySearch = 'buckeye baltimore';
  const html = a.terminalSearchResultsHtml();
  assert.match(html, /2 matching facilit(?:y records|ies)/);
  assert.match(html, /data-terminal-index="0"/);
  assert.match(html, /data-terminal-index="1"/);
  assert.match(html, /record-a/, 'The locator must distinguish otherwise identical facility records');
  assert.match(html, /record-b/, 'Names and operators alone cannot disambiguate separate inventory points');
});

test('reviewed terminal cards keep facility identity sources separate from coordinate evidence', () => {
  const a = app();
  const html = a.railwayTooltipHtml(terminal('reviewed-facility', 'Current operator', {
    name: 'Reviewed storage site', review_status: 'operator_verified', reviewed_at: '2026-10-11', status: 'operating',
    source_as_of: '2026-09', reported_operator: 'Historic record operator',
    coordinate_source_id: 'NPRI-12345', location_note: 'Reported facility centroid; tank positions are not surveyed',
  }).properties);
  assert.match(html, /2026-10-11/);
  assert.match(html, /Current operator/);
  assert.match(html, /Historic record operator/);
  assert.match(html, /href="https:\/\/example.com\/identity"/);
  assert.match(html, /href="https:\/\/example.com\/coordinates"/);
  assert.match(html, /NPRI-12345/);
  assert.match(html, /Reported facility centroid; tank positions are not surveyed/);
  assert.match(html, /reviewed-facility/);
  assert.doesNotMatch(html, /\b\d+(?:\.\d+)?\s*(?:million barrels|bbl\/d)\b/i, 'No storage capacity or throughput can be inferred from a point');
});

test('facility cards escape names and location evidence and reject unsafe source links', () => {
  const a = app();
  const html = a.railwayTooltipHtml(terminal('unsafe', '<script>operator()</script>', {
    name: '<img src=x onerror=bad()>', reported_name: '<svg onload=bad()>',
    location_note: '<b>unsupported accuracy</b>', source_url: 'javascript:bad()',
    coordinate_source_url: 'data:text/html,bad', review_status: 'inventory_only',
  }).properties);
  assert.match(html, /&lt;img/);
  assert.match(html, /&lt;script/);
  assert.match(html, /&lt;b&gt;unsupported accuracy/);
  assert.doesNotMatch(html, /<img|<script|<svg|href="(?:javascript:|data:)/i);
});

test('identity verification does not upgrade an approximate coordinate source to an exact location', () => {
  const a = app();
  const html = a.terminalCardHtml(terminal('address-geocoded', 'Verified operator', {
    review_status: 'operator_verified', reviewed_at: '2026-10-11', location_confidence: 'high',
    location_accuracy: 'Census address-match point; approximate location, not surveyed',
  }).properties);
  assert.match(html, /Census address-match point; approximate location, not surveyed/);
  assert.doesNotMatch(html, /Official facility point; not a surveyed boundary/);
});

test('market-area hub cards expose their approximate location instead of asserting a physical facility', () => {
  const a = app();
  const html = a.renderMarketHubTooltip({ name: 'Cushing', hub_type: 'Crude hub',
    source_summary: 'Public market-area reference',
    geometry_confidence: 'Approximate market-area centroid; not an individual facility or surveyed interconnect' });
  assert.match(html, /Area reference/i);
  assert.match(html, /Approximate market-area centroid/);
  assert.match(html, /not an individual facility/);
});

test('pipeline cards identify displayed operator geometry separately from archived inventory references', () => {
  const a = app();
  const html = a.renderMarketPipelineTooltip({ route_name: 'Buckeye',
    geometry_source_url: 'https://example.com/operator-map',
    geometry_confidence: 'Operator public map; not survey-grade',
    pipeline_details: { source_url: 'https://example.com/operator-facts', source_name: 'Operator facts',
      route_source_url: 'https://example.com/archived-inventory' } });
  assert.match(html, /href="https:\/\/example.com\/operator-map"/);
  assert.match(html, /displayed geometry|geometry source/i);
  assert.match(html, /href="https:\/\/example.com\/operator-facts"/);
});

test('terminal map points provide persistent tap/click details in addition to hover cards', () => {
  const bindings = [];
  const layer = { bindTooltip: () => layer, bindPopup: (html, options) => { bindings.push({ html, options }); return layer; },
    on: () => layer, closeTooltip() {}, isPopupOpen: () => false };
  const fakeL = { geoJSON: (collection, options) => {
    collection.features.forEach(feature => options.onEachFeature(feature, layer));
    return { addTo() { return this; }, bringToBack() {} };
  } };
  const a = app({ window: { L: fakeL, location: { href: 'https://example.com/' } }, L: fakeL });
  a.state.map = { removeLayer() {} };
  a.state.railwayEnabled = true;
  a.state.selectedRailwayCategories = new Set(['product-terminal']);
  a.state.railwayData = { features: [terminal('tap-terminal', 'Buckeye')] };
  a.renderRailwayLayer();
  assert.equal(bindings.length, 1);
  assert.match(bindings[0].html, /tap-terminal/);
  assert.equal(bindings[0].options.autoPan, true);
});

test('facility searches retain the rail context instance while line-category and source-data changes refresh it', () => {
  const removed = [];
  const fakeL = { geoJSON: (collection, options) => {
    collection.features.forEach(feature => {
      const item = { feature, bindTooltip() { return this; }, bindPopup() { return this; }, on() { return this; } };
      options.onEachFeature(feature, item);
    });
    return { features: collection.features, addTo() { return this; }, bringToBack() {} };
  } };
  const a = app({ window: { L: fakeL, location: { href: 'https://example.com/' } }, L: fakeL });
  a.state.map = { removeLayer(layer) { removed.push(layer); } };
  a.state.railwayEnabled = true;
  a.state.railwayData = { features: [
    feature('main-rail', { feature_kind: 'rail_line', category: 'rail-main', name: 'Main corridor' }, 'LineString'),
    feature('industrial-rail', { feature_kind: 'rail_line', category: 'rail-industrial', name: 'Industrial lead' }, 'LineString'),
    terminal('buckeye-terminal', 'Buckeye'), terminal('colonial-terminal', 'Colonial'),
  ] };
  a.state.selectedRailwayCategories = new Set(['rail-main', 'product-terminal']);
  a.renderRailwayLayer();
  const originalLineGroup = a.state.railwayLineLayer;
  const originalPointGroup = a.state.railwayLayer;
  assert.equal(originalLineGroup.features.length, 1);
  a.state.railwaySearch = 'Buckeye';
  a.renderRailwayLayer();
  assert.equal(a.state.railwayLineLayer, originalLineGroup, 'Point queries must not rebuild the large rail network');
  assert.notEqual(a.state.railwayLayer, originalPointGroup);
  assert.deepEqual(Array.from(a.state.railwayLayer.features, feature => feature.properties.facility_id), ['buckeye-terminal']);
  assert.equal(removed.includes(originalLineGroup), false);
  a.state.selectedRailwayCategories.add('rail-industrial');
  a.renderRailwayLayer();
  assert.notEqual(a.state.railwayLineLayer, originalLineGroup);
  assert.equal(a.state.railwayLineLayer.features.length, 2);
  const changedLineGroup = a.state.railwayLineLayer;
  a.state.railwayData = { features: a.state.railwayData.features };
  a.renderRailwayLayer();
  assert.notEqual(a.state.railwayLineLayer, changedLineGroup, 'A new source dataset must invalidate the line cache');
  a.state.railwayEnabled = false;
  a.renderRailwayLayer();
  assert.equal(a.state.railwayLineLayer, null);
  assert.equal(a.state.railwayLayer, null);
});

test('shipped product network routes retain separate Buckeye and Colonial source identities', () => {
  const data = JSON.parse(fs.readFileSync(path.join(__dirname, '../public/data/market_access_pipelines.geojson'), 'utf8'));
  const routes = new Map(data.features.filter(feature => feature.properties.feature_kind === 'pipeline').map(feature => [feature.properties.route_id, feature.properties]));
  const buckeye = routes.get('us-products-buckeye');
  const colonial = routes.get('us-products-colonial');
  assert.ok(buckeye, 'Buckeye must be independently selectable');
  assert.ok(colonial, 'Colonial must be independently selectable');
  assert.match(buckeye.route_name, /Buckeye/i);
  assert.match(colonial.route_name, /Colonial/i);
  assert.ok(buckeye.source_feature_ids.length > 0 && colonial.source_feature_ids.length > 0);
  const buckeyeIds = new Set(buckeye.source_feature_ids);
  assert.equal(colonial.source_feature_ids.some(id => buckeyeIds.has(id)), false, 'Distinct named network features must not reuse one source segment as both networks');
});
