"""Offline regressions for public-source parsing and alert state. Never sends mail."""
import unittest
import io
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import build_aeso_power_status as power
import check_alerts as alerts


class PublicSourceTests(unittest.TestCase):
    def setUp(self):
        retry_sleep = patch.object(power.time, 'sleep')
        retry_sleep.start()
        self.addCleanup(retry_sleep.stop)

    def test_missing_generation_is_not_zero(self):
        parsed = power.parse_csd('Plant (A1)*,100,,0\nOther (A2),100,0,0')
        self.assertIsNone(parsed['assets'][0]['tng_mw'])
        self.assertTrue(parsed['assets'][0]['net_to_grid'])
        self.assertEqual(parsed['assets'][1]['tng_mw'], 0)
        self.assertIsNone(power.to_num('NaN'))
        self.assertEqual(power.to_num('1,000'), 1000)

    def test_invalid_and_stale_power_reports_fail_before_publication(self):
        with patch.object(power, 'fetch_csd', return_value='<html>Service unavailable</html>'):
            with self.assertRaises(ValueError):
                power.build()
        with patch.object(power, 'fetch_csd', return_value='Last Update : Jan 01, 2020 12:00\nAlberta Internal Load (AIL),100\nPlant (A1),100,10,0'):
            with self.assertRaises(ValueError):
                power.build()

    def test_failed_fire_source_does_not_delete_known_fires(self):
        state = {'fires': {'AB-1': {}, 'BC-1': {}}, 'fires_baselined': True}
        alerts.check_fires([], {}, .25, state, {'radius_km':10}, [], {'AB'})
        self.assertNotIn('AB-1', state['fires'])
        self.assertIn('BC-1', state['fires'])

    def test_each_source_baselines_after_its_first_success(self):
        state = {}
        alerts.check_fires([], {}, .25, state, {'radius_km':10}, [], {'AB'})
        emitted = []
        grid, cell = alerts.build_grid([(55, -120, 'Asset')])
        fire = {'id':'BC-1', 'lat':55, 'lon':-120, 'source':'BC', 'status':'Out of Control'}
        alerts.check_fires([fire], grid, cell, state, {'radius_km':10}, emitted, {'BC'})
        self.assertEqual(emitted, [])

    def test_high_latitude_radius_spans_more_than_one_grid_cell(self):
        grid, cell = alerts.build_grid([(65, -110.8, 'Northern asset')])
        hit = alerts.nearest_asset(grid, cell, 65, -111.01, 10)
        self.assertIsNotNone(hit)
        self.assertLess(hit[0], 10)

    def test_same_power_observation_cannot_confirm_two_runs(self):
        now = datetime.now(timezone.utc)
        state = {'power_sites': {'Plant': {'status':'normal', 'runs_below':0, 'runs_above':0}}}
        data = {'observed_at':now.isoformat(), 'site_cogen':[{'site':'Plant','utilization':.1}]}
        cfg = {'down_threshold':.2, 'recover_threshold':.5, 'confirm_runs':2}
        emitted = []
        alerts.check_power(data, state, cfg, emitted)
        alerts.check_power(data, state, cfg, emitted)
        self.assertEqual(state['power_sites']['Plant']['runs_below'], 1)
        self.assertEqual(emitted, [])
        data['observed_at'] = (now - timedelta(hours=3)).isoformat()
        alerts.check_power(data, state, cfg, emitted)
        self.assertEqual(state['power_sites']['Plant']['runs_below'], 1)

    def test_zero_net_export_does_not_establish_site_power_loss(self):
        data = {'observed_at':datetime.now(timezone.utc).isoformat(), 'site_cogen':[{'site':'Plant','utilization':0,'net_to_grid':True}]}
        state = {}
        alerts.check_power(data, state, {'down_threshold':.2, 'recover_threshold':.5, 'confirm_runs':2}, [])
        self.assertEqual(state['power_sites'], {})

    def test_malformed_fire_row_does_not_mark_a_partial_source_successful(self):
        first = {'attributes': {'FIRE_NUMBER':'1', 'FIRE_STATUS':'Out of Control', 'LATITUDE':55, 'LONGITUDE':-120}}
        with patch.object(alerts, 'fetch_json', side_effect=[{'features':[first, {'attributes':{}}]}, {'features':[]} ]):
            fires, successful = alerts.fetch_fires()
        self.assertEqual(successful, {'BC'})
        self.assertEqual(fires, [])
        state = {'fires': {'AB-1': {'status':'Out of Control'}, 'BC-2': {}}, 'fires_baselined': True}
        alerts.check_fires(fires, {}, .25, state, {'radius_km':10}, [], successful)
        self.assertIn('AB-1', state['fires'])
        self.assertNotIn('BC-2', state['fires'])

    def test_active_fire_with_unknown_coordinates_is_not_retired(self):
        for latitude in [None, 'unavailable', 'NaN', 1000]:
            data = {'features':[{'attributes':{'FIRE_NUMBER':'1', 'FIRE_STATUS':'Out of Control', 'LATITUDE':latitude, 'LONGITUDE':-120}}]}
            fires = alerts.normalize_fires(data, 'AB', 'Alberta', 'AREA_ESTIMATE')
            self.assertIsNone(fires[0]['lat'])
            state = {'fires':{'AB-1':{'status':'Out of Control'}}, 'fires_baselined':True}
            emitted = []
            alerts.check_fires(fires, {}, .25, state, {'radius_km':10}, emitted, {'AB'})
            self.assertIn('AB-1', state['fires'])
            self.assertEqual(emitted, [])

    def test_nested_transfer_limit_and_invalid_fire_schema_are_rejected(self):
        for payload in [{'features':[], 'properties':{'exceededTransferLimit':True}}, [], {'features':[]}]:
            with patch.object(alerts.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
                if payload == {'features':[]}:
                    self.assertEqual(alerts.fetch_json('https://example.invalid/fire'), payload)
                else:
                    with self.assertRaises(ValueError):
                        alerts.fetch_json('https://example.invalid/fire')

    def test_missing_power_reading_breaks_a_confirmation_streak(self):
        now = datetime.now(timezone.utc)
        cfg = {'down_threshold':.2, 'recover_threshold':.5, 'confirm_runs':2}
        state = {'power_observation':(now-timedelta(minutes=30)).isoformat(),
                 'power_sites':{'Plant':{'status':'normal','runs_below':0,'runs_above':0}}}
        site = {'site':'Plant','operator':'Test','aeso_name':'Unit','tng_mw':10,'mc_mw':100,'utilization':.1}
        emitted = []
        for minute, rows in [(-20,[site]), (-10,[{**site,'complete':False}]), (0,[site])]:
            alerts.check_power({'observed_at':(now+timedelta(minutes=minute)).isoformat(),'site_cogen':rows}, state, cfg, emitted)
        self.assertEqual(state['power_sites']['Plant']['runs_below'], 1)
        self.assertEqual(emitted, [])
        alerts.check_power({'observed_at':(now+timedelta(seconds=1)).isoformat(),'site_cogen':[]}, state, cfg, emitted)
        self.assertEqual(state['power_sites']['Plant']['runs_below'], 0)

    def test_missing_observation_time_and_reordered_or_equivalent_timestamps_do_not_confirm(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        cfg = {'down_threshold':.2, 'recover_threshold':.5, 'confirm_runs':2}
        state = {'power_observation':now.isoformat(),'power_sites':{'Plant':{'status':'normal','runs_below':1,'runs_above':0}}}
        site = {'site':'Plant','utilization':.1}
        emitted = []
        for stamp in [(now-timedelta(minutes=5)).isoformat(), now.isoformat().replace('+00:00','Z'), now.astimezone(timezone(timedelta(hours=-6))).isoformat()]:
            alerts.check_power({'observed_at':stamp,'site_cogen':[site]}, state, cfg, emitted)
        alerts.check_power({'generated_at':now.isoformat(),'site_cogen':[site]}, state, cfg, emitted)
        self.assertEqual(state['power_sites']['Plant']['runs_below'], 1)
        self.assertEqual(emitted, [])

    def test_distinct_complete_observations_confirm_down_and_recovery_once(self):
        now = datetime.now(timezone.utc)
        cfg = {'down_threshold':.2, 'recover_threshold':.5, 'confirm_runs':2}
        state = {'power_observation':(now-timedelta(minutes=50)).isoformat(),
                 'power_sites':{'Plant':{'status':'normal','runs_below':0,'runs_above':0}}}
        emitted = []
        for minute, utilization in [(-40,.1), (-30,.1), (-20,.8), (-10,.8), (0,.8)]:
            site = {'site':'Plant','operator':'Test','aeso_name':'Unit','tng_mw':utilization*100,'mc_mw':100,'utilization':utilization,'complete':True}
            alerts.check_power({'observed_at':(now+timedelta(minutes=minute)).isoformat(),'site_cogen':[site]}, state, cfg, emitted)
        self.assertEqual([a['kind'] for a in emitted], ['power-down','power-recovered'])
        self.assertEqual(state['power_sites']['Plant']['status'], 'normal')

    def test_new_power_site_baselines_and_invalid_utilization_resets_pending_counts(self):
        now = datetime.now(timezone.utc)
        cfg = {'down_threshold':.2, 'recover_threshold':.5, 'confirm_runs':2}
        state = {'power_observation':(now-timedelta(minutes=10)).isoformat(),
                 'power_sites':{'Existing':{'status':'normal','runs_below':1,'runs_above':0}}}
        emitted = []
        alerts.check_power({'observed_at':now.isoformat(),'site_cogen':[{'site':'New','utilization':.1},{'site':'Existing','utilization':float('nan')}]}, state, cfg, emitted)
        self.assertEqual(state['power_sites']['New']['status'], 'reduced')
        self.assertEqual(state['power_sites']['New']['runs_below'], 0)
        self.assertEqual(state['power_sites']['Existing']['runs_below'], 0)
        self.assertEqual(emitted, [])

    def test_aeso_future_time_fails_and_missing_site_units_remain_explicit(self):
        # Freeze outside the autumn DST fold: the source publishes a local
        # minute without an offset, so an ambiguous wall clock is unsuitable
        # for a deterministic future-time fixture.
        now = datetime(2026, 9, 10, 18, 0, tzinfo=timezone.utc)
        local = now.astimezone(power.ZoneInfo('America/Edmonton'))
        prefix = (f'Last Update : {local:%b %d, %Y %H:%M}\nAlberta Internal Load (AIL),100\n'
                  'Alberta Total Net Generation,100\nNet Actual Interchange,0\n'
                  'Net-To-Grid Generation,100\nDispatched Contingency Reserve (DCR),0\nTOTAL,100,100,0\n')
        site = {'codes':['A1','A2'],'site':'Missing unit','operator':'Test','lat':55,'lon':-120}
        with patch.object(power, 'datetime', wraps=datetime) as clock, patch.object(power, 'SITE_COGEN_SITES', [site]), patch.object(power, 'fetch_csd', return_value=prefix+'Other (B1),100,30,0'):
            clock.now.return_value = now
            result = power.build()
        self.assertEqual(len(result['site_cogen']), 1)
        row = result['site_cogen'][0]
        self.assertFalse(row['complete'])
        self.assertIsNone(row['utilization'])
        self.assertIsNone(row['tng_mw'])
        self.assertEqual(row['aeso_code'], 'A1+A2')
        future = f'Last Update : {local+timedelta(minutes=30):%b %d, %Y %H:%M}\nAlberta Internal Load (AIL),100\nOther (B1),100,30,0'
        with patch.object(power, 'datetime', wraps=datetime) as clock, patch.object(power, 'fetch_csd', return_value=future):
            clock.now.return_value = now
            with self.assertRaises(ValueError):
                power.build()

    def test_aeso_timestamp_accepts_quoted_and_unquoted_csv_date(self):
        for text in ['Last Update : Sep 10, 2026 12:00', '"Last Update : Sep 10, 2026 12:00",,,']:
            self.assertEqual(power.parse_csd(text)['last_update'], 'Sep 10, 2026 12:00')


if __name__ == '__main__':
    unittest.main()
