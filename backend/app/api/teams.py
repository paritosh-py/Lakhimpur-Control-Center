"""Local control-center dispatch and capability-link Team App endpoints."""
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, ConfigDict, Field
from backend.app.api.scenario import get_shared_run_state, run_locked

router = APIRouter(prefix='/api/teams', tags=['teams and assignments'])
Capability = Literal['assessment','rescue','medical','evacuation','boat']


class TeamInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1,max_length=60)
    location: str
    members: int = Field(ge=1,le=100)
    capabilities: list[Capability] = Field(min_length=1,max_length=5)
    available: bool = True


class DispatchInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    team_id: str
    settlement_id: str
    task: str = Field(min_length=3,max_length=1000)
    requirement: Capability
    request_id: str = Field(min_length=8,max_length=100)


class UpdateInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    status: Literal['accepted','en_route','arrived','completed','blocked','cancelled'] | None = None
    note: str = Field(default='',max_length=1000)
    version: int = Field(ge=1)
    request_id: str = Field(min_length=8,max_length=100)


def context_info(request, context, write=False):
    now = request.app.state.assessments.clock.now().isoformat()
    if context == 'live':
        return {'id':'live','source':'live','label':'LIVE OPERATIONS','event_time':now,'recorded_at':now,'writable':True}
    run = get_shared_run_state()
    active = run.is_active and run.run_id == context and run.step_index > 0
    if write and not active:
        raise HTTPException(409,'Exercise is not active or has no loaded hour. Open its current run; archived assignments are read-only.')
    return {'id':context,'source':'simulated','label':'EXERCISE OPERATIONS — NOT LIVE',
            'event_time':run.current_time.isoformat() if active else None,'recorded_at':now,'writable':bool(active)}


def validate_place(request, ident):
    if ident not in {s['id'] for s in request.app.state.assessments.settlements}:
        raise HTTPException(422,'Select one of the 16 study settlements')


def token_from(authorization):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401,'A team access link is required')
    return authorization[7:]


@router.get('/state')
@run_locked
def state(request: Request, context: str = 'live'):
    result = request.app.state.teams.list(context)
    result['context'] = context_info(request,context)
    return result


@router.post('')
@run_locked
def create_team(payload: TeamInput, request: Request, context: str = 'live'):
    meta = context_info(request,context,True)
    validate_place(request,payload.location)
    return request.app.state.teams.save_team(meta,payload)


@router.put('/{team_id}')
@run_locked
def edit_team(team_id: str, payload: TeamInput, request: Request, context: str = 'live'):
    meta = context_info(request,context,True)
    validate_place(request,payload.location)
    return request.app.state.teams.save_team(meta,payload,team_id)


@router.post('/assignments')
@run_locked
def dispatch(payload: DispatchInput, request: Request, context: str = 'live'):
    meta = context_info(request,context,True)
    validate_place(request,payload.settlement_id)
    service = request.app.state.assessments
    snap = service.live(request.app.state.live_weather.get()) if context == 'live' else service.replay(get_shared_run_state())
    evidence = next(c for c in snap['assessments'] if c['settlement_id']==payload.settlement_id)
    return request.app.state.teams.dispatch(meta,payload,evidence)


@router.post('/assignments/{ident}/cancel')
@run_locked
def cancel(ident: str, payload: UpdateInput, request: Request, context: str = 'live'):
    return request.app.state.teams.update(context_info(request,context,True),ident,payload,admin=True)


@router.get('/portal')
@run_locked
def portal(request: Request, authorization: str | None = Header(default=None)):
    result = request.app.state.teams.portal(token_from(authorization))
    result['context'].update(context_info(request,result['team']['context']))
    result['team'].pop('token',None)
    result['settlements'] = [{'id':s['id'],'name':s['name']} for s in request.app.state.assessments.settlements]
    return result


@router.post('/portal/{ident}/updates')
@run_locked
def team_update(ident: str, payload: UpdateInput, request: Request, authorization: str | None = Header(default=None)):
    team = request.app.state.teams.portal(token_from(authorization))['team']
    return request.app.state.teams.update(context_info(request,team['context'],True),ident,payload,team_id=team['id'])
