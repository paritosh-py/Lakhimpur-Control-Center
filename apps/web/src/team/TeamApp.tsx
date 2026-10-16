import { useEffect, useRef, useState } from 'react';
import { requestId } from './requestId';
import RouteMap from './RouteMap';
import NavigationMode from './NavigationMode';
import { humanStatus, stamp, TaskHistory } from '../command/Teams';
import './team.css';

type Settlement = { id: string; name: string };

type MissionPlan = {
  basecamp: { name: string; plus_code: string; address: string; latitude: number; longitude: number };
  settlement: { id: string; name: string; coordinates: [number, number] };
  shelter?: { name: string; published_capacity: number; nearest_segment_id?: string } | null;
  mission_summary: {
    total_distance_km: number;
    total_time_minutes: number;
    leg1_time_minutes: number;
    leg2_time_minutes: number;
    overall_reliability_pct: number;
  };
  leg1_routes: {
    recommended: any;
    alternatives: any[];
    rejected_routes: any[];
  };
  leg2_route?: any;
  navigation_steps: any[];
  model_status?: string;
  has_active_assignment?: boolean;
  active_task?: any;
  assigned_team?: any;
  context?: { id: string; source: string; label: string; event_time: string | null; writable: boolean };
  settlements?: Settlement[];
};

const transitions: Record<string, string[]> = {
  assigned: ['accepted'],
  accepted: ['en_route', 'blocked'],
  en_route: ['arrived', 'blocked'],
  arrived: ['completed', 'blocked'],
  blocked: ['en_route'],
};

export default function TeamApp() {
  const token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
  const [mission, setMission] = useState<MissionPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  const [selectedSettlementId, setSelectedSettlementId] = useState('');
  const [note, setNote] = useState('');
  const [notice, setNotice] = useState('');
  const missionRef = useRef<MissionPlan | null>(null);
  missionRef.current = mission;

  const loadMission = async (settlementId?: string, isBackground = false) => {
    // Only set full loading screen on initial fetch when mission is not yet available
    if (!isBackground && !missionRef.current) {
      setLoading(true);
    }
    if (!isBackground) {
      setError('');
    }
    try {
      if (token) {
        // Authenticated team link
        const portalRes = await fetch('/api/teams/portal', {
          headers: { Authorization: 'Bearer ' + token },
        });
        if (!portalRes.ok) throw new Error('Failed to load team assignment');
        const portalData = await portalRes.json();
        const activeTask = portalData.assignments?.find(
          (t: any) => !['completed', 'cancelled'].includes(t.status)
        );

        const targetId = settlementId || activeTask?.settlement_id || portalData.settlements?.[0]?.id;
        if (!targetId) throw new Error('No target settlement for this team.');

        // On background refresh, if the target settlement hasn't changed, only update assignment status
        const currentTargetId = missionRef.current?.settlement?.id;
        if (isBackground && currentTargetId === targetId && missionRef.current) {
          setMission(prev => prev ? ({
            ...prev,
            active_task: activeTask,
            assigned_team: portalData.team,
            has_active_assignment: !!activeTask,
            context: portalData.context,
            settlements: portalData.settlements,
          }) : prev);
          return;
        }

        const routeRes = await fetch(`/api/routes/plan?settlement_id=${targetId}`);
        if (!routeRes.ok) throw new Error('Failed to compute route from Basecamp');
        const routeData = await routeRes.json();

        routeData.active_task = activeTask;
        routeData.assigned_team = portalData.team;
        routeData.has_active_assignment = !!activeTask;
        routeData.context = portalData.context;
        routeData.settlements = portalData.settlements;
        setMission(routeData);
      } else {
        // Direct mobile access without token (single phone mode)
        const currentTargetId = missionRef.current?.settlement?.id;
        if (isBackground && settlementId && currentTargetId === settlementId && missionRef.current) {
          return;
        }

        const url = settlementId ? `/api/routes/plan?settlement_id=${settlementId}` : '/api/routes/active';
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to load route plan from Basecamp');
        const data = await res.json();
        setMission(data);
      }
    } catch (err: any) {
      if (!isBackground) {
        setError(err.message || 'Error connecting to Lakhimpur emergency server');
      }
    } finally {
      if (!isBackground) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    let done = false;
    let timer: ReturnType<typeof setTimeout>;
    const run = async () => {
      await loadMission(selectedSettlementId || undefined, !!missionRef.current);
      if (!done) timer = setTimeout(run, 10000);
    };
    run();
    return () => {
      done = true;
      clearTimeout(timer);
    };
  }, [token, selectedSettlementId]);

  const update = async (status?: string, customNote?: string) => {
    const task = mission?.active_task;
    if (!task) return;
    setBusy(true);
    setActionError('');
    setNotice('');
    try {
      const res = await fetch(`/api/teams/portal/${task.id}/updates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: 'Bearer ' + token } : {}),
        },
        body: JSON.stringify({
          status: status || null,
          note: customNote || note,
          version: task.version,
          request_id: requestId(),
        }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || 'Failed to update status');
      }
      setNote('');
      setNotice('Update received by the control center.');
      await loadMission(selectedSettlementId || undefined, false);
    } catch (e: any) {
      setActionError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  // If in active Google Maps turn-by-turn navigation mode:
  if (isNavigating && mission && mission.navigation_steps) {
    return (
      <NavigationMode
        mission={mission}
        task={mission.active_task}
        onUpdateStatus={update}
        onExit={() => setIsNavigating(false)}
      />
    );
  }

  const activeRoute = mission?.leg1_routes?.recommended;
  const leg1Polyline: [number, number][] = activeRoute?.polyline || [];
  const leg2Polyline: [number, number][] = mission?.leg2_route?.polyline || [];
  const rejectedRoutes = mission?.leg1_routes?.rejected_routes || [];
  const task = mission?.active_task;
  const settlementName = mission?.settlement?.name || task?.settlement_id || 'Settlement';

  return (
    <div className="team-mobile-container">
      {/* Top Header */}
      <header className="team-mobile-header">
        <div>
          <h1>
            <span>🚑</span> {mission?.assigned_team?.name || 'Rescue Team App'}
          </h1>
          <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8' }}>
            Lakhimpur · assignments, road prediction & navigation
          </p>
        </div>
        <a href="/" style={{ color: '#60a5fa', fontSize: '0.8rem', textDecoration: 'none' }}>
          Control center
        </a>
      </header>

      {/* Timeline Strip */}
      <div className="timeline-strip" style={{ margin: '8px 16px', padding: '8px 12px', background: '#111c2e', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
        <strong>
          {mission?.context?.source === 'live'
            ? 'LIVE TEAM OPERATIONS'
            : mission?.context
              ? 'EXERCISE TEAM APP · NOT LIVE'
              : 'TEAM OPERATIONS · NOT CONNECTED'}
        </strong>
        <span>{mission?.context?.event_time ? stamp(mission.context.event_time) : 'No active timeline'}</span>
      </div>

      {mission?.context && !mission.context.writable && (
        <p className="live-error" style={{ margin: '8px 16px' }}>
          This exercise has ended or was reset. History remains available; updates are disabled.
        </p>
      )}

      {/* Basecamp Origin Banner */}
      <div className="basecamp-origin-card">
        <div className="basecamp-icon">📍</div>
        <div className="basecamp-info">
          <strong>Basecamp: Borimuri (North Lakhimpur)</strong>
          <small>Plus Code: 748G+M62 · 27.2666° N, 94.1255° E · All dispatches start here</small>
        </div>
      </div>

      {(error || actionError) && (
        <p role="alert" className="live-error" style={{ margin: '0 16px 12px 16px' }}>
          {error || actionError}
        </p>
      )}

      {notice && (
        <p role="status" className="team-success" style={{ margin: '0 16px 12px 16px' }}>
          {notice}
        </p>
      )}

      {/* Settlement Selector (if no active assignment or testing) */}
      {!task && mission?.settlements && (
        <div style={{ margin: '0 16px 14px 16px', padding: '12px', background: '#151f30', borderRadius: '10px', border: '1px solid #1e3a5f' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '6px', fontWeight: 600 }}>
            SELECT TARGET SETTLEMENT TO ROUTE:
          </label>
          <select
            style={{ width: '100%', padding: '10px', background: '#0b111e', color: '#f1f5f9', border: '1px solid #334155', borderRadius: '8px', fontSize: '0.95rem' }}
            value={selectedSettlementId || mission.settlement?.id || ''}
            onChange={e => {
              const newId = e.target.value;
              setSelectedSettlementId(newId);
              loadMission(newId, false);
            }}
          >
            {mission.settlements.map((s: any) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {loading && !mission ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
          Computing arrival-time road predictions and optimal route…
        </div>
      ) : task ? (
        <>
          {/* Mission & Assignment Card */}
          <section className="mission-card teams-page">
            <div className="mission-header-row">
              <h2 className="mission-target-title">Assignment: {settlementName}</h2>
              <span className="mission-badge">
                {humanStatus(task.status)}
              </span>
            </div>
            <p className="mission-task-desc team-instructions">
              <strong>{humanStatus(task.status)}</strong> · {task.requirement}
              <br />
              {task.task}
            </p>

            {/* 2-Leg Journey Plan */}
            <div className="journey-plan">
              <div className="journey-leg">
                <span className="journey-leg-icon">🚩</span>
                <div>
                  <strong>Leg 1 (Rescue):</strong> Borimuri Basecamp ➔ {settlementName}
                </div>
              </div>
              {mission?.shelter && (
                <div className="journey-leg">
                  <span className="journey-leg-icon">🏥</span>
                  <div>
                    <strong>Leg 2 (Evacuation):</strong> {settlementName} ➔ {mission.shelter.name}
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#34d399' }}>
                      Relief Camp · Published Capacity: {mission.shelter.published_capacity} people
                    </span>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Route Metrics Strip */}
          {mission?.mission_summary && (
            <div className="route-metrics-bar">
              <div className="metric-box">
                <span>Total Distance</span>
                <strong>{mission.mission_summary.total_distance_km} km</strong>
              </div>
              <div className="metric-box">
                <span>Est. Travel Time</span>
                <strong>{mission.mission_summary.total_time_minutes} min</strong>
              </div>
              <div className="metric-box reliability">
                <span>Route Passability</span>
                <strong>{activeRoute?.reliability_pct || mission.mission_summary.overall_reliability_pct}%</strong>
              </div>
            </div>
          )}

          {/* Interactive Route Map */}
          {mission?.settlement && (
            <div className="team-map-wrapper">
              <RouteMap
                basecamp={mission.basecamp}
                settlement={mission.settlement}
                shelter={mission.shelter}
                leg1Polyline={leg1Polyline}
                leg2Polyline={leg2Polyline}
                height="260px"
              />
            </div>
          )}

          {/* Big Green Start Navigation CTA */}
          <div className="nav-cta-section">
            <button
              className="btn-start-navigation"
              onClick={() => setIsNavigating(true)}
              aria-label="Start Google Maps navigation"
            >
              🧭 Start Navigation (Live Steps)
            </button>
          </div>

          {/* Status message and Action Buttons */}
          <section className="teams-page" style={{ margin: '0 16px 14px 16px', padding: '16px', background: '#131c2d', borderRadius: '12px', border: '1px solid #1e2b40' }}>
            <label className="team-note">
              Status message
              <textarea
                rows={3}
                maxLength={1000}
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="Describe your progress or a blockage and its location"
              />
            </label>
            <div className="exercise-buttons" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
              {(transitions[task.status] || []).map(s => (
                <button
                  key={s}
                  disabled={busy || !!error || (mission?.context && !mission.context.writable) || (s === 'blocked' && !note.trim())}
                  onClick={() => update(s)}
                >
                  {s === 'blocked'
                    ? 'Report road blocked'
                    : s === 'en_route' && task.status === 'blocked'
                      ? 'Resume travel'
                      : humanStatus(s)}
                </button>
              ))}
              <button
                disabled={busy || !!error || (mission?.context && !mission.context.writable) || !note.trim()}
                onClick={() => update()}
              >
                Send message
              </button>
            </div>
            {task.status === 'blocked' && (
              <p style={{ color: '#f87171', fontSize: '0.85rem', marginTop: '8px' }}>
                Task remains assigned. Explain the blockage to the control center before resuming travel.
              </p>
            )}
            <TaskHistory task={task} />
          </section>

          {/* Avoided / Rejected Roads Card (Clear transparency) */}
          {rejectedRoutes.length > 0 && (
            <section className="avoided-roads-card">
              <h3>⚠️ Avoided / Rejected Roads</h3>
              <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '0 0 8px 0' }}>
                The AI model evaluated alternate segments and rejected them due to flood risk or confirmed closures:
              </p>
              {rejectedRoutes.map((rej: any, i: number) => (
                <div key={i} className="avoided-item">
                  <strong>{rej.route_name}:</strong> {rej.reason}
                </div>
              ))}
            </section>
          )}
        </>
      ) : (
        <section className="teams-page" style={{ margin: '0 16px', padding: '24px', background: '#131c2d', borderRadius: '12px', textAlign: 'center' }}>
          <h2>No active assignment</h2>
          <p style={{ color: '#94a3b8', margin: '8px 0 16px 0' }}>
            New tasks appear automatically when dispatched from the control center.
          </p>

          {/* Even with no active task, show the route preview to the selected settlement */}
          {mission?.settlement && (
            <>
              <div className="journey-plan" style={{ textAlign: 'left', marginBottom: '14px' }}>
                <div className="journey-leg">
                  <span className="journey-leg-icon">🚩</span>
                  <div>
                    <strong>Route Preview:</strong> Borimuri Basecamp ➔ {mission.settlement.name}
                  </div>
                </div>
                {mission.shelter && (
                  <div className="journey-leg">
                    <span className="journey-leg-icon">🏥</span>
                    <div>
                      <strong>Nearest Shelter:</strong> {mission.shelter.name} (Capacity: {mission.shelter.published_capacity})
                    </div>
                  </div>
                )}
              </div>

              {mission?.mission_summary && (
                <div className="route-metrics-bar" style={{ margin: '0 0 14px 0' }}>
                  <div className="metric-box">
                    <span>Total Distance</span>
                    <strong>{mission.mission_summary.total_distance_km} km</strong>
                  </div>
                  <div className="metric-box">
                    <span>Est. Travel Time</span>
                    <strong>{mission.mission_summary.total_time_minutes} min</strong>
                  </div>
                  <div className="metric-box reliability">
                    <span>Route Passability</span>
                    <strong>{activeRoute?.reliability_pct || mission.mission_summary.overall_reliability_pct}%</strong>
                  </div>
                </div>
              )}

              <div className="team-map-wrapper">
                <RouteMap
                  basecamp={mission.basecamp}
                  settlement={mission.settlement}
                  shelter={mission.shelter}
                  leg1Polyline={leg1Polyline}
                  leg2Polyline={leg2Polyline}
                  height="240px"
                />
              </div>

              <div className="nav-cta-section" style={{ marginTop: '14px' }}>
                <button
                  className="btn-start-navigation"
                  onClick={() => setIsNavigating(true)}
                  aria-label="Start Google Maps navigation"
                >
                  🧭 Start Navigation (Live Steps)
                </button>
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}
