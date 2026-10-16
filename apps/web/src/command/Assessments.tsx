export type Assessment = {
  settlement_id: string; name: string; severity: string; score: number | null; rank: number;
  confidence: string; confidence_reason: string; evidence_strength: number; why: string;
  affected: boolean; data_status: string; rank_delta: number; change_reason: string | null;
  terrain: { level: string; factor: number; elevation_m: number | null; slope_degrees: number | null; distance_to_river_m: number | null; basis: string };
  rainfall: { rain_mm: Record<string, number | null>; coverage_hours: Record<string, number>; wet_duration_hours: number | null; duration_at_least: boolean; window_end: string; provider: string | null; grid: number[] | null; measurement: string | null; latest_interval_mm: number | null; latest_interval_minutes: number | null; interval_is_fresh: boolean };
  reports: { message: string; conflict: boolean; expired_count: number; records: { id: string; raw_text: string; event_time: string; available_at: string; source: string; status: string }[] };
};
export const severityColor = (s?: string) => s === 'critical' ? '#ff8c85' : s === 'high' ? '#f9b178' : s === 'watch' ? '#f4d37c' : '#172322';
export const severityLabel = (s: string) => ({ none: 'No elevated signal', unknown: 'Insufficient data', watch: 'Flood watch', high: 'High attention', critical: 'Critical attention' }[s] || s);
const date = (s: string) => new Date(s).toLocaleString('en-IN', {timeZone:'Asia/Kolkata'}) + ' IST';

export function AssessmentEvidence({ card }: { card: Assessment }) {
  return <div className="assessment-evidence">
    <p><strong className={`assessment-severity severity-${card.severity.toLowerCase()}`}>{severityLabel(card.severity)}</strong> · {card.confidence} confidence</p>
    <p>{card.why}</p>
    {card.rainfall.interval_is_fresh && card.rainfall.latest_interval_mm != null && <p>Latest interval: {card.rainfall.latest_interval_mm.toFixed(1)} mm / {card.rainfall.latest_interval_minutes} min. {card.severity === 'none' && card.rainfall.latest_interval_mm > 0 ? 'Rainfall observation; no elevated flood signal.' : ''}</p>}
    <dl className="rain-windows">{Object.entries(card.rainfall.rain_mm).map(([h, mm]) => <div key={h}><dt>{h} h precipitation</dt><dd>{mm == null ? 'Unknown' : `${mm.toFixed(1)} mm`}<small>{card.rainfall.coverage_hours[h]}/{h} hours available</small></dd></div>)}</dl>
    <p>Intervals end at {date(card.rainfall.window_end)}. Wet duration: {card.rainfall.wet_duration_hours == null ? 'unknown' : `${card.rainfall.duration_at_least ? 'at least ' : ''}${card.rainfall.wet_duration_hours} h`}.</p>
    <details><summary>Evidence, terrain & confidence</summary>
      <p>{card.confidence_reason} Evidence strength: {card.evidence_strength}/100 (rule-based index, not probability).</p>
      <p>Terrain susceptibility: {card.terrain.level} · factor {card.terrain.factor}. Surface elevation {card.terrain.elevation_m ?? 'unknown'} m; slope {card.terrain.slope_degrees ?? 'unknown'}°; mapped river distance {card.terrain.distance_to_river_m ?? 'unknown'} m.</p>
      <p>{card.terrain.basis}</p><p>{card.rainfall.provider || 'No weather source available'} · {card.rainfall.measurement || 'Unknown measurement'} · grid {card.rainfall.grid?.join(', ') || 'unknown'}</p>
      <p>{card.reports.message}</p>{card.reports.conflict && <p className="live-error">Conflicting reports: verify before acting.</p>}
      {card.reports.records.map(r => <blockquote key={r.id}><strong>{r.source} · {r.status}</strong><p>{r.raw_text}</p><small>Occurred {date(r.event_time)} · received {date(r.available_at)}</small></blockquote>)}
    </details>
    {card.change_reason && <p>{card.change_reason} Priority change: {card.rank_delta > 0 ? '+' : ''}{card.rank_delta}.</p>}
  </div>;
}

export function WarningsPage({ cards, select, failed, onAssign }: { cards: Assessment[]; select: (id: string) => void; failed: boolean; onAssign?: (id:string)=>void }) {
  const affected = cards.filter(c => c.affected);
  return <section className="warnings-page"><h2>Settlement warnings</h2><p>Ranked by assessed severity, then score. Rain-only observations are listed without being called disasters. Confidence measures evidence support separately from severity.</p>
    {failed ? <p className="live-error">Connection lost. Assessments cannot be confirmed current.</p> : !cards.length ? <p>Assessments will appear when the selected source is loaded.</p> : !affected.length ? <p className="assessment-empty">No affected settlements in the available evidence. {cards.filter(c => c.severity === 'unknown').length} assessments have insufficient data; this is not an all-clear.</p> : affected.map(c => <article className="warning-row" key={c.settlement_id} data-settlement={c.settlement_id}><div className="warning-title"><h3>{c.name}</h3><span>Priority {c.rank}</span><button onClick={() => select(c.settlement_id)}>Show on map</button>{onAssign&&<button onClick={()=>onAssign(c.settlement_id)}>Assign team</button>}</div><AssessmentEvidence card={c}/></article>)}
    <details className="assessment-register"><summary>All {cards.length} settlement assessments</summary><ul>{cards.map(c => <li key={c.settlement_id}><button onClick={() => select(c.settlement_id)}>{c.name}</button> {severityLabel(c.severity)} · {c.confidence} confidence</li>)}</ul></details>
  </section>;
}
