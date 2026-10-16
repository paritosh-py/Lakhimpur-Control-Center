"""Read-only views of the same assessment snapshot used by the command map."""
from typing import Literal
from fastapi import APIRouter, HTTPException, Request
from backend.app.api.scenario import get_shared_run_state, _run_lock

router = APIRouter(prefix='/api/warnings', tags=['settlement assessments'])


def snapshot(request, mode):
    service = request.app.state.assessments
    if mode == 'live': return service.live(request.app.state.live_weather.get())
    with _run_lock:
        run = get_shared_run_state()
        if not run.is_active: raise HTTPException(409, 'No active exercise')
        return service.replay(run)


@router.get('/summary')
def summary(request: Request, mode: Literal['live', 'exercise'] = 'live'):
    return snapshot(request, mode)


@router.get('/settlements')
def settlements(request: Request, mode: Literal['live', 'exercise'] = 'live'):
    return snapshot(request, mode)['assessments']


@router.get('/roads')
def roads():
    raise HTTPException(409, 'Verified road assessment is not connected. Rain or a citizen claim cannot confirm a closure.')


@router.get('/{entity_id}/card')
def card(entity_id: str, request: Request, mode: Literal['live', 'exercise'] = 'live'):
    found = next((c for c in snapshot(request, mode)['assessments'] if c['settlement_id'] == entity_id), None)
    if found is None: raise HTTPException(404, 'Unknown settlement')
    return found


@router.post('/reevaluate')
def overrides_disabled():
    raise HTTPException(410, 'Unattributed rainfall and closure overrides have been removed. Use an explicitly labeled exercise.')
