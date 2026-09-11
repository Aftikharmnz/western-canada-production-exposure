const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

function app(fetch = async () => { throw new Error('Unexpected network request'); }, globals = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../src/main.js'), 'utf8').replace(/^boot\(\);/m, '');
  const context = { window: {}, document: { querySelector: () => null, getElementById: () => null },
    console, fetch, URL, URLSearchParams, AbortController, setTimeout, clearTimeout, setInterval, clearInterval, ...globals };
  return vm.runInNewContext(source + '\n({state,els,requestJson,requireFeatureCollection,ensureDateRecords,missingSourcesForDate,renderTimeline,normalizeBearing,parseDDM,geometryContainsPoint,distanceToGeometryKm,selectWindPair,powerSnapshotStale,computeSeasonality,fetchPipelineData,syncPipelineTileCategory,renderMarketPipelineTooltip,renderPipelineSegmentTooltip,bindPipelineCard})', context);
}
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });

test('HTTP-200 API error, malformed JSON and truncation are not empty success', async () => {
  for (const data of [{ error: { message: 'Invalid query' } }, { exceededTransferLimit: true }, { properties: { exceededTransferLimit: true } }]) {
    await assert.rejects(app(async () => response(data)).requestJson('/test'));
  }
  await assert.rejects(app(async () => response({}, 503)).requestJson('/test'), /503/);
  await assert.rejects(app(async () => ({ ok: true, json: async () => { throw new Error('bad JSON'); } })).requestJson('/test'), /bad JSON/);
});

test('request timeout aborts a hanging source', async () => {
  const a = app((_url, { signal }) => new Promise((_resolve, reject) => signal.addEventListener('abort', () => reject(new Error('aborted')))));
  await assert.rejects(a.requestJson('/test', { timeoutMs: 5 }), { name: 'TimeoutError' });
});

test('failed monthly requests remain retryable and invalid asset references are rejected', async () => {
  let attempts = 0;
  const a = app(async () => ++attempts === 1 ? response({}, 503) : response({ date: '2026-07-31', source_id: 'ab', stream: 'Oil', rows: [[0, 2.5]] }));
  a.state.assets = [{ asset_id: 'a' }]; a.state.assetById.set('a', a.state.assets[0]);
  a.state.manifest = { monthly_record_files: { '2026-07-31': 'month.json' } };
  await a.ensureDateRecords('2026-07-31');
  assert.equal(a.state.dateRecordCache.has('2026-07-31'), false);
  assert.equal(a.state.dateRecordErrors.has('2026-07-31'), true);
  a.state.timelineCache = new Map([['2026-07-31', 0]]);
  await a.ensureDateRecords('2026-07-31');
  assert.equal(a.state.dateRecordCache.get('2026-07-31')[0].volume_kbbl_d, 2.5);
  assert.equal(a.state.dateRecordErrors.has('2026-07-31'), false);
  assert.equal(a.state.timelineCache, null, 'Successful month/retry invalidates cached partial timeline totals');
});

test('a forecast or another stream does not hide a missing actual source stream', () => {
  const a = app();
  a.state.selectedSources.add('st39'); a.state.selectedStreams.add('Synthetic');
  a.state.manifest = { date_filter_totals: { '2026-09-30': [{ source_id: 'st39', stream: 'Mined', scenario: 'actual' }, { source_id: 'st39', stream: 'Synthetic', scenario: 'forecast' }] }, source_coverage: [{ source_id: 'st39', stream: 'Synthetic', scenario: 'actual', first_date: '2017-01-31', last_date: '2026-01-31' }] };
  assert.equal(a.missingSourcesForDate('2026-09-30').length, 1);
});

test('unloaded-month timeline does not add base data twice', () => {
  const a = app(); const date = '2026-07-31';
  a.state.dates = [date]; a.state.selectedDate = date;
  a.state.selectedSources.add('ab'); a.state.selectedStreams.add('Oil');
  a.state.manifest = { monthly_record_files: { [date]: 'm.json' }, date_filter_totals: { [date]: [{ source_id: 'ab', stream: 'Oil', location_confidence: 'exact', kbbl_d: 300 }] } };
  a.state.baseRecordsByDate.set(date, [{ asset_id: 'a', date, source_id: 'ab', stream: 'Oil', volume_kbbl_d: 100 }]);
  a.state.assetById.set('a', { asset_id: 'a', latitude: 55, longitude: -112, location_confidence: 'exact' });
  a.renderTimeline();
  assert.equal(a.state.timelineCache.get(date), 300);
});

test('search history distinguishes unloaded months from measured zero', () => {
  const a = app(); const date = '2026-07-31';
  a.state.dates = [date]; a.state.selectedDate = date; a.state.search = 'suncor';
  a.state.manifest = { monthly_record_files: { [date]: 'm.json' } };
  a.els.timelineLabel = { textContent: '' };
  a.renderTimeline();
  assert.equal(a.state.timelineCache.get(date), null);
  assert.match(a.els.timelineLabel.textContent, /1 search totals not loaded/);
  a.state.dateRecordCache.set(date, []); a.state.timelineCache = null;
  a.renderTimeline();
  assert.equal(a.state.timelineCache.get(date), 0);
  assert.doesNotMatch(a.els.timelineLabel.textContent, /not loaded/);
});

test('geographic screening respects holes and segment interiors', () => {
  const a = app();
  const feature = { geometry: { type: 'Polygon', coordinates: [[[0,0],[4,0],[4,4],[0,4],[0,0]], [[1,1],[3,1],[3,3],[1,3],[1,1]]] } };
  assert.equal(a.geometryContainsPoint(feature, .5, .5), true);
  assert.equal(a.geometryContainsPoint(feature, 2, 2), false);
  const distance = a.distanceToGeometryKm(feature, -1, 2);
  assert.ok(distance > 110 && distance < 112, `distance to midpoint: ${distance}`);
  assert.ok(Math.abs(a.parseDDM('-112° 56.7841') + 112.9464016667) < 1e-8);
  assert.ok(Number.isNaN(a.parseDDM('53° 61')));
  assert.equal(a.normalizeBearing(null), null);
});

test('wind requires the same station, forecast time and model run; m/s converts to km/h', () => {
  const a = app(); const now = new Date('2026-09-10T06:00:00Z');
  const feature = (variable, value, forecast, unit) => ({ geometry: { coordinates: [-112,57] }, properties: { variable, forecast_value: value, unit, prognos_station_id: 's', forecast_datetime: forecast, reference_datetime: '2026-09-10T00:00:00Z' } });
  const dir = feature('WindDir', 90, now.toISOString(), 'degree');
  assert.equal(a.selectWindPair([dir], [feature('WindSpeed', 10, '2026-09-09T00:00:00Z', 'km/h')], { lat:57,lon:-112 }, now), null);
  assert.equal(a.selectWindPair([dir], [feature('WindSpeed', 10, now.toISOString(), 'm/s')], { lat:57,lon:-112 }, now).speedKmh, 36);
});

test('stale AESO observations cannot be made fresh by a new fetch timestamp', () => {
  const a = app(); const now = Date.parse('2026-09-10T06:00:00Z');
  assert.equal(a.powerSnapshotStale({ observed_at: '2026-09-10T01:00:00Z', generated_at: '2026-09-10T06:00:00Z' }, now), true);
  assert.equal(a.powerSnapshotStale({ observed_at: '2026-09-10T05:55:00Z' }, now), false);
});

test('seasonality excludes forecasts and retains reported zero months', () => {
  const a = app();
  a.state.baseRecords = [{ asset_id:'a', date:'2026-01-31', volume_kbbl_d:0, scenario:'actual' }, { asset_id:'a', date:'2026-02-28', volume_kbbl_d:100, scenario:'forecast' }];
  const season = a.computeSeasonality(['a']);
  assert.equal(season.ym[2026][1], 0); assert.equal(season.ym[2026][2], undefined);
});

test('pipeline dictionary schema used by the shipped index loads', async () => {
  const index = JSON.parse(fs.readFileSync(path.join(__dirname, '../public/data/aer_pipeline_index.json'), 'utf8'));
  const a = app(async () => response(index));
  assert.equal(await a.fetchPipelineData(), true);
});

test('pipeline cards use sourced capacity units and endpoints without inventing feeder capacity', () => {
  const a = app(undefined, { window: { location: { href: 'https://example.com/' } } });
  const html = a.renderMarketPipelineTooltip({ route_name: 'Example line', pipeline_details: {
    origin: 'Origin terminal', destination: 'Destination terminal', capacity_kbbl_d: 890,
    capacity_basis: 'nominal', product: 'Crude oil / refined products', capacity_note: 'Combined system capacity; not the capacity of each mapped segment.',
    source_url: 'https://example.com/official', source_name: 'Operator', verified_at: '2026-09-11',
  } });
  assert.match(html, /890,000 bbl\/d/);
  assert.match(html, /nominal/);
  assert.match(html, /Product<\/span><span class="pt-route-val">Crude oil \/ refined products/);
  assert.match(html, /Origin terminal/);
  assert.match(html, /Destination terminal/);
  assert.match(html, /not the capacity of each mapped segment/);
  assert.match(html, /href="https:\/\/example.com\/official"/);
  assert.match(a.renderMarketPipelineTooltip({ pipeline_details: { capacity_kbbl_d: null } }), /Not published/);
  assert.doesNotMatch(a.renderMarketPipelineTooltip({ pipeline_details: { capacity_kbbl_d: null } }), /0 bbl\/d/);
  assert.match(a.renderMarketPipelineTooltip({ pipeline_details: { capacity_kbbl_d: 100, capacity_basis: 'operating' } }), /Published operating capacity/);
  const feeder = a.renderPipelineSegmentTooltip({ licence: '123', segment_line: '4', from_fac: 'Well', from_loc: '01-01',
    to_fac: 'Battery', to_loc: '02-02', diameter_mm: '610', maop_kpa: '10000', h2s_pct: 0,
    substance: 'Crude Oil', substance2: 'Condensate', substance3: 'Crude Oil' });
  assert.match(feeder, /Licence 123 · segment 4/);
  assert.match(feeder, /Well · 01-01/); assert.match(feeder, /Battery · 02-02/);
  assert.match(feeder, /Nameplate capacity<\/span><strong>Not published/);
  assert.match(feeder, /H₂S 0%/);
  assert.match(feeder, /Product<\/span><span class="pt-route-val">Crude Oil \/ Condensate/);
  assert.doesNotMatch(feeder, /610,000 bbl\/d/);
});

test('pipeline hover cards and tap popups escape external facts and unsafe links', () => {
  const a = app(undefined, { window: { location: { href: 'https://example.com/' } } });
  const html = a.renderMarketPipelineTooltip({ route_name: '<script>bad()</script>', pipeline_details: {
    origin: '<img src=x>', destination: '&destination', capacity_label: '<b>bad</b>', source_url: 'javascript:bad()',
  } });
  assert.doesNotMatch(html, /<script>|<img|href="javascript:/);
  assert.match(html, /&lt;script&gt;/); assert.match(html, /&amp;destination/);
  const bindings = {};
  const events = {};
  let tooltipClosed = 0;
  a.bindPipelineCard({ bindTooltip: (value, options) => { bindings.hover = { value, options }; },
    bindPopup: (value, options) => { bindings.tap = { value, options }; },
    on: (event, handler) => { events[event] = handler; },
    closeTooltip: () => { tooltipClosed++; }, isPopupOpen: () => true }, html);
  assert.equal(bindings.hover.value, html); assert.equal(bindings.tap.value, html);
  assert.equal(bindings.hover.options.sticky, true); assert.equal(bindings.tap.options.autoPan, true);
  events.popupopen(); events.mouseover();
  assert.equal(tooltipClosed, 2, 'A pinned card hides the duplicate hover card, including on re-entry');
});

test('late pipeline tiles remain cached but hidden after zooming out or panning away', async () => {
  for (const action of ['zoom', 'pan', 'hide']) {
    let resolveRequest;
    let requests = 0;
    let zoom = 6;
    let longitude = -112;
    const visible = new Set();
    const a = app(() => { requests++; return new Promise((resolve) => { resolveRequest = resolve; }); }, {
      L: { geoJSON: () => ({ addTo() { visible.add(this); } }) },
    });
    a.state.pipelineEnabled = true;
    a.state.map = {
      getZoom: () => zoom,
      getBounds: () => ({ pad() { return this; }, getWest: () => longitude, getEast: () => longitude,
        getNorth: () => 55, getSouth: () => 55 }),
      hasLayer: (layer) => visible.has(layer), removeLayer: (layer) => visible.delete(layer),
    };
    const entry = { tile_zoom: 6, tile_template: '/tiles/{z}/{x}/{y}.json', tile_keys: ['12/20'] };
    const pending = a.syncPipelineTileCategory('pipe-oil', entry, true);
    if (action === 'zoom') zoom = 5;
    if (action === 'pan') longitude = -80;
    if (action === 'hide') a.state.pipelineEnabled = false;
    await a.syncPipelineTileCategory('pipe-oil', entry, action !== 'hide');
    resolveRequest(response({ type: 'FeatureCollection', features: [] }));
    await pending;
    assert.equal(visible.size, 0, action);
    // Returning to the original viewport reuses the completed request.
    zoom = 6; longitude = -112; a.state.pipelineEnabled = true;
    await a.syncPipelineTileCategory('pipe-oil', entry, true);
    assert.equal(visible.size, 1, action);
    assert.equal(requests, 1, action);
  }
});
