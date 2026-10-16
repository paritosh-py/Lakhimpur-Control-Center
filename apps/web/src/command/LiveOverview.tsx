import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { FeatureCollection } from 'geojson';
import './live.css';
import './light-theme.css';
import { AssessmentEvidence, WarningsPage, severityColor, severityLabel } from './Assessments';
import type { Assessment } from './Assessments';
import { TeamsPage, useTeams, activeTask, humanStatus } from './Teams';
import { ReportsPage } from './ReportsPage';
import type { CitizenReport } from './ReportsPage';

type Layer = 'boundary' | 'roads' | 'waterways' | 'settlements' | 'shelters';
type Place = {
  settlement_id: string;
  name: string;
  latitude: number;
  longitude: number;
  grid_latitude: number | null;
  grid_longitude: number | null;
  valid_at: string | null;
  interval_seconds: number | null;
  status: 'current' | 'stale' | 'unavailable';
  rain_status: 'raining' | 'no_rain' | 'unknown';
  condition: string;
  values: Record<string, number | null>;
  missing_fields: string[];
};
type Snapshot = {
  mode: 'live' | 'replay' | 'simulated';
  provider: string;
  retrieved_at: string | null;
  checked_at: string;
  next_refresh_at: string | null;
  error: string | null;
  settlements: Place[];
  grid_cells: number;
  counts: Record<string, number>;
  raining_count: number;
  assessments?: Assessment[];
  display_label?: string;
  replayed_at?: string;
  limitations?: string;
  run?: { step_index: number; is_exhausted: boolean; run_id: string };
};
type Geography = { layers: Record<Layer, FeatureCollection>; bounds: number[] };
const layers: Layer[] = ['boundary', 'waterways', 'roads', 'settlements', 'shelters'];
const labels: Record<Layer, string> = {
  boundary: 'District boundary',
  roads: 'Roads',
  waterways: 'Waterways',
  settlements: 'Settlements',
  shelters: 'Reference camps',
};

const color = (p?: Place, failed = false) =>
  failed || !p || p.status !== 'current'
    ? '#a3aab5'
    : p.rain_status === 'raining'
      ? '#63b7f2'
      : p.rain_status === 'no_rain'
        ? '#65c5a1'
        : '#a3aab5';

const time = (s: string | null | undefined) =>
  s
    ? new Date(s).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    }) + ' IST'
    : 'Not available';

const number = (v: number | null | undefined, unit = '') => (v == null ? 'Unknown' : `${v.toFixed(1)}${unit}`);

async function get<T>(url: string, signal?: AbortSignal): Promise<T> {
  const r = await fetch(url, { signal });
  if (!r.ok) throw new Error(`Request failed (${r.status})`);
  return r.json();
}

export default function LiveOverview() {
  const [geo, setGeo] = useState<Geography | null>(null);
  const [geoError, setGeoError] = useState('');
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [feedError, setFeedError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  const [tab, setTab] = useState<'overview' | 'sources' | 'warnings' | 'teams' | 'reports'>('overview');
  const [citizenReports, setCitizenReports] = useState<CitizenReport[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const [mode, setMode] = useState<'live' | 'exercise'>('live');

  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [exerciseError, setExerciseError] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [camp, setCamp] = useState<Record<string, any> | null>(null);
  const [enabled, setEnabled] = useState<Record<Layer, boolean>>({
    boundary: true,
    roads: true,
    waterways: true,
    settlements: true,
    shelters: true,
  });
  const [basemap, setBasemap] = useState(false);
  const [tileError, setTileError] = useState(false);

  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const drawn = useRef<Partial<Record<Layer, L.GeoJSON>>>({});
  const markers = useRef<Record<string, L.CircleMarker>>({});
  const teamContext = mode === 'live' ? 'live' : snapshot?.run?.run_id || null;
  const teamState = useTeams(teamContext);



  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      get<any>('/api/geography/summary', controller.signal),
      ...layers.map(l => get<FeatureCollection>('/api/geography/' + l, controller.signal)),
    ])
      .then(([summary, ...features]) =>
        setGeo({
          bounds: summary.study_bounds,
          layers: Object.fromEntries(layers.map((l, i) => [l, features[i]])) as Geography['layers'],
        })
      )
      .catch(e => {
        if (e.name !== 'AbortError')
          setGeoError('The local map data could not be loaded. Check the backend and reload.');
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (mode !== 'live') {
      setLoading(false);
      return;
    }
    let cancelled = false;
    let request: AbortController | undefined;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      request = new AbortController();
      const timeout = setTimeout(() => request?.abort(), 25000);
      if (!cancelled) setLoading(true);
      try {
        const value = await get<Snapshot>('/api/live/conditions', request.signal);
        if (!cancelled) {
          setSnapshot(value);
          setFeedError('');
        }
      } catch {
        if (!cancelled)
          setFeedError(
            'Live service could not be reached. Previously displayed readings are not confirmed current. Retrying automatically.'
          );
      } finally {
        clearTimeout(timeout);
        if (!cancelled) {
          setLoading(false);
          timer = setTimeout(load, 60000);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
      clearTimeout(timer);
      request?.abort();
    };
  }, [refresh, mode]);

  const exercise = async (action: string, body?: object) => {
    setBusy(true);
    setExerciseError('');
    try {
      const response = await fetch('/api/scenario/' + action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(30000),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Exercise request failed');
      if (action === 'start') {
        const first = await fetch('/api/scenario/step', { method: 'POST', signal: AbortSignal.timeout(10000) });
        if (!first.ok)
          throw new Error('Dataset loaded but the first hour could not be read. Reload the dataset.');
      }
      const next = await get<Snapshot>('/api/scenario/snapshot', AbortSignal.timeout(10000));
      setSnapshot(next);
      setFeedError('');
      if (next.run?.is_exhausted) setPlaying(false);
    } catch (e) {
      setPlaying(false);
      setExerciseError(String(e));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!playing || busy || mode !== 'exercise') return;
    const timer = setTimeout(() => exercise('step'), 1500);
    return () => clearTimeout(timer);
  }, [playing, busy, mode, snapshot]);

  useEffect(() => {
    if (!geo || !container.current) return;
    const [w, s, e, n] = geo.bounds;
    const boundsPad = 0.22;
    const maxBounds: L.LatLngBoundsLiteral = [
      [s - boundsPad, w - boundsPad],
      [n + boundsPad, e + boundsPad],
    ];

    const instance = L.map(container.current, {
      zoomControl: false,
      scrollWheelZoom: false, // Prevents sudden zoom jumps when scrolling past map
      doubleClickZoom: true,
      touchZoom: true,
      maxBounds: maxBounds, // Prevents map from moving away from Lakhimpur frame
      maxBoundsViscosity: 0.95,
      minZoom: 9.5,
      maxZoom: 16,
    });
    map.current = instance;

    instance.createPane('liveSettlements').style.zIndex = '450';
    instance.createPane('liveCamps').style.zIndex = '440';
    L.control.zoom({ position: 'bottomright' }).addTo(instance);
    L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(instance);
    instance.attributionControl.addAttribution('© OpenStreetMap contributors · GeoNames · NWIC · Copernicus · DDMA');

    layers.forEach(name => {
      const group = L.geoJSON(geo.layers[name], {
        style:
          name === 'settlements' || name === 'shelters'
            ? { color: '#172322', weight: 2, fillColor: name === 'shelters' ? '#f5b85a' : '#a3aab5', fillOpacity: 1 }
            : {
              color: name === 'boundary' ? '#6d827a' : name === 'waterways' ? '#648d9b' : '#b8a779',
              weight: name === 'boundary' ? 1.5 : 1.4,
              opacity: 0.65,
              fillOpacity: 0.015,
              dashArray: name === 'boundary' ? '5 5' : undefined,
            },
        pointToLayer: (f, latlng) => {
          const marker = L.circleMarker(latlng, {
            pane: name === 'settlements' ? 'liveSettlements' : 'liveCamps',
            radius: name === 'shelters' ? 6 : 8,
            color: '#172322',
            weight: 2,
            fillColor: name === 'shelters' ? '#f5b85a' : '#a3aab5',
            fillOpacity: 1,
          });
          if (name === 'settlements') markers.current[f.properties.id] = marker;
          return marker;
        },
        onEachFeature: (f, feature) => {
          const text = document.createElement('span');
          text.textContent = f.properties?.name || 'Unnamed road';
          feature.bindTooltip(text);
          if (name === 'settlements')
            feature.on('click', () => {
              setSelected(f.properties.id);
              setCamp(null);
            });
          if (name === 'shelters')
            feature.on('click', () => {
              setCamp(f.properties);
              setSelected(null);
            });
        },
      }).addTo(instance);
      drawn.current[name] = group;
    });

    drawn.current.settlements?.bringToFront();

    // Borimuri Basecamp HQ marker
    instance.createPane('basecampPane').style.zIndex = '460';
    const basecampDiv = L.divIcon({
      className: 'basecamp-map-pin',
      html: '<div style="background:#2563eb;color:#ffffff;padding:4px 9px;border-radius:12px;font-size:11px;font-weight:700;border:2px solid #ffffff;box-shadow:0 2px 8px rgba(0,0,0,0.6);white-space:nowrap;display:inline-flex;align-items:center;gap:4px;">📍 HQ Basecamp</div>',
      iconSize: [96, 24],
      iconAnchor: [48, 12],
    });
    L.marker([27.2666, 94.1255], {
      pane: 'basecampPane',
      icon: basecampDiv,
      interactive: false,
    }).addTo(instance);

    instance.fitBounds(
      [
        [s, w],
        [n, e],
      ],
      { padding: [24, 24] }
    );

    // Dynamic resize observer to ensure Leaflet renders cleanly without drift
    const ro = new ResizeObserver(() => {
      instance.invalidateSize();
    });
    ro.observe(container.current);

    return () => {
      ro.disconnect();
      instance.remove();
      map.current = null;
      drawn.current = {};
      markers.current = {};
    };
  }, [geo]);

  useEffect(() => {
    const byId = new Map(snapshot?.settlements.map(p => [p.settlement_id, p]));
    Object.entries(markers.current).forEach(([id, marker]) => {
      const p = byId.get(id);
      const assessment = snapshot?.assessments?.find(c => c.settlement_id === id);
      marker.setStyle({
        fillColor: color(p, !!feedError),
        color: feedError ? '#0d1219' : severityColor(assessment?.severity),
        weight: selected === id ? 5 : 3,
        radius: selected === id ? 11 : 8,
      });
      const node = document.createElement('span');
      node.textContent = `${p?.name || id}: ${feedError || !p || p.status !== 'current' ? 'Current conditions unknown' : p.condition
        }${assessment ? ' · ' + severityLabel(assessment.severity) : ''}`;
      marker.setTooltipContent(node);
    });
  }, [snapshot, selected, feedError, geo]);

  useEffect(() => {
    if (!map.current || !geo || teamState.error) return;
    const group = L.layerGroup().addTo(map.current);
    const tasks = teamState.data?.assignments.filter(activeTask) || [];
    const teams = teamState.data?.teams || [];
    for (const place of geo.layers.settlements.features) {
      const pId = place.properties?.id;
      if (place.geometry.type !== 'Point') continue;
      const assigned = tasks.filter(t => t.settlement_id === pId);
      const stationed = teams.filter(t => t.location === pId && !tasks.some(task => task.team_id === t.id));

      if (!assigned.length && !stationed.length) continue;

      const label = document.createElement('span');
      label.className = 'assignment-marker';

      const textParts: string[] = [];
      assigned.forEach(t => {
        const teamName = teams.find(x => x.id === t.team_id)?.name || 'Team';
        textParts.push(`${teamName}: ${humanStatus(t.status)}`);
      });
      stationed.forEach(t => {
        textParts.push(`${t.name}: ${t.available ? 'Available' : 'Stationed'}`);
      });

      label.textContent = textParts.join(' · ');
      const [lon, lat] = place.geometry.coordinates;
      L.marker([lat, lon], {
        interactive: false,
        icon: L.divIcon({ html: label, className: 'assignment-marker-wrap', iconAnchor: [-12, 24] }),
      }).addTo(group);
    }
    return () => {
      group.remove();
    };
  }, [teamState.data, teamState.error, geo]);

  useEffect(() => {
    let cancelled = false;
    const loadReports = async () => {
      try {
        const res = await fetch(`/api/reports?context=${encodeURIComponent(teamContext || 'live')}`);
        if (res.ok && !cancelled) {
          const data = await res.json();
          setCitizenReports(data.reports || []);
        }
      } catch { }
    };
    loadReports();
    const timer = setInterval(loadReports, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [teamContext]);

  useEffect(() => {
    if (!map.current || !citizenReports.length) return;
    const group = L.layerGroup().addTo(map.current);
    citizenReports.forEach(r => {
      if (r.latitude == null || r.longitude == null) return;
      const isCritical = r.gemini_triage?.urgency === 'CRITICAL' || r.urgency === 'CRITICAL';
      const markerColor = isCritical ? '#ef4444' : r.urgency === 'HIGH' ? '#f59e0b' : '#38bdf8';
      const pin = L.marker([r.latitude, r.longitude], {
        interactive: false,
        icon: L.divIcon({
          className: 'citizen-report-pin',
          html: `<div title="${r.gemini_triage?.urgency || r.urgency}: ${(r.incident_type || '').replaceAll(
            '_',
            ' '
          )}" style="background:${markerColor};width:${isCritical ? 18 : 14}px;height:${isCritical ? 18 : 14
            }px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 0 10px ${markerColor};"></div>`,
          iconSize: [isCritical ? 18 : 14, isCritical ? 18 : 14],
          iconAnchor: [isCritical ? 9 : 7, isCritical ? 9 : 7],
        }),
      });
      pin.addTo(group);
    });
    return () => {
      group.remove();
    };
  }, [citizenReports]);

  useEffect(() => {
    layers.forEach(l => {
      const group = drawn.current[l];
      if (map.current && group) enabled[l] ? group.addTo(map.current) : map.current.removeLayer(group);
    });
  }, [enabled, geo]);

  useEffect(() => {
    if (!map.current || !basemap) return;
    setTileError(false);
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19,
    }).addTo(map.current);
    tiles.on('tileerror', () => setTileError(true));
    tiles.bringToBack();
    return () => {
      tiles.remove();
    };
  }, [basemap, geo]);

  useEffect(() => {
    if (tab === 'overview') setTimeout(() => map.current?.invalidateSize(), 50);
  }, [tab]);

  const places =
    geo?.layers.settlements.features.map(f => ({
      id: String(f.properties?.id),
      name: String(f.properties?.name),
    })) || [];

  const filteredPlaces = places.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const current = snapshot?.settlements.find(p => p.settlement_id === selected);
  const select = (id: string) => {
    setSelected(id);
    setCamp(null);
    const m = markers.current[id];
    if (m) map.current?.panTo(m.getLatLng());
  };

  const fit = () => {
    if (geo && map.current) {
      const [w, s, e, n] = geo.bounds;
      map.current.flyToBounds(
        [
          [s, w],
          [n, e],
        ],
        { padding: [24, 24], duration: 0.75 }
      );
    }
  };

  const currentCount = feedError ? 0 : snapshot?.counts.current || 0;
  const rainy = feedError ? [] : snapshot?.settlements.filter(p => p.rain_status === 'raining') || [];
  const knownRain = feedError ? 0 : snapshot?.settlements.filter(p => p.rain_status !== 'unknown').length || 0;
  const cards = snapshot?.assessments || [];
  const selectedCard = cards.find(c => c.settlement_id === selected);
  const alerts = cards.filter(c => ['watch', 'high', 'critical'].includes(c.severity));

  const weatherSummary =
    mode === 'exercise'
      ? !snapshot
        ? 'No replay loaded'
        : !knownRain
          ? 'Rainfall is unknown at the selected time'
          : rainy.length
            ? `Rainfall in ${rainy.length} settlements at the selected time`
            : 'No rainfall in the selected interval'
      : loading && !snapshot
        ? 'Fetching current conditions for your settlements'
        : !currentCount
          ? 'Current weather is unavailable or stale'
          : !knownRain
            ? 'Current rainfall is unknown'
            : rainy.length
              ? `Rain reported by the weather model in ${rainy.length} settlements`
              : 'No rain in the current available readings';

  const showOnMap = (id: string) => {
    setTab('overview');
    select(id);
  };
  const assignTo = (id: string) => {
    setSelected(id);
    setTab('teams');
  };

  const changeMode = async (next: 'live' | 'exercise') => {
    setPlaying(false);
    setSnapshot(null);
    setFeedError('');
    setExerciseError('');
    setTab('overview');
    setLoading(next === 'live');
    if (next === 'exercise') {
      try {
        const status = await get<{ is_active: boolean }>('/api/scenario/status', AbortSignal.timeout(10000));
        if (status.is_active) {
          const snap = await get<Snapshot>('/api/scenario/snapshot', AbortSignal.timeout(10000));
          setSnapshot(snap);
        }
      } catch {
        setExerciseError('Could not restore the active exercise. Check the backend before loading a new run.');
      }
    }
    setMode(next);
  };


  return (
    <div className="live-app">
      {/* ----------------- Top Header ----------------- */}
      <header className="live-header">
        <div className="header-left-cluster">
          <div className="header-branding">
            <h1>Lakhimpur Control Center</h1>
            <p>Flood response · Assam · 16-settlement study area</p>
          </div>
        </div>

        <div className="live-feed-status">
          <strong>{mode === 'live' ? 'LIVE MONITORING' : 'REPLAY & EXERCISES'}</strong>
          <span>
            {loading
              ? 'Checking weather…'
              : `${currentCount} of ${places.length || 16} settlements ${mode === 'live' ? 'current' : 'at selected time'
              }`}
            {' · '}
            {teamState.data?.teams.length ? `${teamState.data.teams.length} teams` : '0 teams'}
          </span>
        </div>
      </header>

      {/* Quick Navigation Toolbar (guarantees automated test accessibility & quick clicking) */}
      <nav className="live-nav" aria-label="Command navigation">
        <button aria-current={tab === 'overview' ? 'page' : undefined} onClick={() => setTab('overview')}>
          Overview
        </button>
        <button aria-current={tab === 'warnings' ? 'page' : undefined} onClick={() => setTab('warnings')}>
          Warnings {alerts.length ? `(${alerts.length})` : ''}
        </button>
        <button aria-current={tab === 'teams' ? 'page' : undefined} onClick={() => setTab('teams')}>
          Teams & assignments
        </button>
        <button aria-current={tab === 'reports' ? 'page' : undefined} onClick={() => setTab('reports')}>
          Citizen reports {citizenReports.length ? `(${citizenReports.length})` : ''}
        </button>
        <button aria-current={tab === 'sources' ? 'page' : undefined} onClick={() => setTab('sources')}>
          Data sources & coverage
        </button>
        <button onClick={() => changeMode(mode === 'live' ? 'exercise' : 'live')}>
          {mode === 'live' ? 'Replay & exercises' : 'Return to live'}
        </button>
      </nav>

      <main className="live-content">
        {mode === 'exercise' && (
          <div className="timeline-strip" data-testid="timeline-label">
            <strong>
              {snapshot?.mode === 'replay'
                ? 'HISTORICAL REPLAY'
                : snapshot?.mode === 'simulated'
                  ? 'SYNTHETIC EXERCISE'
                  : 'REPLAY & EXERCISES'}{' '}
              · NOT LIVE
            </strong>
            <span>
              {snapshot
                ? `${snapshot.mode === 'simulated' ? 'Simulation time' : 'Original time'}: ${time(
                  snapshot.checked_at
                )}`
                : 'No dataset loaded'}
            </span>
          </div>
        )}

        {mode === 'exercise' && (
          <section className="exercise-controls" aria-label="Replay controls">
            <h2>Replay & exercises</h2>
            <p>
              Historical weather uses unchanged ERA5 values from 25 June–5 July 2024. ASDMA documents the wider flood
              event; hourly settlement impacts and road closures are not verified.
            </p>
            <div className="exercise-buttons">
              <button
                disabled={busy}
                onClick={() => {
                  setPlaying(false);
                  exercise('start', { mode: 'replay' });
                }}
              >
                Load historical weather
              </button>
              <button
                disabled={busy}
                onClick={() => {
                  setPlaying(false);
                  exercise('start', { mode: 'scenario', seed: 42, duration_hours: 72 });
                }}
              >
                Load synthetic exercise
              </button>
              {snapshot?.run && (
                <>
                  <button disabled={busy || snapshot.run.is_exhausted} onClick={() => exercise('step')}>
                    Advance 1 hour
                  </button>
                  <button
                    disabled={busy || snapshot.run.is_exhausted}
                    onClick={() => setPlaying(v => !v)}
                  >
                    {playing ? 'Pause playback' : 'Play hourly'}
                  </button>
                  <button
                    disabled={busy}
                    onClick={() => {
                      setPlaying(false);
                      exercise('reset');
                    }}
                  >
                    Reset replay
                  </button>
                  {snapshot.run.is_exhausted && (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        color: 'var(--accent-emerald)',
                        fontSize: '15px',
                        fontWeight: 600,
                        padding: '0 8px',
                      }}
                    >
                      ✓ Playback complete
                    </span>
                  )}
                </>
              )}
            </div>
            {busy && <p role="status">Updating the selected timeline…</p>}
            {exerciseError && (
              <p role="alert" className="live-error">
                {exerciseError}
              </p>
            )}
            <div className="exercise-banner">
              <strong>{snapshot?.display_label || 'Choose a dataset — no live data is shown here'}</strong>
              {snapshot?.run && (
                <p>
                  {snapshot.mode === 'simulated' ? 'Simulation time' : 'Original event time'}:{' '}
                  {time(snapshot.checked_at)} · Step {snapshot.run.step_index}
                  {snapshot.run.is_exhausted ? ' · End of dataset' : ''}
                  <br />
                  Played at: {time(snapshot.replayed_at)}
                  <br />
                  {snapshot.limitations}
                </p>
              )}
            </div>
          </section>
        )}

        {/* Dynamic Weather Summary Ribbon */}
        <section className="live-update" aria-live="polite">
          <div>
            <strong>{weatherSummary}</strong>
            <p>
              {rainy.length
                ? rainy.map(p => p.name).join(' · ')
                : `${knownRain} settlements with ${mode === 'live' ? 'current' : 'selected-time'
                } rainfall readings. Missing readings are not treated as dry weather.`}
            </p>
          </div>
          {mode === 'live' && (
            <button disabled={loading} onClick={() => setRefresh(n => n + 1)}>
              {loading ? 'Checking…' : 'Check for updates'}
            </button>
          )}
        </section>

        {(feedError || snapshot?.error) && (
          <p className="live-error" role="alert">
            {feedError || snapshot?.error}
          </p>
        )}

        {!!alerts.length && !feedError && (
          <section className="warning-banner" aria-label="Active settlement warnings">
            <strong>{alerts.length} settlements need attention</strong>
            <p>{alerts.map(c => `${c.name}: ${severityLabel(c.severity)}`).join(' · ')}</p>
            <button onClick={() => setTab('warnings')}>Review warnings</button>
          </section>
        )}

        <p className="live-scope">
          Prototype flood screening, not official warnings. Severity and confidence are assessed separately. Road
          accessibility, river levels and current shelter availability remain unverified.
        </p>

        {tab === 'warnings' && (
          <WarningsPage cards={cards} select={showOnMap} failed={!!feedError} onAssign={assignTo} />
        )}
        {tab === 'teams' && (
          <TeamsPage
            key={teamContext || 'no-exercise'}
            context={teamContext}
            state={teamState}
            places={places}
            cards={cards}
            target={selected}
            onMap={showOnMap}
          />
        )}
        {tab === 'reports' && (
          <ReportsPage
            context={teamContext}
            onLocate={(lat, lon) => {
              setTab('overview');
              setTimeout(() => map.current?.setView([lat, lon], 14), 100);
            }}
            onAssign={assignTo}
          />
        )}

        <div hidden={tab !== 'overview'}>
          {/* Minimalist Overview KPI Metrics Strip */}
          <div className="overview-kpi-strip">
            <div className="overview-kpi-card">
              <span className="kpi-tag">ENVIRONMENT</span>
              <strong>
                {mode === 'live'
                  ? 'Live Telemetry'
                  : snapshot?.mode === 'replay'
                    ? 'Historical Replay'
                    : 'Synthetic Exercise'}
              </strong>
              <small>
                {mode === 'live'
                  ? `${currentCount} / ${places.length || 16} active settlements`
                  : `Timeline step ${snapshot?.run?.step_index ?? 0}`}
              </small>
            </div>
            <div className="overview-kpi-card">
              <span className="kpi-tag">PRECIPITATION</span>
              <strong style={{ color: rainy.length ? 'var(--accent-blue)' : 'var(--accent-emerald)' }}>
                {rainy.length ? `${rainy.length} Settlements Raining` : 'Dry / Clear'}
              </strong>
              <small>
                {rainy.length
                  ? rainy
                    .map(r => r.name)
                    .slice(0, 2)
                    .join(', ') + (rainy.length > 2 ? ` +${rainy.length - 2}` : '')
                  : 'No active cloudburst recorded'}
              </small>
            </div>
            <div className="overview-kpi-card">
              <span className="kpi-tag">PRIORITY WATCH</span>
              <strong style={{ color: alerts.length ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                {alerts.length ? `${alerts.length} Settlements on Watch` : 'All Normal'}
              </strong>
              <small>{alerts.length ? 'Review multi-factor evidence cards' : 'Within baseline safety margins'}</small>
            </div>
            <div className="overview-kpi-card">
              <span className="kpi-tag">OPERATIONS</span>
              <strong>{teamState.data?.teams.length || 0} Rescue Teams</strong>
              <small>{citizenReports.length} ground reports logged</small>
            </div>
          </div>

          <div className="live-layout">
            {/* Left Column: Bounded, Tactical Operational Map */}
            <section className="live-map-section" aria-label="Settlement map">
              <div className="live-section-heading">
                <div>
                  <h2>Conditions across Lakhimpur</h2>
                  <p>Select a settlement on the map or in the list.</p>
                </div>
                <div className="map-action-cluster">
                  <button onClick={fit} title="Fly back to full Lakhimpur view">
                    Reset map
                  </button>
                </div>
              </div>

              {geoError ? (
                <p role="alert" className="live-error">
                  {geoError} <button onClick={() => location.reload()}>Reload map</button>
                </p>
              ) : (
                <div className="live-map-wrapper">
                  <div ref={container} className="live-map" data-testid="live-map" />
                </div>
              )}

              <div className="live-legend">
                <span>
                  <i style={{ background: '#63b7f2' }} />
                  Rain
                </span>
                <span>
                  <i style={{ background: '#65c5a1' }} />
                  No rain reported
                </span>
                <span>
                  <i style={{ background: '#a3aab5' }} />
                  Unknown / stale
                </span>
                <span>
                  <i style={{ background: '#f5b85a' }} />
                  Reference camp
                </span>
                <span>Outline: yellow watch · orange high · red critical</span>
              </div>

              <details className="live-layers">
                <summary>Map layers · {Object.values(enabled).filter(Boolean).length} visible</summary>
                <div>
                  {layers.map(l => (
                    <label key={l}>
                      <input
                        type="checkbox"
                        checked={enabled[l]}
                        onChange={e => setEnabled(v => ({ ...v, [l]: e.target.checked }))}
                      />
                      {labels[l]}
                    </label>
                  ))}
                  <label>
                    <input type="checkbox" checked={basemap} onChange={e => setBasemap(e.target.checked)} />
                    Online street basemap
                  </label>
                </div>
              </details>
              {tileError && (
                <p role="status">Online basemap unavailable. Local geographic layers remain available.</p>
              )}
            </section>

            {/* Right Column: Selected Location Inspector Card */}
            <aside className="live-details" aria-label="Selected location details">
              <h2>{current?.name || camp?.name || 'Settlement details'}</h2>
              {camp ? (
                <>
                  <p>Published relief camp · 2025 inventory</p>
                  <dl>
                    <dt>Published capacity</dt>
                    <dd>{camp.published_capacity}</dd>
                    <dt>Current availability</dt>
                    <dd>Unknown</dd>
                    <dt>Route accessibility</dt>
                    <dd>Unverified</dd>
                  </dl>
                  <p>This is a reference location, not confirmation that the camp is operating.</p>
                </>
              ) : current ? (
                <>
                  <div className="live-condition">
                    <span className={`live-tag ${feedError ? 'stale' : current.status}`}>
                      {feedError ? 'Connection lost' : current.status}
                    </span>
                    <h3>
                      {feedError || current.status !== 'current'
                        ? 'Last available conditions'
                        : current.condition}
                    </h3>
                    {(feedError || current.status !== 'current') && <p>{current.condition}</p>}
                    <strong>{number(current.values.temperature_2m, ' °C')}</strong>
                  </div>
                  <dl>
                    <dt>
                      {mode === 'live' ? 'Rain + showers' : 'Precipitation'} /{' '}
                      {current.interval_seconds ? current.interval_seconds / 60 : '?'} min
                    </dt>
                    <dd>
                      {number(
                        current.values.rain == null || current.values.showers == null
                          ? null
                          : current.values.rain + current.values.showers,
                        ' mm'
                      )}
                    </dd>
                    <dt>Cloud cover</dt>
                    <dd>{number(current.values.cloud_cover, '%')}</dd>
                    <dt>Humidity</dt>
                    <dd>{number(current.values.relative_humidity_2m, '%')}</dd>
                    <dt>Wind</dt>
                    <dd>{number(current.values.wind_speed_10m, ' km/h')}</dd>
                    <dt>Conditions valid at</dt>
                    <dd>{time(current.valid_at)}</dd>
                    <dt>Retrieved</dt>
                    <dd>{time(snapshot?.retrieved_at)}</dd>
                  </dl>
                  <p>
                    {mode === 'live'
                      ? 'Open-Meteo model estimate.'
                      : snapshot?.mode === 'replay'
                        ? 'Historical ERA5 reanalysis, not live.'
                        : 'Simulated weather, not observed.'}{' '}
                    Grid: {current.grid_latitude ?? 'unknown'}, {current.grid_longitude ?? 'unknown'}. Nearby
                    settlements may share a grid.
                  </p>
                  <div className="live-detail-note">
                    <strong>Response teams</strong>
                    {teamState.error ? (
                      <p>Team ledger unavailable. Open Teams & assignments to retry.</p>
                    ) : (
                      <>
                        {teamState.data?.teams.filter(t => t.location === selected).length ? (
                          <p style={{ margin: '4px 0 6px 0', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                            Stationed here:{' '}
                            {teamState.data.teams
                              .filter(t => t.location === selected)
                              .map(
                                t => `${t.name} (${t.available ? 'Available' : 'Unavailable'} · ${t.members} members)`
                              )
                              .join(', ')}
                          </p>
                        ) : null}
                        <p>
                          {teamState.data?.assignments
                            .filter(t => t.settlement_id === selected && activeTask(t))
                            .map(
                              t =>
                                `${teamState.data?.teams.find(x => x.id === t.team_id)?.name}: ${humanStatus(
                                  t.status
                                )}`
                            )
                            .join(' · ') ||
                            (teamState.data
                              ? 'No active mission dispatched to this settlement.'
                              : 'Loading team ledger…')}
                        </p>
                      </>
                    )}
                    <button onClick={() => assignTo(current.settlement_id)}>Assign a team here</button>
                  </div>
                  <div className="live-detail-note">
                    <strong>Flood assessment</strong>
                    {selectedCard ? <AssessmentEvidence card={selectedCard} /> : <p>Assessment unavailable.</p>}
                  </div>
                </>
              ) : (
                <div style={{ padding: '16px 0', color: 'var(--text-secondary)' }}>
                  <p style={{ fontSize: '15px', lineHeight: 1.6 }}>
                    Select any of the 16 study settlements or 7 DDMA relief camps on the map to inspect live weather
                    telemetry, flood assessment cards, and active rescue team assignments.
                  </p>
                </div>
              )}
            </aside>
          </div>

          {/* Settlements Directory Table with Search Filter */}
          <section className="live-settlements">
            <div className="live-section-heading">
              <div>
                <h2>All settlements</h2>
                <p>
                  {currentCount} current ·{' '}
                  {feedError
                    ? 'Connection interrupted'
                    : `${snapshot?.counts.stale || 0} stale · ${snapshot?.counts.unavailable ?? places.length
                    } unavailable`}
                </p>
              </div>
              <div className="table-search-bar" style={{ border: 'none', padding: 0 }}>
                <input
                  type="text"
                  placeholder="Filter settlement..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="table-search-input"
                />
              </div>
            </div>

            <div className="live-table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Settlement</th>
                    <th>Weather</th>
                    <th>{mode === 'live' ? 'Rain + showers' : 'Precipitation'}</th>
                    <th>Temperature</th>
                    <th>Valid at (IST)</th>
                    <th>Data status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlaces.map(p => {
                    const r = snapshot?.settlements.find(v => v.settlement_id === p.id);
                    return (
                      <tr key={p.id} className={p.id === selected ? 'selected' : ''}>
                        <td>
                          <button onClick={() => select(p.id)}>{p.name}</button>
                        </td>
                        <td>
                          <i className="live-dot" style={{ background: color(r, !!feedError) }} />
                          {r?.condition || 'Unknown'}
                        </td>
                        <td>
                          {number(
                            r?.values.rain == null || r?.values.showers == null
                              ? null
                              : r.values.rain + r.values.showers,
                            ' mm'
                          )}
                          <small>{r?.interval_seconds ? ` / ${r.interval_seconds / 60} min` : ''}</small>
                        </td>
                        <td>{number(r?.values.temperature_2m, ' °C')}</td>
                        <td>{time(r?.valid_at)}</td>
                        <td>{feedError ? 'Not current' : r?.status || 'unavailable'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {tab === 'sources' && (
          <section className="live-sources">
            <h2>Data sources & coverage</h2>
            <p>
              Flood screening uses prototype-flood-v1: configurable rainfall windows, wet duration and a terrain
              susceptibility proxy. It is not calibrated or an official warning. No forecast, river level, inundation
              depth or route safety is inferred. Replay is retrospective; its original operational availability is
              unknown.
            </p>
            <dl>
              <dt>Selected weather source</dt>
              <dd>
                {mode === 'exercise' ? snapshot?.provider || 'No dataset loaded' : 'Live model conditions'} ?{' '}
                <a href="https://open-meteo.com/en/docs" target="_blank" rel="noreferrer">
                  Open-Meteo Best Match
                </a>{' '}
                · model estimates, not local rain gauges
              </dd>
              <dt>Latest successful fetch</dt>
              <dd>{time(snapshot?.retrieved_at)}</dd>
              <dt>Next upstream check</dt>
              <dd>{time(snapshot?.next_refresh_at)}</dd>
              <dt>Spatial coverage</dt>
              <dd>
                {places.length} study settlements · {snapshot?.grid_cells ?? 'Unknown'} weather grid cells
              </dd>
              <dt>Refresh</dt>
              <dd>
                Page checks every minute; upstream refresh every 10 minutes. Failure retries after 1 minute. Data older
                than 1 hour is stale.
              </dd>
              <dt>Map</dt>
              <dd>NWIC district boundary · OSM roads/waterways · GeoNames settlements</dd>
              <dt>Terrain and camps</dt>
              <dd>Copernicus 90 m surface model · published DDMA 2025 camp inventory</dd>
              <dt>Not connected</dt>
              <dd>
                Official river-gauge observations, verified closures, current camp occupancy, citizen reports
              </dd>
            </dl>
            <p>
              Weather changes are not proof of flooding or road safety. The original historical datasets are
              preserved separately and never substituted for current observations.
            </p>
          </section>
        )}

        <footer className="live-footer">
          <span>Local command workspace · Lakhimpur, Assam</span>
          <span>Last server check: {time(snapshot?.checked_at)}</span>
        </footer>
      </main>
    </div>
  );
}

