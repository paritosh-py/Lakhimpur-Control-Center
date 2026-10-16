from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import uuid

import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.services.live_weather import LiveWeatherService
from engine.clock import ScenarioClock


@pytest.fixture
def setup(tmp_path):
    clock=ScenarioClock(datetime(2026,10,11,tzinfo=timezone.utc))
    app=create_app(clock=clock,operations_path=tmp_path/'operations.sqlite3')
    def offline(_): raise OSError('offline')
    app.state.live_weather=LiveWeatherService(clock=clock,cache_path=tmp_path/'none.json',fetcher=offline)
    client=TestClient(app)
    client.post('/api/scenario/stop')
    places=[s['id'] for s in app.state.assessments.settlements]
    yield client,app,places
    client.post('/api/scenario/stop')


def team(client,place,context='live',name='Team A',capabilities=None,available=True):
    response=client.post('/api/teams',params={'context':context},json={'name':name,'location':place,'members':4,'capabilities':capabilities or ['assessment','rescue'],'available':available})
    assert response.status_code==200,response.text
    return response.json()


def dispatch(client,t,place,context='live',request_id=None,requirement='assessment'):
    return client.post('/api/teams/assignments',params={'context':context},json={'team_id':t['id'],'settlement_id':place,'task':'Assess water level and report needs','requirement':requirement,'request_id':request_id or uuid.uuid4().hex})


def update(client,t,task,status=None,note='',version=None,request_id=None):
    return client.post('/api/teams/portal/'+task['id']+'/updates',headers={'Authorization':'Bearer '+t['token']},json={'status':status,'note':note,'version':version or task['version'],'request_id':request_id or uuid.uuid4().hex})


def test_assignment_to_team_app_lifecycle_messages_location_and_release(setup):
    client,app,places=setup
    t=team(client,places[0]); task=dispatch(client,t,places[1]).json()
    portal=client.get('/api/teams/portal',headers={'Authorization':'Bearer '+t['token']}).json()
    assert portal['assignments'][0]['id']==task['id']
    assert 'token' not in portal['team']
    assert task['route_status']=='unverified' and task['eta_minutes'] is None
    for status in ('accepted','en_route','arrived'):
        response=update(client,t,task,status)
        assert response.status_code==200,response.text
        task=response.json()
    task=update(client,t,task,note='Assessment complete; no rescue requested.').json()
    assert task['events'][-1]['note'].startswith('Assessment complete')
    task=update(client,t,task,'completed').json()
    assert task['status']=='completed'
    state=client.get('/api/teams/state').json()
    assert state['teams'][0]['location']==places[1]
    assert dispatch(client,t,places[0]).status_code==200
    assert update(client,t,task,note='late edit').status_code==409


def test_double_booking_race_and_dispatch_retry(setup):
    client,app,places=setup
    t=team(client,places[0]); key=uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:dispatch(client,t,places[1]),range(2)))
    assert sorted(r.status_code for r in results)==[200,409]
    other=team(client,places[0],name='Team B')
    first=dispatch(client,other,places[1],request_id=key)
    retry=dispatch(client,other,places[1],request_id=key)
    assert first.json()['id']==retry.json()['id']
    assert dispatch(client,other,places[0],request_id=key).status_code==409


def test_capabilities_availability_duplicate_names_and_bad_locations(setup):
    client,app,places=setup
    t=team(client,places[0],available=False)
    assert dispatch(client,t,places[1]).status_code==409
    boat=team(client,places[0],name='Boat crew',capabilities=['boat'])
    assert dispatch(client,boat,places[1]).status_code==409
    payload={'name':'team a','location':places[0],'members':4,'capabilities':['assessment']}
    assert client.post('/api/teams',json=payload).status_code==409
    assert client.put('/api/teams/'+t['id'],json={'name':'Team A','location':places[1],'members':5,'capabilities':['assessment'],'available':True}).status_code==200
    assert dispatch(client,t,places[0]).status_code==200
    payload.update(name='Team C',location='not-a-settlement')
    assert client.post('/api/teams',json=payload).status_code==422
    payload.update(name='  ',location=places[0])
    assert client.post('/api/teams',json=payload).status_code==422


def test_state_machine_blocked_reservation_versions_and_token_isolation(setup):
    client,app,places=setup
    t=team(client,places[0]); other=team(client,places[0],name='Team B')
    task=dispatch(client,t,places[1]).json()
    assert update(client,t,task,'completed').status_code==409
    assert update(client,other,task,'accepted').status_code==404
    task=update(client,t,task,'accepted').json()
    assert update(client,t,task,'en_route',version=1).status_code==409
    assert update(client,t,task,'blocked').status_code==422
    task=update(client,t,task,'blocked',note='Water over bridge near Kadam; awaiting instructions.').json()
    assert dispatch(client,t,places[0]).status_code==409
    assert client.put('/api/teams/'+t['id'],json={'name':'Team A','members':5,'location':places[0],'capabilities':['rescue']}).status_code==409
    task=update(client,t,task,'en_route',note='Control center instructed us to resume.').json()
    assert task['status']=='en_route'
    cancel=client.post('/api/teams/assignments/'+task['id']+'/cancel',json={'status':'cancelled','note':'cancel','version':task['version'],'request_id':uuid.uuid4().hex})
    assert cancel.status_code==409
    assert client.get('/api/teams/portal').status_code==401
    assert client.get('/api/teams/portal',headers={'Authorization':'Bearer wrong'}).status_code==404


def test_cancellation_and_idempotent_updates(setup):
    client,app,places=setup
    t=team(client,places[0]); task=dispatch(client,t,places[1]).json(); key=uuid.uuid4().hex
    first=update(client,t,task,'accepted',request_id=key).json()
    again=update(client,t,task,'accepted',request_id=key).json()
    assert first['version']==again['version']==2 and len(again['events'])==2
    assert update(client,t,first,'cancelled').status_code==403
    result=client.post('/api/teams/assignments/'+task['id']+'/cancel',json={'status':'cancelled','note':'Not required now','version':2,'request_id':uuid.uuid4().hex})
    assert result.status_code==200
    assert dispatch(client,t,places[0]).status_code==200


def test_exercise_live_isolation_reset_and_persistence(setup):
    client,app,places=setup
    live=team(client,places[0])
    run=client.post('/api/scenario/start',json={'mode':'scenario','seed':42,'duration_hours':6}).json()['run_id']
    assert client.post('/api/teams',params={'context':run},json={'name':'Team A','location':places[0],'members':4,'capabilities':['rescue']}).status_code==409
    client.post('/api/scenario/step')
    simulated=team(client,places[0],run)
    assert dispatch(client,live,places[1],run).status_code==404
    task=dispatch(client,simulated,places[1],run).json()
    assert task['source']=='simulated' and task['event_time'].startswith('2024-')
    assert task['recorded_at'].startswith('2026-')
    assert not client.get('/api/teams/state').json()['assignments']
    restarted=TestClient(create_app(operations_path=app.state.teams.path))
    assert restarted.get('/api/teams/state',params={'context':run}).json()['assignments'][0]['id']==task['id']
    new=client.post('/api/scenario/reset').json()['run_id']
    assert not client.get('/api/teams/state',params={'context':new}).json()['teams']
    assert update(client,simulated,task,'accepted').status_code==409
    archived=client.get('/api/teams/portal',headers={'Authorization':'Bearer '+simulated['token']}).json()
    assert not archived['context']['writable'] and len(archived['assignments'])==1


def test_weather_progress_does_not_silently_reassign_committed_team(setup):
    client,app,places=setup
    run=client.post('/api/scenario/start',json={'mode':'scenario','seed':42,'duration_hours':72}).json()['run_id']
    client.post('/api/scenario/step')
    t=team(client,places[0],run); original=dispatch(client,t,places[1],run).json()
    accepted=update(client,t,original,'accepted').json()
    committed=update(client,t,accepted,'en_route').json()
    for _ in range(12): client.post('/api/scenario/step')
    current=client.get('/api/teams/state',params={'context':run}).json()['assignments'][0]
    assert current['id']==committed['id'] and current['status']=='en_route'
    assert current['settlement_id']==places[1] and current['evidence']==original['evidence']
