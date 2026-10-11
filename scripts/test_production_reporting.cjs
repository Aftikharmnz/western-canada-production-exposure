const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

function app(elements = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../src/main.js'), 'utf8').replace(/^boot\(\);/m, '');
  const context = {
    window: {}, document: { querySelector: () => null, getElementById: (id) => elements[id] || null },
    console, URL, URLSearchParams, AbortController, setTimeout, clearTimeout, setInterval, clearInterval,
    fetch: async () => { throw new Error('Reporting tests must not make network requests'); },
  };
  return vm.runInNewContext(source + '\n({state,els,computeSeasonality,drawSeasonalityChart,renderTimeline,renderSeasonalityDetails,renderDetails,productionReportingForDate})', context);
}

function group(source, stream, months) {
  return { source_id: source, stream, months };
}

function setup(index, assets = []) {
  const a = app();
  a.state.seasonalityIndex = index;
  a.state.assets = assets;
  assets.forEach((asset) => a.state.assetById.set(asset.asset_id, asset));
  a.state.manifest = { source_coverage: [], date_filter_totals: {} };
  a.state.dates = ['2026-06-30', '2026-07-31', '2026-08-31'];
  return a;
}

function asset(id, source = 'early', stream = 'Oil') {
  return { asset_id: id, source_id: source, display_name: id, province: 'Alberta', company: 'Operator',
    asset_kind: 'well', production_system: 'conventional', latitude: 55, longitude: -112,
    location_confidence: 'exact', stream };
}

function mixedIndex() {
  return {
    late: { __groups: [0], '2026-06': 100, '2026-07': 100 },
    early: { __groups: [1], '2026-06': 20, '2026-07': 20, '2026-08': 20 },
    __reporting: { schema_version: 1, groups: [
      group('late-source', 'Oil', ['2026-06', '2026-07']),
      group('early-source', 'Oil', ['2026-06', '2026-07', '2026-08']),
    ] },
  };
}

test('mixed-source reporting lag keeps a provisional subtotal out of the complete series', () => {
  const a = setup(mixedIndex(), [asset('late', 'late-source'), asset('early', 'early-source')]);
  const data = a.computeSeasonality(['late', 'early']);
  assert.equal(data.months[2026][7].status, 'complete');
  assert.equal(data.months[2026][7].value, 120);
  const august = data.months[2026][8];
  assert.equal(august.status, 'partial');
  assert.equal(august.value, null);
  assert.equal(august.reportedTotal, 20);
  assert.equal(august.expectedGroupsCount, 2);
  assert.equal(august.reportingGroupsCount, 1);
  assert.equal(august.observedAssets, 1);
  assert.equal(august.selectedAssetCount, 2);
  assert.equal(august.unavailableAssetsCount, 1);
  assert.ok(august.missingSources.some((item) => item.source_id === 'late-source' && item.stream === 'Oil'));
});

test('unselected sources do not limit a selected source that has reported the latest month', () => {
  const a = setup(mixedIndex(), [asset('late', 'late-source'), asset('early', 'early-source')]);
  const august = a.computeSeasonality(['early']).months[2026][8];
  assert.equal(august.status, 'complete');
  assert.equal(august.value, 20);
  assert.equal(august.expectedGroupsCount, 1);
  assert.equal(august.missingSources.length, 0);
});

test('an explicit reported zero is complete and remains distinct from an absent asset observation', () => {
  const a = setup({
    zero: { __groups: [0], '2026-07': 100, '2026-08': 0 },
    absent: { __groups: [0], '2026-07': 100 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
  }, [asset('zero', 'source'), asset('absent', 'source')]);
  const zero = a.computeSeasonality(['zero']).months[2026][8];
  assert.equal(zero.status, 'complete');
  assert.equal(zero.reportedTotal, 0);
  assert.equal(zero.value, 0);
  assert.equal(zero.observedAssets, 1);
  const absent = a.computeSeasonality(['absent']).months[2026][8];
  assert.equal(absent.status, 'missing');
  assert.equal(absent.value, null);
  assert.equal(absent.reportedTotal, null);
  assert.equal(absent.observedAssets, 0);
});

test('source coverage does not require every sparse well to have an observation', () => {
  const a = setup({
    stopped: { __groups: [0], '2026-07': 100 },
    observed: { __groups: [0], '2026-07': 20, '2026-08': 20 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
  }, [asset('stopped', 'source'), asset('observed', 'source')]);
  const august = a.computeSeasonality(['stopped', 'observed']).months[2026][8];
  assert.equal(august.status, 'complete');
  assert.equal(august.value, 20);
  assert.equal(august.unavailableAssetsCount, 1);
  assert.equal(august.observedAssets, 1);
});

test('a missing component of a multi-stream asset stays provisional when another asset reports that stream', () => {
  const a = setup({
    plant: { __groups: [0, 1], __month_groups: { '2026-07': [0, 1], '2026-08': [1] },
      '2026-07': 120, '2026-08': 20 },
    well: { __groups: [0], '2026-07': 10, '2026-08': 10 },
    __reporting: { schema_version: 1, groups: [
      group('source', 'Oil', ['2026-07', '2026-08']),
      group('source', 'Condensate', ['2026-07', '2026-08']),
    ] },
  }, [asset('plant', 'source'), asset('well', 'source')]);
  const august = a.computeSeasonality(['plant', 'well']).months[2026][8];
  assert.equal(august.status, 'partial');
  assert.equal(august.value, null);
  assert.equal(august.reportedTotal, 30);
  assert.ok(august.missingSources.some((item) => item.source_id === 'source' && item.stream === 'Oil'));
});

test('an unreconciled high source-quality warning keeps the reported decline visible as provisional', () => {
  const a = setup({
    well: { __groups: [0], '2026-07': 100, '2026-08': 10 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
  }, [asset('well', 'source')]);
  a.state.manifest.data_quality = { date_warnings: {
    '2026-08-31': [{ source_id: 'source', stream: 'Oil', severity: 'high', message: 'Large reported production change; review source reconciliation.' }],
  } };
  const august = a.computeSeasonality(['well']).months[2026][8];
  assert.equal(august.status, 'unverified');
  assert.equal(august.reportedTotal, 10);
  assert.equal(august.value, null);
  assert.ok(august.warnings.some((message) => /Large reported production change/.test(message)));
});

test('matching source reconciliation preserves a genuine decline or measured zero despite a quality warning', () => {
  for (const amount of [10, 0]) {
    const a = setup({
      well: { __groups: [0], '2026-07': 100, '2026-08': amount },
      __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
    }, [asset('well', 'source')]);
    a.state.manifest.data_quality = { date_warnings: {
      '2026-08-31': [{ source_id: 'source', stream: 'Oil', severity: 'high', message: 'Large reported production change; review source reconciliation.' }],
    } };
    a.state.manifest.source_reconciliation = [{ source_id: 'source', stream: 'Oil', period: '2026-08',
      units: 'm3/d', source_unit_total: amount * 1000 / 6.28981077 }];
    const august = a.computeSeasonality(['well']).months[2026][8];
    assert.equal(august.status, 'complete');
    assert.equal(august.reportedTotal, amount);
    assert.equal(august.value, amount);
    assert.ok(august.warnings.some((message) => /Large reported production change/.test(message)));
  }
});

test('an unreconciled measured zero stays visible as zero rather than becoming a missing observation', () => {
  const a = setup({
    well: { __groups: [0], '2026-07': 100, '2026-08': 0 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
  }, [asset('well', 'source')]);
  a.state.manifest.data_quality = { date_warnings: {
    '2026-08-31': [{ source_id: 'source', stream: 'Oil', severity: 'high', message: 'Treat this month as incomplete until source reconciliation passes.' }],
  } };
  const august = a.computeSeasonality(['well']).months[2026][8];
  assert.equal(august.status, 'unverified');
  assert.equal(august.reportedTotal, 0);
  assert.equal(august.value, null);
  assert.equal(august.observedAssets, 1);
});

test('reconciliation must match the warned source, stream and reporting month', () => {
  for (const mismatch of [{ source_id: 'other-source' }, { stream: 'Condensate' }, { period: '2026-07' }]) {
    const a = setup({
      well: { __groups: [0], '2026-07': 100, '2026-08': 10 },
      __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
    }, [asset('well', 'source')]);
    a.state.manifest.data_quality = { date_warnings: {
      '2026-08-31': [{ source_id: 'source', stream: 'Oil', severity: 'high', message: 'Source coverage requires review.' }],
    } };
    a.state.manifest.source_reconciliation = [{ source_id: 'source', stream: 'Oil', period: '2026-08',
      units: 'm3/d', source_unit_total: 10, ...mismatch }];
    const august = a.computeSeasonality(['well']).months[2026][8];
    assert.equal(august.status, 'unverified');
    assert.equal(august.reportedTotal, 10);
    assert.equal(august.value, null);
  }
});

test('an unselected source warning does not downgrade a selected source that has reported', () => {
  const a = setup(mixedIndex(), [asset('early', 'early-source')]);
  a.state.manifest.data_quality = { date_warnings: {
    '2026-08-31': [{ source_id: 'late-source', stream: 'Oil', severity: 'high', message: 'Unselected source requires review.' }],
  } };
  const august = a.computeSeasonality(['early']).months[2026][8];
  assert.equal(august.status, 'complete');
  assert.equal(august.value, 20);
  assert.equal(august.warnings.length, 0);
});

test('legacy numeric history remains available but cannot claim verified reporting coverage', () => {
  const a = setup({ well: { '2026-07': 100, '2026-08': 0 } }, [asset('well', 'source')]);
  const data = a.computeSeasonality(['well']);
  assert.equal(data.partialHistory, true);
  assert.equal(data.months[2026][7].status, 'unverified');
  assert.equal(data.months[2026][7].reportedTotal, 100);
  assert.equal(data.months[2026][7].value, null);
  assert.equal(data.months[2026][8].status, 'unverified');
  assert.equal(data.months[2026][8].reportedTotal, 0);
});

test('local fallback observations are deduplicated by asset, date, source and stream without dropping another stream', () => {
  const a = setup({
    plant: { __groups: [0, 1], __month_groups: { '2026-06': [0, 1] }, '2026-06': 25 },
    __reporting: { schema_version: 1, groups: [
      group('source', 'Oil', ['2026-06', '2026-07']),
      group('source', 'Condensate', ['2026-06', '2026-07']),
    ] },
  }, [asset('plant', 'source')]);
  const oil = { asset_id: 'plant', date: '2026-07-31', source_id: 'source', stream: 'Oil', scenario: 'actual', volume_kbbl_d: 20 };
  const condensate = { ...oil, stream: 'Condensate', volume_kbbl_d: 5 };
  a.state.baseRecords = [oil];
  a.state.dateRecordCache.set('2026-07-31', [oil, condensate, { ...oil, scenario: 'forecast', volume_kbbl_d: 999 }]);
  const july = a.computeSeasonality(['plant']).months[2026][7];
  assert.equal(july.reportedTotal, 25);
  assert.equal(july.status, 'complete');
  assert.equal(july.value, 25);
});

test('an index value is not counted again through loaded monthly fallback records', () => {
  const a = setup({
    well: { __groups: [0], '2026-07': 100 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07'])] },
  }, [asset('well', 'source')]);
  const row = { asset_id: 'well', date: '2026-07-31', source_id: 'source', stream: 'Oil', scenario: 'actual', volume_kbbl_d: 100 };
  a.state.baseRecords = [row];
  a.state.dateRecordCache.set('2026-07-31', [row]);
  const july = a.computeSeasonality(['well']).months[2026][7];
  assert.equal(july.reportedTotal, 100);
  assert.equal(july.value, 100);
});

test('null amounts do not manufacture reported zeros', () => {
  const a = setup({
    well: { __groups: [0], '2026-07': null, '2026-08': 0 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2026-07', '2026-08'])] },
  }, [asset('well', 'source')]);
  const data = a.computeSeasonality(['well']);
  assert.equal(data.months[2026][7].status, 'missing');
  assert.equal(data.months[2026][7].reportedTotal, null);
  assert.equal(data.months[2026][7].value, null);
  assert.equal(data.months[2026][8].value, 0);
});

test('older-only asset history does not mislabel the old year as the current dataset year', () => {
  const a = setup({
    stopped: { __groups: [0], '2025-07': 100 },
    __reporting: { schema_version: 1, groups: [group('source', 'Oil', ['2025-07', '2026-07', '2026-08'])] },
  }, [asset('stopped', 'source')]);
  a.state.manifest.latest_actual_date = '2026-08-31';
  const data = a.computeSeasonality(['stopped']);
  assert.equal(data.currentYear, 2026);
  assert.equal(data.months[2026][8].status, 'missing');
  assert.equal(data.months[2026][8].reportedTotal, null);
  assert.equal(data.months[2025][7].value, 100);
});

function timelineApp(selectedSources) {
  const a = app();
  a.state.dates = ['2026-07-31', '2026-08-31'];
  a.state.selectedDate = '2026-08-31';
  selectedSources.forEach((source) => a.state.selectedSources.add(source));
  a.state.selectedStreams.add('Oil');
  a.state.manifest = {
    monthly_record_files: { '2026-07-31': 'july.json', '2026-08-31': 'august.json' },
    source_coverage: [
      { source_id: 'late-source', stream: 'Oil', scenario: 'actual', first_date: '2026-07-31', last_date: '2026-07-31' },
      { source_id: 'early-source', stream: 'Oil', scenario: 'actual', first_date: '2026-07-31', last_date: '2026-08-31' },
    ],
    date_filter_totals: {
      '2026-07-31': [
        { source_id: 'late-source', stream: 'Oil', scenario: 'actual', location_confidence: 'exact', kbbl_d: 100 },
        { source_id: 'early-source', stream: 'Oil', scenario: 'actual', location_confidence: 'exact', kbbl_d: 20 },
      ],
      '2026-08-31': [{ source_id: 'early-source', stream: 'Oil', scenario: 'actual', location_confidence: 'exact', kbbl_d: 20 }],
    },
  };
  a.els.timelineLabel = { textContent: '' };
  a.els.timelineBars = { innerHTML: '', querySelectorAll: () => [] };
  return a;
}

function timelineButton(a, date) {
  return a.els.timelineBars.innerHTML.match(/<button\b[^>]*>/g).find((button) => button.includes(`data-date="${date}"`));
}

test('timeline marks a mixed-source subtotal as partial instead of an ordinary low-production bar', () => {
  const a = timelineApp(['late-source', 'early-source']);
  a.renderTimeline();
  const august = timelineButton(a, '2026-08-31');
  assert.match(august, /class="[^"]*\bpartial\b/);
  assert.match(august, /partial|incomplete/i);
});

test('the timeline retains a suspicious source amount as a labeled subtotal instead of a solid collapse', () => {
  const a = timelineApp(['early-source']);
  a.state.manifest.date_filter_totals['2026-08-31'][0].kbbl_d = 0.001;
  a.state.manifest.data_quality = { date_warnings: {
    '2026-08-31': [{ source_id: 'early-source', stream: 'Oil', severity: 'high', message: 'Treat this month as incomplete until source reconciliation passes.' }],
  } };
  a.renderTimeline();
  assert.equal(a.state.timelineCache.get('2026-08-31'), 0.001);
  assert.equal(a.state.timelineReportingCache.get('2026-08-31').status, 'unverified');
  const august = timelineButton(a, '2026-08-31');
  assert.match(august, /class="[^"]*\bpartial\b/);
  assert.match(august, /reported subtotal/);
  assert.doesNotMatch(august, /\b0(?:\.0+)? kbbl\/d\b/);
});

test('a timeline month lacking the selected source is missing rather than a measured zero', () => {
  const a = timelineApp(['late-source']);
  a.renderTimeline();
  const august = timelineButton(a, '2026-08-31');
  assert.match(august, /class="[^"]*\bmissing\b/);
  assert.match(august, /not reported|unavailable|awaiting|incomplete/i);
  assert.doesNotMatch(august, /\b0(?:\.0+)? kbbl\/d\b/);
});

function detailApp(id, records = []) {
  const a = app();
  const selected = asset(id, 'source');
  const other = asset('other', 'source');
  a.state.selectedDate = '2026-08-31';
  a.state.selectedAssetId = id;
  a.state.assetById.set(id, selected);
  a.state.assetById.set('other', other);
  a.state.selectedSources.add('source');
  a.state.selectedStreams.add('Oil');
  a.state.baseRecordsByDate.set('2026-08-31', records);
  for (const name of ['detailTitle', 'detailSubtitle', 'detailVolume', 'detailSource', 'detailStatus']) a.els[name] = { textContent: '' };
  a.els.streamBreakdown = { innerHTML: '' };
  const aggregated = { byAsset: new Map([['other', { asset: other, kbbl: 999, streams: new Map([['Oil', 999]]),
    sources: new Set(['source']), scenarios: new Set(['actual']) }]]) };
  return { a, aggregated };
}

test('an explicitly selected asset with missing observations stays selected instead of switching to the largest producer', () => {
  const { a, aggregated } = detailApp('missing');
  a.renderDetails(aggregated);
  assert.equal(a.els.detailTitle.textContent, 'missing');
  assert.equal(a.els.detailVolume.textContent, '--');
  assert.match(a.els.detailStatus.textContent, /Unavailable|missing/i);
  assert.match(a.els.streamBreakdown.innerHTML, /unavailable/i);
  assert.doesNotMatch(a.els.detailVolume.textContent, /999/);
});

test('a selected asset with an explicit actual zero remains a measured-zero detail', () => {
  const zero = { asset_id: 'zero', date: '2026-08-31', source_id: 'source', stream: 'Oil', scenario: 'actual', volume_kbbl_d: 0 };
  const { a, aggregated } = detailApp('zero', [zero]);
  a.renderDetails(aggregated);
  assert.equal(a.els.detailTitle.textContent, 'zero');
  assert.match(a.els.detailVolume.textContent, /^0(?:\.0+)? kbbl\/d$/);
  assert.equal(a.els.detailStatus.textContent, 'actual');
  assert.match(a.els.streamBreakdown.innerHTML, /Oil/);
});

test('a source-wide zero does not invent a measured zero for a searched asset with no record', () => {
  const a = app();
  a.state.selectedDate = '2026-08-31';
  a.state.search = 'missing well';
  a.state.assetById.set('missing', { ...asset('missing', 'source'), display_name: 'Missing well' });
  a.state.assetById.set('zero', { ...asset('zero', 'source'), display_name: 'Other well' });
  a.state.selectedSources.add('source');
  a.state.selectedStreams.add('Oil');
  a.state.baseRecordsByDate.set('2026-08-31', [
    { asset_id: 'zero', date: '2026-08-31', source_id: 'source', stream: 'Oil', scenario: 'actual', volume_kbbl_d: 0 },
  ]);
  a.state.manifest = {
    source_coverage: [{ source_id: 'source', stream: 'Oil', scenario: 'actual', first_date: '2026-07-31', last_date: '2026-08-31' }],
    date_filter_totals: { '2026-08-31': [{ source_id: 'source', stream: 'Oil', scenario: 'actual', location_confidence: 'exact', kbbl_d: 0 }] },
  };
  const point = a.productionReportingForDate('2026-08-31', 0);
  assert.equal(point.status, 'missing');
  assert.equal(point.reportedTotal, null);
  assert.equal(point.value, null);
});

function chartMonth(year, month, status, amount) {
  return { date: `${year}-${String(month).padStart(2, '0')}-01`, status,
    value: status === 'complete' ? amount : null, reportedTotal: status === 'missing' ? null : amount,
    missingSources: [], expectedGroupsCount: 1, reportingGroupsCount: status === 'complete' ? 1 : 0,
    observedAssets: status === 'missing' ? 0 : 1, selectedAssetCount: 1,
    unavailableAssetsCount: status === 'missing' ? 1 : 0, warnings: [], note: '' };
}

function chartApp() {
  const strokes = [], fills = [];
  let currentPath = [];
  const ctx = {
    beginPath() { currentPath = []; },
    moveTo(x, y) { currentPath.push({ op: 'move', x, y }); },
    lineTo(x, y) { currentPath.push({ op: 'line', x, y }); },
    arc(x, y, radius) { currentPath.push({ op: 'arc', x, y, radius }); },
    closePath() { currentPath.push({ op: 'close' }); },
    stroke() { strokes.push({ color: this.strokeStyle, path: currentPath.map((point) => ({ ...point })) }); },
    fill() { fills.push({ color: this.fillStyle, path: currentPath.map((point) => ({ ...point })) }); },
    clearRect() {}, fillRect() {}, fillText() {}, save() {}, restore() {}, translate() {}, rotate() {},
    setLineDash() {},
  };
  const canvas = { width: 580, height: 240, style: {}, getContext: () => ctx };
  return { a: app({ seasonalityCanvas: canvas }), strokes, fills };
}

test('complete chart runs stop at missing and partial months while a real zero stays plotted', () => {
  const { a, strokes, fills } = chartApp();
  const months = { 2026: {
    1: chartMonth(2026, 1, 'complete', 100),
    2: chartMonth(2026, 2, 'missing', null),
    3: chartMonth(2026, 3, 'complete', 0),
    4: chartMonth(2026, 4, 'partial', 20),
    5: chartMonth(2026, 5, 'complete', 80),
    6: chartMonth(2026, 6, 'complete', 90),
  } };
  a.drawSeasonalityChart({ months, years: [2026], currentYear: 2026 }, 1);
  const redLine = strokes.find((stroke) => stroke.color === '#dc2626');
  assert.ok(redLine);
  assert.equal(redLine.path.filter((point) => point.op === 'move').length, 3);
  assert.equal(redLine.path.filter((point) => point.op === 'line').length, 1);
  assert.ok(fills.some((fill) => fill.color === '#dc2626' && fill.path.some((point) => point.op === 'arc' && point.y === 204)),
    'A complete measured zero must have a filled current-year point at the zero axis');
  assert.ok(strokes.some((stroke) => stroke.color === '#64748b' && stroke.path.some((point) => point.op === 'arc')),
    'A partial subtotal must have a separate hollow point');
});

test('historical envelope and prior-year paths do not span a month with missing observations', () => {
  const { a, strokes, fills } = chartApp();
  const months = {};
  for (const year of [2024, 2025, 2026]) {
    months[year] = {};
    for (let month = 1; month <= 4; month++) months[year][month] = chartMonth(year, month, 'complete', 80 + month);
  }
  months[2024][2] = chartMonth(2024, 2, 'missing', null);
  a.drawSeasonalityChart({ months, years: [2024, 2025, 2026], currentYear: 2026 }, 1);
  const envelopes = fills.filter((fill) => fill.color === 'rgba(156,163,175,0.28)');
  assert.equal(envelopes.length, 2, 'The historical range must split into separate January and March-April bands');
  const priorLine = strokes.find((stroke) => stroke.color === '#2563eb');
  assert.equal(priorLine.path.filter((point) => point.op === 'move').length, 2);
  assert.equal(priorLine.path.filter((point) => point.op === 'line').length, 1);
});

test('month details explain unavailable amounts and escape source names, reasons and warnings', () => {
  const a = app();
  const month = chartMonth(2026, 8, 'missing', null);
  month.missingSources = [{ source_id: '<img src=x>', stream: 'Oil & condensate', last_date: '2026-07-31', reason: '<script>alert(1)</script>' }];
  month.warnings = ['<svg onload=alert(1)>'];
  const html = a.renderSeasonalityDetails(month);
  assert.match(html, /Unavailable/);
  assert.match(html, /missing observations are not treated as zero/i);
  assert.match(html, /&lt;img/);
  assert.match(html, /&lt;script/);
  assert.match(html, /&lt;svg/);
  assert.doesNotMatch(html, /<img|<script|<svg/);
});
