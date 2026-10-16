from copy import deepcopy
from datetime import datetime, timedelta, timezone

import httpx
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.live_weather import FIELDS, LiveWeatherService
from engine.clock import ScenarioClock

NOW = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)


def fixture(service):
    result = []
    for i, f in enumerate(service.features):
        lon, lat = f['geometry']['coordinates']
        result.append({'location_id': i, 'latitude': lat, 'longitude': lon, 'utc_offset_seconds': 0,
            'current_units': FIELDS.copy(), 'current': {'time': NOW.isoformat(), 'interval': 900,
            'temperature_2m': 27.5, 'relative_humidity_2m': 70, 'precipitation': .3 if i < 6 else 0,
            'rain': .3 if i < 6 else 0, 'showers': 0, 'weather_code': 61 if i < 6 else 0,
            'cloud_cover': 80 if i < 6 else 10, 'wind_speed_10m': 4.2, 'is_day': 1}})
    return result


def service(tmp_path):
    s = LiveWeatherService(clock=ScenarioClock(NOW), cache_path=tmp_path/'live.json')
    s.fetcher = lambda _: fixture(s)
    return s


def test_six_rainy_settlements_and_no_cross_location_mix(tmp_path):
    s = service(tmp_path)
    view = s.get()
    assert view['counts']['current'] == 16
    assert view['raining_count'] == 6
    assert view['settlements'][0]['condition'] == 'Light rain'
    assert view['settlements'][8]['condition'] == 'Sunny'
    assert view['settlements'][8]['values']['rain'] == 0
    assert view['settlements'][0]['interval_seconds'] == 900  # Never labeled mm/h.


def test_hourly_history_filters_future_and_keeps_missing_values(tmp_path):
    s = service(tmp_path); payload = fixture(s)
    for item in payload:
        item['hourly_units'] = {'precipitation':'mm'}
        item['hourly'] = {'time':[(NOW-timedelta(hours=1)).isoformat(), NOW.isoformat(), (NOW+timedelta(hours=1)).isoformat()],
                          'precipitation':[None, 2, 999]}
    s.fetcher = lambda _:payload
    h = s.get()['settlements'][0]['hourly_history']
    assert [r['precipitation_mm'] for r in h]==[None, 2]
    payload[0]['hourly_units']['precipitation']='inch'
    s.clock.advance(timedelta(minutes=11))
    assert s.get()['error']


def test_missing_is_unknown_not_dry_and_night_not_sunny(tmp_path):
    s = service(tmp_path); data = fixture(s)
    data[0]['current']['rain'] = None
    data[6]['current']['is_day'] = 0
    s.fetcher = lambda _: data
    view = s.get()
    assert view['settlements'][0]['rain_status'] == 'unknown'
    assert 'rain' in view['settlements'][0]['missing_fields']
    assert view['settlements'][6]['condition'] == 'Clear sky'


def test_cache_refresh_backoff_and_stale_outage(tmp_path):
    s = service(tmp_path); calls = []
    def fetch(_):
        calls.append(1)
        if len(calls) > 1:
            raise httpx.ConnectError('offline')
        return fixture(s)
    s.fetcher = fetch
    original = s.get(); s.get()
    assert len(calls) == 1
    s.clock.advance(timedelta(minutes=11))
    stale = s.get(); s.get()
    assert len(calls) == 2
    assert stale['counts']['stale'] == 16
    assert stale['raining_count'] == 0
    assert stale['retrieved_at'] == original['retrieved_at']
    assert stale['settlements'][0]['values']['rain'] == .3
    assert stale['error']
    restarted = LiveWeatherService(clock=s.clock, fetcher=fetch, cache_path=s.cache_path)
    assert restarted.get()['counts']['stale'] == 16


def test_no_cache_outage_retains_all_locations_as_unknown(tmp_path):
    s = service(tmp_path)
    def fail(_): raise httpx.ConnectError('offline')
    s.fetcher = fail
    view = s.get()
    assert view['counts']['unavailable'] == 16
    assert all(r['values']['temperature_2m'] is None for r in view['settlements'])
    assert view['retrieved_at'] is None


def test_invalid_units_order_and_future_current_rejected(tmp_path):
    for field in ['units', 'order', 'future', 'incomplete']:
        s = service(tmp_path / field); data = fixture(s)
        if field == 'units': data[0]['current_units']['rain'] = 'inch'
        if field == 'order': data[0]['location_id'] = 7
        if field == 'future': data[0]['current']['time'] = (NOW + timedelta(days=1)).isoformat()
        if field == 'incomplete': data = data[:-1]
        s.fetcher = lambda _: data
        assert s.get()['counts']['unavailable'] == 16


def test_old_provider_timestamp_not_freshened_by_new_download(tmp_path):
    s = service(tmp_path); s.clock.advance(timedelta(hours=2))
    assert s.get()['counts']['stale'] == 16


def test_live_endpoint_is_independent_of_scenario_and_rejects_legacy_steps(tmp_path):
    app = create_app(); app.state.live_weather = service(tmp_path)
    c = TestClient(app)
    c.post('/api/scenario/start', json={'mode': 'scenario', 'duration_hours': 6})
    before = c.get('/api/scenario/status').json()
    assert c.get('/api/live/conditions').json()['counts']['current'] == 16
    assert c.get('/api/scenario/status').json() == before
    assert c.post('/api/scenario/start', json={'mode': 'live'}).status_code == 409
    c.post('/api/scenario/stop')
    # Protect even a legacy adapter inserted by an older caller.
    from backend.app.api.scenario import get_shared_run_state
    from engine.ingest.source import LiveWeatherAdapter
    import json
    from engine.config import ROOT
    get_shared_run_state().start(LiveWeatherAdapter(json.loads((ROOT/'data/processed/weather_live.json').read_text())))
    assert c.post('/api/scenario/step').status_code == 409
    assert c.post('/api/scenario/reset').status_code == 409
    c.post('/api/scenario/stop')
