import {useEffect, useRef, useState} from 'react';
import './roads.css';

type Prediction = {probability_unusable:number; risk_level:'LOW'|'MODERATE'|'HIGH'; road_status:string; data_quality_status:string};
type Road = {road_id:string;name:string;road_type:string|null;length_m:number|null;recorded_road_status:string;prediction:Prediction|null};
type Snapshot = {mode:string;model_version:string;eta_minutes:number;fetched_at:string;weather_retrieved_at:string;rainfall_completion_example:string;matched_count:number;prediction_count:number;road_count:number;unmatched_prediction_count:number;roads:Road[]};
const time = (value:string) => new Date(value).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})+' IST';
const percent = (p:number) => (p*100).toFixed(4)+'%';

export default function RoadEstimates(){
  const [eta,setEta]=useState(60),[revision,setRevision]=useState(0),[data,setData]=useState<Snapshot|null>(null);
  const [error,setError]=useState(''),[loading,setLoading]=useState(true),[search,setSearch]=useState(''),[filter,setFilter]=useState('ALL'),[selected,setSelected]=useState('');
  const detail = useRef<HTMLElement>(null);
  useEffect(()=>{if(selected)detail.current?.scrollIntoView({block:"start"});},[selected]);
  useEffect(()=>{
    const controller=new AbortController();let active=true;
    setData(null);setError('');setLoading(true);
    const timeout=setTimeout(()=>controller.abort(),15000);
    (async()=>{try{
      const response=await fetch('/api/ml/roads?eta='+eta,{signal:controller.signal,cache:'no-store'});
      const body=await response.json();
      if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:'Unable to load road estimates. Retry the connection.');
      if(active)setData(body);
    }catch(e){if(active)setError(e instanceof Error&&e.name==='AbortError'?'Connection timed out. Check Wi-Fi and retry.':e instanceof Error?e.message:'Unable to reach the command server. Retry the connection.');}
    finally{clearTimeout(timeout);if(active)setLoading(false);}})();
    return()=>{active=false;clearTimeout(timeout);controller.abort();};
  },[eta,revision]);
  const current=data?.eta_minutes===eta?data:null;
  const rows=(current?.roads||[]).filter(r=>(filter==='ALL'||(r.prediction?.risk_level||'UNKNOWN')===filter)&&`${r.name} ${r.road_id} ${r.road_type}`.toLowerCase().includes(search.toLowerCase()));
  const road=current?.roads.find(r=>r.road_id===selected);
  return <div className="road-app">
    <header className="road-header"><h1>Road access at arrival</h1><p>Rescue Team App · Lakhimpur</p><a href={'?view=team'+location.hash}>Team assignments</a></header>
    <aside className="road-disclosure"><strong>Saved-weather demo · Not live</strong><span>Simulation-trained estimates. Low risk does not confirm an open road.</span></aside>
    <main>
      <section className="road-controls" aria-label="Prediction controls">
        <label>Intended travel time<select aria-label="Intended travel time" value={eta} onChange={e=>setEta(Number(e.target.value))}>{[30,60,120].map(n=><option value={n} key={n}>{n} minutes to arrival</option>)}</select></label>
        <button disabled={loading} onClick={()=>setRevision(v=>v+1)}>Refresh estimates</button>
      </section>
      <p className="road-context">Choose the model’s arrival horizon. This is not a calculated route or a forecast from today’s weather. Exercise playback does not change this saved snapshot.</p>
      {loading&&<p role="status" className="road-message">Loading {eta}-minute estimates…</p>}
      {error&&<div role="alert" className="road-error"><h2>Estimates unavailable</h2><p>{error}</p><button onClick={()=>setRevision(v=>v+1)}>Retry connection</button></div>}
      {current&&<>
        <details className="road-provenance"><summary>Snapshot & model details</summary><dl><dt>Weather retrieved</dt><dd>{time(current.weather_retrieved_at)} (reported by model owner)</dd><dt>Example rainfall completion</dt><dd>{time(current.rainfall_completion_example)}; per-road times not supplied</dd><dt>API fetched</dt><dd>{time(current.fetched_at)}; this does not refresh the weather</dd><dt>Model</dt><dd>{current.model_version}</dd><dt>Rainfall features</dt><dd>Previous 1, 3, 6, 24 and 72 hours: rolling accumulated totals in mm.</dd><dt>Model limitations</dt><dd>Trained on simulated road usability; not independently calibrated for real-world use. Input warnings require verification, not closure.</dd></dl></details>
        <section className="road-browser" aria-label="Road estimates">
          <h2>Study roads <span>{current.matched_count} / {current.road_count} matched</span></h2>
          <p>All study segments; not filtered to your assignment or a navigation route.</p>
          {!!current.unmatched_prediction_count&&<p role="status">{current.unmatched_prediction_count} predictions have no matching study road.</p>}
          <label>Search roads<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Road name or segment ID"/></label>
          <label>Risk band<select aria-label="Risk band" value={filter} onChange={e=>setFilter(e.target.value)}><option value="ALL">All estimates</option><option value="LOW">Low · below 40%</option><option value="MODERATE">Moderate · 40% to below 70%</option><option value="HIGH">High · 70% and above</option><option value="UNKNOWN">Unknown · no estimate</option></select></label>
          {road&&<section ref={detail} className="road-selected" aria-label="Selected road"><div className="road-detail-heading"><h3>{road.name}</h3><button onClick={()=>setSelected('')}>Close details</button></div><code>{road.road_id}</code><dl><dt>Estimated unusable at arrival</dt><dd>{road.prediction?percent(road.prediction.probability_unusable):'Unknown'} · {eta} minutes</dd><dt>Risk band</dt><dd>{road.prediction?.risk_level||'UNKNOWN'}</dd><dt>Recorded road status</dt><dd>{road.recorded_road_status} (reference dataset)</dd><dt>Model-reported road status</dt><dd>{road.prediction?.road_status||'unknown'} (not independently verified)</dd><dt>Input quality</dt><dd>{road.prediction?.data_quality_status||'No prediction'}{road.prediction?.data_quality_status==='CHECK_REQUIRED'&&' — Missing, uncertain or distribution-shifted inputs; verify on the ground.'}</dd><dt>Road segment</dt><dd>{road.road_type||'Type unknown'} · {road.length_m===null?'Length unknown':road.length_m+' m'}</dd></dl><p>Confirmed closures remain binding. A model estimate cannot reopen a road.</p></section>}
          <p aria-live="polite">{rows.length} road segments{rows.length>100?' · showing first 100; search to narrow':''}</p>
          <ul className="road-list">{rows.slice(0,100).map(r=><li key={r.road_id}><button aria-pressed={r.road_id===selected} onClick={()=>setSelected(r.road_id)}><span className="road-name">{r.name}<small>{r.road_id}</small></span><span className={'road-band band-'+(r.prediction?.risk_level||'UNKNOWN').toLowerCase()}>{r.prediction?.risk_level||'UNKNOWN'}<small>{r.prediction?percent(r.prediction.probability_unusable):'No estimate'}</small></span></button></li>)}</ul>
          {!rows.length&&<p>No road segments match these filters.</p>}
        </section>
      </>}
    </main>
  </div>;
}
