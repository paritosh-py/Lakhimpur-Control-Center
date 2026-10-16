import copy
import hashlib
import json
import math
from threading import RLock

from engine.clock import LiveClock
from engine.config import ROOT
from engine.ingest.source import SourceRecord
from engine.warnings.assessment import assess, RULES
from backend.app.services.live_weather import timestamp


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r * c


class AssessmentService:
    def __init__(self, clock=None, report_store=None):
        self.clock = clock or LiveClock()
        self.report_store = report_store
        geo_data = json.loads((ROOT / 'data/processed/settlements.geojson').read_text(encoding='utf-8'))
        self.settlements = [f['properties'] for f in geo_data['features']]
        self.settlement_coords = {}
        for f in geo_data['features']:
            sid = f.get('properties', {}).get('id')
            coords = f.get('geometry', {}).get('coordinates', [])
            if sid and len(coords) >= 2:
                self.settlement_coords[sid] = (float(coords[1]), float(coords[0]))
        self.cache = {}
        self.lock = RLock()

    def _citizen_report_records(self, decision, context: str = 'live', run_id: str | None = None) -> list[SourceRecord]:
        if not self.report_store:
            try:
                from backend.app.services.reports import ReportStore
                self.report_store = ReportStore()
            except Exception:
                return []

        contexts = {context}
        if run_id:
            contexts.add(run_id)
        if context in ('exercise', 'scenario') or run_id:
            contexts.update(['exercise', 'scenario', 'live'])

        raw_reports = []
        seen = set()
        for ctx in contexts:
            try:
                for rep in self.report_store.list_reports(context=ctx):
                    if rep['id'] not in seen:
                        seen.add(rep['id'])
                        raw_reports.append(rep)
            except Exception:
                pass

        records = []
        for rep in raw_reports:
            if rep.get('status') in ('closed', 'resolved'):
                continue
            settlement_id = rep.get('settlement_id')
            if not settlement_id:
                continue

            rep_lat = rep.get('latitude')
            rep_lon = rep.get('longitude')

            sender_loc_type = 'on_site'
            location_mismatch = False
            dist_km = 0.0
            sender_loc_name = rep.get('settlement_name') or 'Assam'

            if rep_lat is not None and rep_lon is not None and settlement_id in self.settlement_coords:
                s_lat, s_lon = self.settlement_coords[settlement_id]
                dist_km = haversine_km(rep_lat, rep_lon, s_lat, s_lon)
                if dist_km > 35.0:
                    sender_loc_type = 'location_mismatch'
                    location_mismatch = True
                    if 18.0 <= rep_lat <= 19.5 and 73.0 <= rep_lon <= 74.5:
                        sender_loc_name = 'Pune, Maharashtra'
                    else:
                        sender_loc_name = f'Remote ({round(dist_km)} km away)'
                elif dist_km > 5.0:
                    sender_loc_type = 'nearby'
                else:
                    sender_loc_type = 'on_site'

            inc_type = str(rep.get('incident_type') or '').lower()
            road_stat = str(rep.get('road_status') or '').lower()
            if road_stat in ('blocked', 'impassable') or inc_type == 'road_closure':
                rep_status = 'closed'
            elif inc_type in ('rescue_sos', 'medical') or (rep.get('water_depth_cm') or 0) > 0:
                rep_status = 'flooded'
            else:
                rep_status = 'need_rescue'

            payload = {
                'settlement_id': settlement_id,
                'road_id': None,
                'sender_id': rep.get('device_id') or rep.get('sender_name') or 'citizen',
                'sender_location_type': sender_loc_type,
                'location_mismatch': location_mismatch,
                'mismatch_distance_km': dist_km,
                'sender_location_name': sender_loc_name,
                'reported_status': rep_status,
                'raw_text': rep.get('description') or f"Report: {inc_type} at {settlement_id}",
                'report_id': rep['id'],
                'device_id': rep.get('device_id'),
            }

            rec = SourceRecord(
                kind='report',
                entity_id=rep['id'],
                event_time=decision,
                available_at=decision,
                payload=payload,
                source='live' if context == 'live' else 'simulated',
                provider='Citizen Mobile App',
                replayed_at=self.clock.now() if context != 'live' else None,
            )
            records.append(rec)
        return records

    def evaluate(self, records, decision, key, unavailable=False):
        # Cache by actual evidence/time: repeated GETs cannot consume rank changes.
        signature = hashlib.sha256(repr((records, decision, unavailable)).encode()).hexdigest()
        with self.lock:
            old = self.cache.get(key)
            if old and old[0] == signature: return copy.deepcopy(old[1])
            cards = assess(self.settlements, records, decision, unavailable=unavailable)
            previous = {c['settlement_id']: c for c in old[1]} if old else {}
            for c in cards:
                p = previous.get(c['settlement_id'])
                c['previous_rank'] = p['rank'] if p else None
                c['rank_delta'] = p['rank'] - c['rank'] if p else 0
                if c.get('reports', {}).get('location_mismatch') and p and (p['rank'] < c['rank'] or (p['score'] or 0) > (c['score'] or 0)):
                    c['change_reason'] = 'Ground report location mismatch (Pune vs Assam) reduced confidence and priority.'
                else:
                    c['change_reason'] = ('Rainfall, its age or reports changed the assessment.' if p and
                        (p['severity'], p['score'], p['rank']) != (c['severity'], c['score'], c['rank']) else None)
                if p and (p['severity'], p['score'], p['rank']) == (c['severity'], c['score'], c['rank']):
                    for field in ('previous_rank', 'rank_delta', 'change_reason'): c[field] = p[field]
            if len(self.cache) > 20: self.cache.clear()
            self.cache[key] = (signature, copy.deepcopy(cards))
            return cards

    def live(self, snapshot):
        records = []
        retrieved = timestamp(snapshot['retrieved_at']) if snapshot['retrieved_at'] else None
        decision = timestamp(snapshot['checked_at'])
        for row in snapshot['settlements']:
            if retrieved and row['valid_at'] and row.get('interval_seconds'):
                records.append(SourceRecord('weather', row['settlement_id'], timestamp(row['valid_at']), retrieved,
                    {'precipitation_mm': row['values']['precipitation'], 'interval_minutes': row['interval_seconds']/60,
                     'measurement': 'model_estimate'}, 'live', snapshot['provider']))
            for h in row.get('hourly_history', []):
                if retrieved is None: continue
                records.append(SourceRecord('weather', row['settlement_id'], timestamp(h['valid_at']), retrieved,
                    {'precipitation_mm': h['precipitation_mm'], 'interval_minutes': 60,
                     'measurement': 'model_estimate', 'grid': [row['grid_latitude'], row['grid_longitude']]},
                    'live', snapshot['provider']))
        if not snapshot.get('error'):
            citizen_records = self._citizen_report_records(decision, context='live')
            records.extend(citizen_records)
        snapshot['assessments'] = self.evaluate(records, decision, 'live', bool(snapshot['error']))
        snapshot['rules'] = RULES
        return snapshot

    def replay(self, run):
        decision = run.current_time or self.clock.now()
        mode = 'replay' if run.mode and run.mode.value == 'replay' else 'simulated'
        records = list(run.records)
        # Only simulated synthetic exercises ingest interactive citizen reports
        if mode == 'simulated':
            citizen_records = self._citizen_report_records(decision, context='exercise', run_id=run.run_id)
            records.extend(citizen_records)
        cards = self.evaluate(records, decision, run.run_id or 'idle')
        rows = []
        for c in cards:
            rain = c['rainfall']['rain_mm']['1']
            rows.append({'settlement_id': c['settlement_id'], 'name': c['name'],
                         'status': 'current' if rain is not None else 'unavailable',
                         'rain_status': 'unknown' if rain is None else 'raining' if rain > 0 else 'no_rain',
                         'condition': 'Rainfall recorded' if rain and rain > 0 else 'No rainfall recorded' if rain == 0 else 'Conditions unavailable',
                         'valid_at': c['rainfall']['latest_at'], 'interval_seconds': 3600,
                         'grid_latitude': (c['rainfall']['grid'] or [None, None])[0],
                         'grid_longitude': (c['rainfall']['grid'] or [None, None])[1],
                         'values': {'rain': rain, 'showers': 0 if rain is not None else None,
                                    'temperature_2m': None, 'cloud_cover': None, 'relative_humidity_2m': None, 'wind_speed_10m': None}})
        return {'mode': mode, 'provider': 'Open-Meteo / ERA5' if mode == 'replay' else 'Seeded synthetic generator',
                'checked_at': decision.isoformat(), 'retrieved_at': None, 'next_refresh_at': None,
                'replayed_at': self.clock.now().isoformat(), 'error': None, 'settlements': rows,
                'assessments': cards, 'rules': RULES, 'run': run.status(), 'display_label': run.display_label,
                'grid_cells': len({tuple(c['rainfall']['grid']) for c in cards if c['rainfall']['grid']}),
                'counts': {'current': sum(r['status'] == 'current' for r in rows), 'stale': 0,
                           'unavailable': sum(r['status'] == 'unavailable' for r in rows)},
                'raining_count': sum(r['rain_status'] == 'raining' for r in rows),
                'limitations': 'Retrospective weather playback: original operational availability unknown; not a forecast issued in 2024.' if mode == 'replay' else 'All rain and reports are generated; not a reconstruction of actual settlement impacts.'}
