"""End-to-end source chronology and actual data-driven changes."""
from fastapi.testclient import TestClient
from backend.app.main import create_app


def test_exercise_evolves_without_future_reports_or_spatial_duplication():
    client = TestClient(create_app())
    client.post('/api/scenario/start',json={'mode':'scenario','seed':42,'duration_hours':72})
    scores, reports = [], 0
    for _ in range(72):
        response = client.post('/api/scenario/step')
        assert response.status_code==200
        step = response.json()
        ids = []
        for record in step['records']:
            assert record['available_at'] <= step['current_time']
            assert record['event_time'] <= step['current_time']
            if record['kind']=='weather': ids += record['payload']['settlement_ids']
            if record['kind']=='report': reports += 1
        assert len(ids)==len(set(ids))==16
        snapshot = client.get('/api/scenario/snapshot').json()
        assert snapshot['mode']=='simulated'
        scores.append(max(c['score'] or 0 for c in snapshot['assessments']))
    assert reports > 0 and max(scores) > scores[0]
    assert snapshot['run']['is_exhausted']
    assert client.post('/api/scenario/step').status_code==400
    client.post('/api/scenario/start',json={'mode':'replay'})
    assert all(not c['reports']['records'] for c in client.get('/api/scenario/snapshot').json()['assessments'])
    client.post('/api/scenario/stop')
