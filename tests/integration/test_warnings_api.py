"""Corrected snapshot contracts; replaces legacy tests that required fake alerts."""
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.services.live_weather import LiveWeatherService


def test_unknown_live_is_not_fabricated_and_override_is_retired(tmp_path):
    app = create_app()
    def outage(_): raise OSError('offline')
    app.state.live_weather = LiveWeatherService(fetcher=outage, cache_path=tmp_path/'missing.json')
    client = TestClient(app)
    data = client.get('/api/warnings/summary').json()
    assert data['mode']=='live' and len(data['assessments'])==16
    assert all(c['severity']=='unknown' and not c['affected'] for c in data['assessments'])
    ident = data['assessments'][0]['settlement_id']
    card = client.get(f'/api/warnings/{ident}/card').json()
    assert card['rainfall']['rain_mm']['1'] is None
    assert card['reports']['message']=='No ground reports received'
    assert client.get('/api/warnings/missing/card').status_code==404
    assert client.get('/api/warnings/roads').status_code==409
    assert client.post('/api/warnings/reevaluate',json={'rain_1h_override':99}).status_code==410


def test_historical_grid_mapping_snapshot_agreement_and_reset():
    client = TestClient(create_app())
    client.post('/api/scenario/stop')
    assert client.get('/api/scenario/snapshot').status_code==409
    client.post('/api/scenario/start',json={'mode':'replay'})
    for _ in range(6):
        step = client.post('/api/scenario/step').json()
        assert len(step['records'])==16
        assert all(r['event_time']==step['current_time'] for r in step['records'])
        assert all(r['source']=='replay' and r['replayed_at'] for r in step['records'])
    snapshot = client.get('/api/scenario/snapshot').json()
    cards = snapshot['assessments']
    assert len(cards)==16 and all(c['rainfall']['coverage_hours']['6']==6 for c in cards)
    assert len({tuple(c['rainfall']['grid']) for c in cards})==3
    assert cards==client.get('/api/warnings/settlements?mode=exercise').json()
    assert cards==client.get('/api/scenario/snapshot').json()['assessments']
    ident = cards[0]['settlement_id']
    assert cards[0]==client.get(f'/api/warnings/{ident}/card?mode=exercise').json()
    assert all(not c['reports']['records'] for c in cards)
    client.post('/api/scenario/reset')
    reset = client.get('/api/scenario/snapshot').json()
    assert reset['run']['run_id'] != snapshot['run']['run_id']
    assert all(c['severity']=='unknown' and c['previous_rank'] is None for c in reset['assessments'])
    client.post('/api/scenario/stop')
