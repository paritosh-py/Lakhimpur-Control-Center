import { requestId } from '../team/requestId';
import { useEffect, useState } from 'react';
import type { Assessment } from './Assessments';
import { severityLabel } from './Assessments';
import './teams.css';

export type Team = { id: string; name: string; location: string; members: number; capabilities: string[]; available: boolean; token: string };
export type Task = { id: string; team_id: string; settlement_id: string; task: string; requirement: string; status: string; version: number; source: string; event_time: string; recorded_at: string; evidence: Assessment; events: { id: number; status: string; note: string; actor: string; event_time: string; recorded_at: string }[] };
export type TeamState = { context: { id: string; source: string; label: string; writable: boolean }; teams: Team[]; assignments: Task[] };
export const activeTask = (t: Task) => !['completed', 'cancelled'].includes(t.status);
export const humanStatus = (s: string) => s.replaceAll('_', ' ');
export const stamp = (s: string) => new Date(s).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) + ' IST';
export async function teamApi(url: string, method = 'GET', body?: object, token?: string) {
  const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(25000) });
  const value = await r.json().catch(() => null);
  if (!r.ok) throw new Error(typeof value?.detail === 'string' ? value.detail : r.status >= 500 ? 'Team service is unavailable. Your last confirmed state is preserved; retry when the backend returns.' : 'Invalid input. Check the required fields.');
  if (!value) throw new Error('Team service returned an invalid response. Retry the request.');
  return value;
}
export function useTeams(context: string | null) {
  const [data, setData] = useState<TeamState | null>(null), [error, setError] = useState(''), [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!context) return;
    let cancelled = false; let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try { const next = await teamApi('/api/teams/state?context=' + encodeURIComponent(context)); if (!cancelled) { setData(next); setError(''); } }
      catch (e) { if (!cancelled) setError(String(e)); }
      finally { if (!cancelled) timer = setTimeout(load, 5000); }
    };
    load(); return () => { cancelled = true; clearTimeout(timer); };
  }, [context, revision]);
  return { data: data?.context.id === context ? data : null, error, refresh: () => setRevision(v => v + 1) };
}

const capabilities = ['assessment', 'rescue', 'medical', 'evacuation', 'boat'];
type Place = { id: string; name: string };
export function TaskHistory({ task }: { task: Task }) {
  return <details className="task-history"><summary>Assignment history · {task.events.length} updates</summary>{task.events.map(e => <div key={e.id}><strong>{humanStatus(e.status)} · {e.actor}</strong><p>{e.note || 'Status updated'}</p><small>{task.source === 'simulated' ? 'Simulation time' : 'Event time'}: {stamp(e.event_time)} · Recorded: {stamp(e.recorded_at)}</small></div>)}</details>;
}

export function TeamsPage({ context, state, places, cards, target, onMap }: { context: string | null; state: ReturnType<typeof useTeams>; places: Place[]; cards: Assessment[]; target: string | null; onMap: (id: string) => void }) {
  const [name, setName] = useState(''), [location, setLocation] = useState(''), [members, setMembers] = useState(4), [skills, setSkills] = useState<string[]>(['assessment']);
  const [editing, setEditing] = useState<Team | null>(null), [available, setAvailable] = useState(true);
  const [settlement, setSettlement] = useState(target || ''), [team, setTeam] = useState(''), [task, setTask] = useState(''), [requirement, setRequirement] = useState('assessment');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  useEffect(() => { if (target) setSettlement(target); }, [target]);
  if (!context) return <section className="teams-page"><h2>Teams & assignments</h2><p>Load a historical replay or synthetic exercise first. Its roster and assignments will be separate from live operations.</p></section>;
  const data = state.data, tasks = data?.assignments || [], teams = data?.teams || [];
  const occupied = new Set(tasks.filter(activeTask).map(t => t.team_id));
  const eligible = teams.filter(t => t.available && !occupied.has(t.id) && t.capabilities.includes(requirement));
  const card = cards.find(c => c.settlement_id === settlement);
  const disabled = busy || !data?.context.writable || !!state.error;
  const placeName = (id: string) => places.find(p => p.id === id)?.name || id;
  const execute = async (action: () => Promise<unknown>, message: string) => {
    setBusy(true); setError(''); setNotice('');
    try { await action(); setNotice(message); state.refresh(); } catch (e) { setError(String(e)); state.refresh(); } finally { setBusy(false); }
  };
  const edit = (t: Team) => { setEditing(t); setName(t.name); setLocation(t.location); setMembers(t.members); setSkills(t.capabilities); setAvailable(t.available); };
  return <section className="teams-page"><h2>Teams & assignments</h2><p>{context === 'live' ? 'Live operations' : 'Exercise roster · simulated assignments, not live'} · Team App updates refresh here every 5 seconds.</p>
    <p className="live-scope">Manual dispatch. Availability and declared capabilities are checked. Routes, travel times, road-model predictions and shelter reservations are not yet connected.</p>
    {(error || state.error) && <p role="alert" className="live-error">{error || state.error}</p>}{notice && <p role="status" className="team-success">{notice}</p>}
    {!data && <p>Loading the team ledger…</p>}
    {data && !data.context.writable && <p className="team-review">This run is reset or inactive. Load its first hour before adding teams. Earlier run records are preserved separately.</p>}
    <div className="team-forms"><form onSubmit={e => { e.preventDefault(); execute(async () => { await teamApi('/api/teams' + (editing ? '/' + editing.id : '') + '?context=' + encodeURIComponent(context), editing ? 'PUT' : 'POST', { name, location, members, capabilities: skills, available }); setName(''); setEditing(null); }, editing ? 'Team updated.' : 'Team added.'); }}>
      <h3>{editing ? 'Edit team' : 'Add a team'}</h3><label>Team name<input required maxLength={60} value={name} onChange={e => setName(e.target.value)} placeholder="Team A" /></label>
      <label>Current location<select required value={location} onChange={e => setLocation(e.target.value)}><option value="">Choose settlement</option>{places.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
      <label>Team members<input required type="number" min={1} max={100} value={members} onChange={e => setMembers(Number(e.target.value))} /></label>
      <fieldset><legend>Declared capabilities</legend>{capabilities.map(c => <label className="team-check" key={c}><input type="checkbox" checked={skills.includes(c)} onChange={e => setSkills(v => e.target.checked ? [...v, c] : v.filter(x => x !== c))} />{c}</label>)}</fieldset>
      <label className="team-check"><input type="checkbox" checked={available} onChange={e => setAvailable(e.target.checked)} />Available for assignment</label>
      <button disabled={disabled || !skills.length} type="submit">{editing ? 'Save team' : 'Add team'}</button>{editing && <button type="button" onClick={() => { setEditing(null); setName(''); }}>Cancel edit</button>}
    </form>
      <form onSubmit={e => { e.preventDefault(); execute(async () => { await teamApi('/api/teams/assignments?context=' + encodeURIComponent(context), 'POST', { team_id: team, settlement_id: settlement, task, requirement, request_id: requestId() }); setTeam(''); setTask(''); }, 'Assignment delivered to the Team App.'); }}>
        <h3>Assign a settlement</h3><label>Target settlement<select required value={settlement} onChange={e => setSettlement(e.target.value)}><option value="">Choose settlement</option>{places.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        {card && <p>{severityLabel(card.severity)} · {card.confidence} confidence · priority {card.rank}. {card.why}</p>}
        <label>Required capability<select value={requirement} onChange={e => { setRequirement(e.target.value); setTeam(''); }}>{capabilities.map(c => <option key={c}>{c}</option>)}</select></label>
        <label>Available team<select required value={team} onChange={e => setTeam(e.target.value)}><option value="">Choose eligible team</option>{eligible.map(t => <option key={t.id} value={t.id}>{t.name} · {placeName(t.location)} · {t.members} members</option>)}</select></label>
        {!eligible.length && <p>No available team has this capability. Add a team or complete an existing assignment.</p>}
        <label>Task instructions<textarea required minLength={3} maxLength={1000} rows={3} value={task} onChange={e => setTask(e.target.value)} placeholder="Describe the assessment or assistance required" /></label>
        <p>Route and ETA: unverified. This assigns a task; it does not certify a safe travel route.</p><button type="submit" disabled={disabled || !eligible.some(t => t.id === team)}>Assign team</button>
      </form></div>
    <h3>Team roster</h3>{!teams.length ? <p>No teams added in this {context === 'live' ? 'live roster' : 'exercise run'}.</p> : <div className="live-table-scroll"><table><thead><tr><th>Team</th><th>Location</th><th>Capability</th><th>Status</th><th>Actions</th></tr></thead><tbody>{teams.map(t => <tr key={t.id}><td>{t.name}<small> · {t.members} members</small></td><td>{placeName(t.location)}</td><td>{t.capabilities.join(', ')}</td><td>{occupied.has(t.id) ? 'On assignment' : t.available ? 'Available' : 'Unavailable'}</td><td><button disabled={disabled || occupied.has(t.id)} onClick={() => edit(t)}>Edit {t.name}</button> <a target="_blank" rel="noreferrer" href={'/?view=team#token=' + encodeURIComponent(t.token)}>Open Team App — {t.name}</a></td></tr>)}</tbody></table></div>}
    <h3>Assignments & team messages</h3>{!tasks.length ? <p>No assignments yet. Select a settlement and dispatch an available team above.</p> : tasks.map(t => {
      const current = cards.find(c => c.settlement_id === t.settlement_id); return <article className="team-task" key={t.id}><div className="warning-title"><h3>{teams.find(x => x.id === t.team_id)?.name || 'Team'} → {placeName(t.settlement_id)}</h3><strong>{humanStatus(t.status)}</strong><button onClick={() => onMap(t.settlement_id)}>Locate assignment</button></div><p>{t.task}</p><p>{t.source === 'simulated' ? 'SIMULATED ASSIGNMENT' : 'LIVE ASSIGNMENT'} · {stamp(t.event_time)} · Required: {t.requirement}</p>
        {current && activeTask(t) && current.severity !== t.evidence.severity && <p className="team-review">Conditions changed: {severityLabel(t.evidence.severity)} at dispatch → {severityLabel(current.severity)} now. Review this commitment; it has not been automatically reassigned.</p>}
        {t.status === 'blocked' && <p className="live-error">Team reported a blockage. Assignment remains reserved and needs operator review. This is not an automatically verified road closure.</p>}
        <TaskHistory task={t} />{['assigned', 'accepted'].includes(t.status) && <button disabled={disabled} onClick={() => execute(() => teamApi('/api/teams/assignments/' + t.id + '/cancel?context=' + encodeURIComponent(context), 'POST', { status: 'cancelled', note: 'Cancelled by control center before travel commitment.', version: t.version, request_id: requestId() }), 'Assignment cancelled; team released.')}>Cancel uncommitted task</button>}
      </article>;
    })}
  </section>;
}
