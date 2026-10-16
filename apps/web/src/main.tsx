import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import L from 'leaflet';
import type { Feature, FeatureCollection, Geometry } from 'geojson';
import 'leaflet/dist/leaflet.css';
import './style.css';
import LiveOverview from './command/LiveOverview';
import TeamApp from './team/TeamApp';
import RoadEstimates from './team/RoadEstimates';

type Props = Record<string, any>;
type LayerName = 'roads' | 'settlements' | 'shelters' | 'waterways' | 'boundary';
type Summary = { counts: Record<LayerName, number>; study_bounds: number[]; generated_at: string; terrain: { resolution_m: number }; limitations: string[]; connected_components: number };
type Weather = { label: string; provider: string; retrieved_at: string; records: { valid_at: string; precipitation_mm: number | null }[] };
type Data = { summary: Summary; layers: Record<LayerName, FeatureCollection<Geometry, Props>>; weather: Weather };

type RunStatus = {
  is_active: boolean;
  run_id: string | null;
  mode: 'live' | 'replay' | 'scenario' | null;
  step_index: number;
  current_time: string | null;
  is_exhausted: boolean;
  display_label: string;
  steps_completed: number;
};

type StepRecord = {
  kind: string;
  entity_id: string;
  event_time: string;
  available_at: string;
  source: string;
  provider: string;
  event_name?: string | null;
  replayed_at?: string | null;
  payload: Record<string, any>;
};

type StepResponse = {
  run_id: string;
  step_index: number;
  current_time: string;
  num_records: number;
  record_kinds: Record<string, number>;
  is_exhausted: boolean;
  display_label: string;
  records: StepRecord[];
};

type WarningFactors = {
  recent_rain_1h_mm: number;
  recent_rain_3h_mm: number;
  recent_rain_6h_mm: number;
  forecast_rain_3h_mm: number;
  ground_saturation_api_mm: number;
  elevation_m: number;
  slope_degrees: number;
  distance_to_river_m: number;
  active_reports_count: number;
  is_confirmed_closed: boolean;
};

type EvidenceCard = {
  entity_id: string;
  entity_type: 'settlement' | 'road_segment';
  entity_name: string;
  risk_score: number;
  severity: 'advisory' | 'moderate' | 'high' | 'critical';
  why: string;
  confidence: 'low' | 'medium' | 'high';
  confidence_reason: string;
  data_age_seconds: number;
  lead_time_hours: number | null;
  uncertainty_disclosure: string;
  factors: WarningFactors;
  source_mode: 'live' | 'replay' | 'simulated';
  generated_at: string;
  rank?: number | null;
  rank_delta?: number | null;
  rerank_reason?: string | null;
};

type RankedWarning = {
  rank: number;
  entity_id: string;
  entity_type: 'settlement' | 'road_segment';
  entity_name: string;
  risk_score: number;
  severity: 'advisory' | 'moderate' | 'high' | 'critical';
  primary_driver: string;
  previous_rank: number | null;
  rank_delta: number;
  rerank_reason: string | null;
};

type WarningSummary = {
  run_id: string | null;
  source_mode: 'live' | 'replay' | 'simulated';
  evaluated_at: string;
  total_settlements_evaluated: number;
  total_roads_evaluated: number;
  severity_counts: Record<string, number>;
  highest_risk_settlement: RankedWarning | null;
  highest_risk_road: RankedWarning | null;
  active_warnings: RankedWarning[];
};

const names: LayerName[] = ['boundary', 'waterways', 'roads', 'settlements', 'shelters'];
const colors: Record<LayerName, string> = {
  boundary: '#64748b',
  waterways: '#0284c7',
  roads: '#f59e0b',
  settlements: '#10b981',
  shelters: '#f43f5e',
};

async function api<T>(path: string): Promise<T> {
  const result = await fetch('/api' + path);
  if (!result.ok) throw new Error(`Data request failed (${result.status}). Check the API and acquired datasets.`);
  return result.json();
}

async function postApi<T>(path: string, body?: any): Promise<T> {
  const result = await fetch('/api' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!result.ok) {
    const err = await result.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `Request failed (${result.status})`);
  }
  return result.json();
}

function App() {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const drawn = useRef<Partial<Record<LayerName, L.GeoJSON>>>({});
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<{ kind: LayerName; properties: Props } | null>(null);
  const [enabled, setEnabled] = useState<Record<LayerName, boolean>>({ boundary: true, roads: true, settlements: true, shelters: true, waterways: true });
  const [base, setBase] = useState(false);
  const [tilesFailed, setTilesFailed] = useState(false);
  const tileRef = useRef<L.TileLayer | null>(null);

  // Phase 2: Scenario and run state
  const [targetMode, setTargetMode] = useState<'scenario' | 'replay' | 'live'>('scenario');
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [recentRecords, setRecentRecords] = useState<StepRecord[]>([]);
  const [closedRoads, setClosedRoads] = useState<Set<string>>(new Set());
  const [currentRainRate, setCurrentRainRate] = useState<number>(0.0);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Phase 3: Warning engine and Evidence Cards
  const [warnings, setWarnings] = useState<WarningSummary | null>(null);
  const [selectedCard, setSelectedCard] = useState<EvidenceCard | null>(null);
  const [activeWarningId, setActiveWarningId] = useState<string | null>(null);

  const fetchWarnings = async () => {
    try {
      const summary = await api<WarningSummary>('/warnings/summary');
      setWarnings(summary);
    } catch (e) {
      console.error('Failed to load warnings summary', e);
    }
  };

  const loadEvidenceCard = async (entityId: string) => {
    try {
      const card = await api<EvidenceCard>(`/warnings/${entityId}/card`);
      setSelectedCard(card);
      setActiveWarningId(entityId);
    } catch (e) {
      console.error('Failed to load evidence card', e);
    }
  };

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Summary>('/geography/summary'),
      api<Weather>('/weather/live'),
      Promise.all(names.map(name => api<FeatureCollection<Geometry, Props>>('/geography/' + name))),
      api<RunStatus>('/scenario/status').catch(() => null),
      api<WarningSummary>('/warnings/summary').catch(() => null),
    ])
      .then(([summary, weather, layers, status, warnSummary]) => {
        if (active) {
          setData({ summary, weather, layers: Object.fromEntries(names.map((n, i) => [n, layers[i]])) as Data['layers'] });
          if (status) setRunStatus(status);
          if (warnSummary) setWarnings(warnSummary);
        }
      }).catch(e => { if (active) setError(String(e.message)); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!data || !container.current || mapRef.current) return;
    const map = L.map(container.current, { zoomControl: false });
    mapRef.current = map;
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map);
    map.attributionControl.addAttribution('<a href="https://www.openstreetmap.org/copyright">© OSM</a> · GeoNames · NWIC · Copernicus DEM');
    for (const name of names) {
      const layer = L.geoJSON(data.layers[name], {
        style: (feature) => {
          if (name === 'roads') {
            const isClosed = feature?.properties?.id && closedRoads.has(feature.properties.id);
            return {
              color: isClosed ? '#ef4444' : colors['roads'],
              weight: isClosed ? 3.5 : 2,
              opacity: isClosed ? 1.0 : 0.75,
              dashArray: isClosed ? '4 4' : undefined,
            };
          }
          return name === 'settlements' || name === 'shelters'
            ? { color: '#ffffff', weight: 1.5, fillColor: colors[name], fillOpacity: 0.95 }
            : { color: colors[name], weight: name === 'boundary' ? 1.5 : 2,
              opacity: 0.7, fillOpacity: 0.03, dashArray: name === 'boundary' ? '4 5' : undefined };
        },
        pointToLayer: (_f, latlng) => L.circleMarker(latlng, {
          radius: name === 'shelters' ? 7 : 5,
          color: '#ffffff',
          weight: 1.5,
          fillColor: colors[name],
          fillOpacity: 1,
        }),
        onEachFeature: (f: Feature<Geometry, Props>, item) => {
          const text = document.createElement('span');
          text.textContent = f.properties.name || f.properties.id || name;
          item.bindTooltip(text);
          item.on('click', () => {
            setSelected({ kind: name, properties: f.properties });
            if (name === 'settlements' || name === 'roads') {
              if (f.properties?.id) {
                loadEvidenceCard(f.properties.id);
              }
            } else {
              setSelectedCard(null);
              setActiveWarningId(null);
            }
          });
        }
      }).addTo(map);
      drawn.current[name] = layer;
    }
    const [w, s, e, n] = data.summary.study_bounds;
    map.fitBounds([[s, w], [n, e]], { padding: [25, 25] });
    return () => { map.remove(); mapRef.current = null; drawn.current = {}; };
  }, [data]);

  // Update road layer styling when closedRoads set changes
  useEffect(() => {
    const roadLayer = drawn.current['roads'];
    if (!roadLayer) return;
    roadLayer.setStyle((feature) => {
      const isClosed = feature?.properties?.id && closedRoads.has(feature.properties.id);
      return {
        color: isClosed ? '#ef4444' : colors['roads'],
        weight: isClosed ? 3.5 : 2,
        opacity: isClosed ? 1.0 : 0.75,
        dashArray: isClosed ? '4 4' : undefined,
      };
    });
  }, [closedRoads]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;
    for (const name of names) {
      const layer = drawn.current[name];
      if (layer) enabled[name] ? layer.addTo(map) : map.removeLayer(layer);
    }
  }, [enabled, data]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;
    if (base) {
      const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '' });
      tiles.on('tileerror', () => setTilesFailed(true));
      tiles.addTo(map); tileRef.current = tiles;
    } else if (tileRef.current) { map.removeLayer(tileRef.current); tileRef.current = null; }
    return () => { if (tileRef.current) { map.removeLayer(tileRef.current); tileRef.current = null; } };
  }, [base, data]);

  const fit = () => {
    if (data && mapRef.current) {
      const [w, s, e, n] = data.summary.study_bounds;
      mapRef.current.fitBounds([[s, w], [n, e]], { padding: [25, 25] });
    }
  };

  // Phase 2 Scenario Handlers
  const handleStart = async () => {
    try {
      setBusy(true);
      setActionError(null);
      const res = await postApi<any>('/scenario/start', {
        mode: targetMode,
        seed: 42,
        duration_hours: 72,
        peak_rain_mm_h: 28.5,
      });
      setRunStatus(res.status);
      setRecentRecords([]);
      setClosedRoads(new Set());
      setCurrentRainRate(0.0);
      await fetchWarnings();
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleStep = async () => {
    try {
      setBusy(true);
      setActionError(null);
      const res = await postApi<StepResponse>('/scenario/step');
      setRunStatus({
        is_active: true,
        run_id: res.run_id,
        mode: runStatus?.mode || targetMode,
        step_index: res.step_index,
        current_time: res.current_time,
        is_exhausted: res.is_exhausted,
        display_label: res.display_label,
        steps_completed: res.step_index,
      });
      setRecentRecords(prev => [...res.records, ...prev].slice(0, 50));

      // Extract closures and weather updates from records
      const newClosed = new Set(closedRoads);
      let latestRain = currentRainRate;
      for (const r of res.records) {
        if (r.kind === 'report' && r.payload.reported_status === 'closed' && r.payload.road_id) {
          newClosed.add(r.payload.road_id);
        }
        if (r.kind === 'weather' && r.payload.precipitation_mm != null) {
          latestRain = r.payload.precipitation_mm;
        }
      }
      setClosedRoads(newClosed);
      setCurrentRainRate(latestRain);
      await fetchWarnings();
      if (activeWarningId) {
        await loadEvidenceCard(activeWarningId);
      }
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    try {
      setBusy(true);
      setActionError(null);
      const res = await postApi<any>('/scenario/reset');
      setRunStatus(res.status);
      setRecentRecords([]);
      setClosedRoads(new Set());
      setCurrentRainRate(0.0);
      await fetchWarnings();
      if (activeWarningId) {
        await loadEvidenceCard(activeWarningId);
      }
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    try {
      setBusy(true);
      setActionError(null);
      const res = await postApi<any>('/scenario/stop');
      setRunStatus(res.status);
      setRecentRecords([]);
      setClosedRoads(new Set());
      setCurrentRainRate(0.0);
      await fetchWarnings();
      if (activeWarningId) {
        await loadEvidenceCard(activeWarningId);
      }
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const weatherDate = data && new Date(data.weather.retrieved_at);
  const props = selected?.properties;
  const isSelectedClosed = selected?.kind === 'roads' && props?.id && closedRoads.has(props.id);

  // Weather Telemetry calculation
  const rainSeverity = currentRainRate === 0
    ? { label: 'Clear / Dry', class: 'dry' }
    : currentRainRate < 2.5
    ? { label: 'Light Drizzle', class: 'drizzle' }
    : currentRainRate < 15.0
    ? { label: 'Heavy Rain', class: 'heavy' }
    : { label: 'Flood Cloudburst', class: 'flood' };

  const activeHourIndex = (runStatus?.step_index ?? 0) % (data?.weather.records.length || 24);

  return (
    <div className="shell">
      <aside className="rail" aria-label="Sidebar navigation">
        <div className="brand" title="Flood Command Atlas">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2" />
            <polyline points="2 17 12 22 22 17" />
            <polyline points="2 12 12 17 22 12" />
          </svg>
        </div>
        <span className="vertical">FLOOD COMMAND</span>
        <span className="phase">PHASE 03</span>
      </aside>

      <main>
        {/* Top App Header */}
        <header>
          <div className="header-brand-group">
            <span className="sub-header-title">Assam State Disaster Management Authority</span>
            <h1>Lakhimpur <span>District Command Console</span></h1>
          </div>
          <div className="header-right">
            <span className="status-dot" />
            ONLINE WORKBENCH <span className="divider">/</span> PHASE 3
          </div>
        </header>

        {/* Mandatory Requirement B6: Persistent banner when replaying or simulating */}
        {runStatus && runStatus.is_active && runStatus.mode !== 'live' ? (
          <div className={`scenario-banner ${runStatus.mode}`} role="status">
            <div>
              <strong>{runStatus.mode === 'replay' ? 'HISTORICAL REPLAY' : 'SYNTHETIC SIMULATION'}</strong>
              <span>{runStatus.display_label}</span>
            </div>
            {runStatus.current_time && (
              <span className="banner-clock">
                TIMELINE: {new Date(runStatus.current_time).toISOString().replace('.000Z', 'Z')}
              </span>
            )}
          </div>
        ) : (
          <div className="notice">
            <strong>REFERENCE DATA</strong>
            <span>Road conditions and shelter availability are unverified. This map does not issue safe-route advice.</span>
          </div>
        )}

        {error ? (
          <div role="alert" className="error">
            <h2>Data could not be loaded</h2>
            <p>{error}</p>
            <button onClick={() => window.location.reload()}>Retry</button>
          </div>
        ) : !data ? (
          <div className="loading">Initializing Lakhimpur district telemetry…</div>
        ) : (
          <>
            {/* Streamlined Stats HUD Strip */}
            <section className="stats" aria-label="Dataset summary">
              <div>
                <span>ROAD SEGMENTS</span>
                <strong>{data.summary.counts.roads} <small>connected</small></strong>
              </div>
              <div className="divider">/</div>
              <div>
                <span>SETTLEMENTS</span>
                <strong>{data.summary.counts.settlements} <small>communities</small></strong>
              </div>
              <div className="divider">/</div>
              <div>
                <span>RELIEF CAMPS</span>
                <strong>{data.summary.counts.shelters} <small>DDMA 2025</small></strong>
              </div>
              <div className="divider">/</div>
              <div>
                <span>TERRAIN RESOLUTION</span>
                <strong>{data.summary.terrain.resolution_m}<em>m</em> <small>Copernicus DSM</small></strong>
              </div>
            </section>

            {/* Workbench 3-Pane Layout */}
            <section className="workspace">
              {/* Left Pane: Timeline & Scenario Engine */}
              <div className="left-pane">
                <div className="panel-section">
                  <div className="panel-header-title">
                    <span>Source Controls</span>
                    <small>Phase 3</small>
                  </div>

                  <div className="mode-segmented-control" aria-label="Simulation source mode">
                    <button
                      className={`mode-btn ${targetMode === 'scenario' ? 'active' : ''}`}
                      onClick={() => setTargetMode('scenario')}
                      disabled={busy || (runStatus?.is_active ?? false)}
                    >
                      Scenario
                    </button>
                    <button
                      className={`mode-btn ${targetMode === 'replay' ? 'active' : ''}`}
                      onClick={() => setTargetMode('replay')}
                      disabled={busy || (runStatus?.is_active ?? false)}
                    >
                      2024 Replay
                    </button>
                    <a href="/">Live Overview</a>
                  </div>

                  {actionError && (
                    <div style={{ color: 'var(--color-danger)', fontSize: 11, marginBottom: 8 }}>
                      {actionError}
                    </div>
                  )}

                  <div className="playback-actions">
                    {!runStatus?.is_active ? (
                      <button className="btn-primary" onClick={handleStart} disabled={busy}>
                        Start {targetMode}
                      </button>
                    ) : (
                      <>
                        <button className="btn-step" onClick={handleStep} disabled={busy || runStatus.is_exhausted}>
                          Step +1h
                        </button>
                        <button className="btn-secondary" onClick={handleReset} disabled={busy}>
                          ↺ Reset
                        </button>
                        <button className="btn-secondary" onClick={handleStop} disabled={busy}>
                          ⏹ Stop
                        </button>
                      </>
                    )}
                  </div>

                  {runStatus?.is_active && (
                    <div className="scenario-status-box">
                      <div className="status-row">
                        <span>Mode</span>
                        <strong>{runStatus.mode?.toUpperCase()}</strong>
                      </div>
                      <div className="status-row">
                        <span>Step Index</span>
                        <strong>{runStatus.step_index} {runStatus.is_exhausted ? '(Exhausted)' : ''}</strong>
                      </div>
                      {runStatus.current_time && (
                        <div className="status-row">
                          <span>Timeline</span>
                          <strong>{new Date(runStatus.current_time).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })} IST</strong>
                        </div>
                      )}
                      {closedRoads.size > 0 && (
                        <div className="status-row" style={{ color: 'var(--color-danger)' }}>
                          <span>Closed Roads</span>
                          <strong>{closedRoads.size} segments</strong>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="panel-header-title" style={{ marginTop: 6, marginBottom: 6 }}>
                    <span>Incident & Telemetry Feed</span>
                    <small>{recentRecords.length} records</small>
                  </div>
                  <div className="event-feed">
                    {recentRecords.length === 0 ? (
                      <div style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: '24px 0', fontSize: 11 }}>
                        Stream idle. Step forward to ingest timeline records.
                      </div>
                    ) : (
                      recentRecords.slice(0, 15).map((rec, i) => (
                        <div key={i} className="feed-item">
                          <div className="feed-meta-row">
                            <span className={`feed-badge ${rec.kind}`}>
                              {rec.kind === 'resource_change' ? 'RESOURCE' : rec.kind.toUpperCase()}
                            </span>
                            <span className="feed-time">
                              {new Date(rec.event_time).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <div className="feed-content">
                            {rec.kind === 'report' ? (
                              <span>
                                <strong style={{ color: rec.payload.reported_status === 'closed' ? 'var(--color-danger)' : 'var(--color-success)' }}>
                                  [{rec.payload.reported_status?.toUpperCase()}]
                                </strong>{' '}
                                {rec.payload.raw_text}
                              </span>
                            ) : rec.kind === 'resource_change' ? (
                              <span>
                                <strong>[{rec.payload.change_type?.toUpperCase()}]</strong>{' '}
                                {rec.payload.settlement_name || rec.payload.shelter_name}
                              </span>
                            ) : (
                              <span>
                                <strong>[{rec.payload.precipitation_mm}mm rain]</strong> at {rec.entity_id}
                              </span>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Center Pane: Operational Field Map */}
              <div className="center-pane">
                <div className="map-header">
                  <div>
                    <h2>North Lakhimpur–Kadam corridor</h2>
                  </div>
                  <button onClick={fit} title="Reset map bounds">
                    ↗ Reset view
                  </button>
                </div>

                <div
                  ref={container}
                  className="map"
                  aria-label="Interactive map of Lakhimpur roads, settlements and relief camps"
                />

                <div className="map-footer">
                  <span>
                    <i className="tiny-dot" />
                    Local vector layers · offline-ready
                    {closedRoads.size > 0 ? ` · ${closedRoads.size} simulated closed segments` : ''}
                  </span>
                  <label>
                    <input type="checkbox" checked={base} onChange={e => setBase(e.target.checked)} />
                    Online basemap
                  </label>
                </div>
                {tilesFailed && base && (
                  <div role="status" className="tile-note">
                    Online basemap is unavailable. Acquired local layers remain visible.
                  </div>
                )}
              </div>

              {/* Right Pane: Telemetry & Entity Inspector */}
              <div className="right-pane">
                {/* Weather Telemetry Monitor */}
                <div className="panel-section weather-card">
                  <div className="weather-monitor-header">
                    <h2>Hourly Rainfall (GFS)</h2>
                    <span className="weather-provider-tag">
                      {runStatus?.is_active ? 'ACTIVE STREAM' : 'CACHED GFS'}
                    </span>
                  </div>

                  <div className="rainfall-gauge-box">
                    <div>
                      <div className="gauge-rate">
                        {currentRainRate.toFixed(1)} <span>mm/h</span>
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                        Current Intensity
                      </div>
                    </div>
                    <div className={`gauge-badge ${rainSeverity.class}`}>
                      {rainSeverity.label}
                    </div>
                  </div>

                  <div className="detail-row">
                    <span>Provider</span>
                    <strong>{data.weather.provider}</strong>
                  </div>
                  <div className="detail-row" style={{ marginBottom: 6 }}>
                    <span>Acquired (IST)</span>
                    <strong>
                      {weatherDate?.toLocaleString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </strong>
                  </div>

                  <div className="rain-bars" aria-label="First 24 hourly precipitation values in the acquired weather snapshot">
                    {data.weather.records.slice(0, 24).map((r, i) => (
                      <span
                        key={i}
                        className={i === activeHourIndex && runStatus?.is_active ? 'active' : ''}
                        title={`Hour ${i} (${r.valid_at.slice(11, 16)}): ${r.precipitation_mm ?? 'missing'} mm`}
                        style={{ height: `${Math.max(4, Math.min(40, (r.precipitation_mm ?? 0) * 7 + 4))}px` }}
                      />
                    ))}
                  </div>

                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>
                    Sample: North Lakhimpur corridor. Weather for all {data.summary.counts.settlements} settlements is cached.
                  </div>
                </div>

                {/* Layer Visibility Controls */}
                <div className="panel-section layer-card">
                  <div className="panel-header-title">
                    <span>Map Layers</span>
                    <small>5 Active</small>
                  </div>
                  <div className="layer-grid">
                    {names.map(n => (
                      <label key={n}>
                        <input
                          type="checkbox"
                          checked={enabled[n]}
                          onChange={e => setEnabled({ ...enabled, [n]: e.target.checked })}
                        />
                        <i style={{ background: colors[n] }} />
                        <span>{n === 'shelters' ? 'Published relief camps' : n[0].toUpperCase() + n.slice(1)}</span>
                        <b>{data.summary.counts[n]}</b>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Ranked Flood Warnings (Phase 3 Requirement B2, B3) */}
                <div className="panel-section warnings-card">
                  <div className="panel-header-title">
                    <span>Ranked Flood Warnings</span>
                    <small>{warnings ? `${warnings.active_warnings.length} Evaluated` : 'OFFLINE'}</small>
                  </div>

                  <div className="severity-stats-strip">
                    <div className="severity-pill critical">
                      CRIT {warnings?.severity_counts.critical || 0}
                    </div>
                    <div className="severity-pill high">
                      HIGH {warnings?.severity_counts.high || 0}
                    </div>
                    <div className="severity-pill moderate">
                      MOD {warnings?.severity_counts.moderate || 0}
                    </div>
                    <div className="severity-pill advisory">
                      ADV {warnings?.severity_counts.advisory || 0}
                    </div>
                  </div>

                  <div className="warning-list" role="list" aria-label="Ranked flood alerts">
                    {!warnings || warnings.active_warnings.length === 0 ? (
                      <div style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0', fontSize: 11 }}>
                        No active warnings. System running baseline monitoring.
                      </div>
                    ) : (
                      warnings.active_warnings.slice(0, 15).map((w) => {
                        const isSelected = activeWarningId === w.entity_id;
                        return (
                          <div
                            key={w.entity_id}
                            role="listitem"
                            className={`warning-item ${isSelected ? 'active' : ''}`}
                            onClick={() => {
                              loadEvidenceCard(w.entity_id);
                              setSelected({
                                kind: w.entity_type === 'settlement' ? 'settlements' : 'roads',
                                properties: { id: w.entity_id, name: w.entity_name },
                              });
                            }}
                          >
                            <div className="warning-title-row">
                              <div className="warning-title-group">
                                <span className="warning-rank-num">#{w.rank}</span>
                                <span className="warning-name">{w.entity_name}</span>
                                <span style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                                  {w.entity_type === 'settlement' ? 'Settlement' : 'Road'}
                                </span>
                              </div>
                              <span className={`warning-score-badge ${w.severity}`}>
                                {w.risk_score.toFixed(1)}
                              </span>
                            </div>
                            <div className="warning-meta-row">
                              <span style={{ maxWidth: '170px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {w.primary_driver}
                              </span>
                              <span className={`rank-delta-pill ${w.rank_delta > 0 ? 'up' : w.rank_delta < 0 ? 'down' : 'same'}`}>
                                {w.rank_delta > 0 ? `▲ +${w.rank_delta}` : w.rank_delta < 0 ? `▼ ${w.rank_delta}` : '—'}
                              </span>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Entity Inspector & Evidence Card (Phase 3 Requirement B4) */}
                <div className="panel-section inspect-card">
                  <div className="panel-header-title">
                    <span>Entity Inspector</span>
                    <small>{selected ? selected.kind.toUpperCase() : 'NO SELECTION'}</small>
                  </div>
                  <h2>{props?.name || props?.id || 'Select feature on map'}</h2>

                  {!props ? (
                    <p style={{ color: 'var(--text-tertiary)' }}>
                      Select any road segment, community, or relief camp on the map to inspect its real terrain, source, and limits.
                    </p>
                  ) : (
                    <>
                      <div className="source-label">{props.provenance?.label || 'Verified Source'}</div>

                      {selected?.kind === 'shelters' && (
                        <>
                          <div className="detail-row">
                            <span>Published capacity (2025)</span>
                            <strong>2025 PUBLISHED INVENTORY: {props.published_capacity}</strong>
                          </div>
                          <div className="detail-row">
                            <span>Current availability</span>
                            <strong>Unknown</strong>
                          </div>
                          <p style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                            Document-listed coordinates · DDMA plan, page 48. Not field-verified.
                          </p>
                        </>
                      )}

                      {props.elevation_m != null && (
                        <div className="detail-row">
                          <span>Surface elevation</span>
                          <strong>{props.elevation_m} m</strong>
                        </div>
                      )}
                      {props.slope_degrees != null && (
                        <div className="detail-row">
                          <span>Local surface slope</span>
                          <strong>{props.slope_degrees}°</strong>
                        </div>
                      )}
                      {props.distance_to_river_m != null && (
                        <div className="detail-row">
                          <span>Nearest mapped river</span>
                          <strong>{Math.round(props.distance_to_river_m)} m</strong>
                        </div>
                      )}
                      {props.distance_to_road_m != null && (
                        <div className="detail-row">
                          <span>Nearest study road</span>
                          <strong>{props.distance_to_road_m} m</strong>
                        </div>
                      )}
                      {props.length_m && (
                        <div className="detail-row">
                          <span>Segment length</span>
                          <strong>{Math.round(props.length_m)} m</strong>
                        </div>
                      )}
                      {props.status && (
                        <div className="detail-row">
                          <span>Road status</span>
                          <strong style={{ color: isSelectedClosed ? 'var(--color-danger)' : 'inherit' }}>
                            {isSelectedClosed ? 'Reported Closed (Simulated)' : 'Unknown'}
                          </strong>
                        </div>
                      )}
                      {selected?.kind === 'settlements' && (
                        <p style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                          Population unknown. Proximity to a road does not verify last-mile access.
                        </p>
                      )}

                      {/* Explainable Evidence Card */}
                      {selectedCard && (
                        <div className="evidence-card-box" data-testid="evidence-card">
                          <div className="evidence-header">
                            <div>
                              <span style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                EXPLAINABLE EVIDENCE CARD
                              </span>
                              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                                {selectedCard.entity_name}
                              </div>
                            </div>
                            <span className={`evidence-score-pill ${selectedCard.severity}`}>
                              {selectedCard.risk_score.toFixed(1)} / 100
                            </span>
                          </div>

                          <div className="evidence-why-callout">
                            <strong>Primary Driver & Reasoning</strong>
                            {selectedCard.why}
                          </div>

                          {selectedCard.rerank_reason && selectedCard.rank_delta !== 0 && (
                            <div style={{ fontSize: 11, color: 'var(--color-warning)', background: 'rgba(245, 158, 11, 0.08)', padding: '5px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                              <strong style={{ fontSize: 9, textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>Rank Shift Rationale</strong>
                              {selectedCard.rerank_reason}
                            </div>
                          )}

                          <div className="detail-row">
                            <span>Confidence</span>
                            <strong style={{ color: selectedCard.confidence === 'high' ? 'var(--color-success)' : selectedCard.confidence === 'medium' ? 'var(--color-warning)' : 'var(--text-tertiary)' }}>
                              {selectedCard.confidence.toUpperCase()}
                            </strong>
                          </div>
                          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 4, lineHeight: 1.3 }}>
                            {selectedCard.confidence_reason}
                          </div>

                          <div className="detail-row">
                            <span>Estimated Lead Time</span>
                            <strong>
                              {selectedCard.lead_time_hours != null
                                ? `${selectedCard.lead_time_hours.toFixed(1)} hrs`
                                : 'Immediate / Ongoing'}
                            </strong>
                          </div>

                          <div className="detail-row">
                            <span>Newest Data Age</span>
                            <strong>{selectedCard.data_age_seconds}s ago</strong>
                          </div>

                          <div className="evidence-metrics-grid">
                            <div className="evidence-metric-cell">
                              <span>1h Rain</span>
                              <strong>{selectedCard.factors.recent_rain_1h_mm.toFixed(1)} mm</strong>
                            </div>
                            <div className="evidence-metric-cell">
                              <span>3h Rain</span>
                              <strong>{selectedCard.factors.recent_rain_3h_mm.toFixed(1)} mm</strong>
                            </div>
                            <div className="evidence-metric-cell">
                              <span>6h Rain</span>
                              <strong>{selectedCard.factors.recent_rain_6h_mm.toFixed(1)} mm</strong>
                            </div>
                            <div className="evidence-metric-cell">
                              <span>Soil Saturation</span>
                              <strong>{selectedCard.factors.ground_saturation_api_mm.toFixed(0)} mm</strong>
                            </div>
                            <div className="evidence-metric-cell">
                              <span>Elevation / Slope</span>
                              <strong>{selectedCard.factors.elevation_m.toFixed(0)}m / {selectedCard.factors.slope_degrees.toFixed(1)}°</strong>
                            </div>
                            <div className="evidence-metric-cell">
                              <span>River Proximity</span>
                              <strong>{Math.round(selectedCard.factors.distance_to_river_m)} m</strong>
                            </div>
                          </div>

                          <div className="evidence-disclosure">
                            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Uncertainty & Sensor Limits: </span>
                            {selectedCard.uncertainty_disclosure}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </section>

            <footer>
              <span>Warning in. Action out. With proof.</span>
              <span>NWIC boundary · OSM roads · GeoNames · Copernicus terrain · DDMA inventory</span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

const view = new URLSearchParams(location.search).get('view');
const isMobilePath = location.pathname.includes('/team-mobile');
createRoot(document.getElementById('root')!).render(
  view === 'roads' ? <RoadEstimates /> : view === 'team' || isMobilePath ? <TeamApp /> : <LiveOverview />
);
