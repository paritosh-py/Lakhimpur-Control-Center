"""Pure settlement screening. Provenance never changes the decision rules.

Rainfall is an interval-ending amount, never multiplied to invent missing windows.
These configurable heuristics are not calibrated flood probabilities.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta

from engine.config import ROOT
from engine.ingest.source import SourceRecord

RULES = json.loads((ROOT / 'config/flood_assessment.json').read_text(encoding='utf-8'))
WINDOWS = (1, 3, 6, 24, 72)


def rain_features(records: list[SourceRecord], settlement_id: str, decision: datetime) -> dict:
    # Most recently available revision wins for each interval; duplicates cannot add rain.
    hourly = {}
    latest_interval = None
    for r in sorted(records, key=lambda x: x.available_at):
        if r.kind != 'weather' or r.available_at > decision or r.event_time > decision:
            continue
        if settlement_id not in r.payload.get('settlement_ids', [r.entity_id]):
            continue
        value = r.payload.get('precipitation_mm')
        if value is not None and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
            if latest_interval is None or r.event_time > latest_interval.event_time or (
                r.event_time == latest_interval.event_time and r.payload.get('interval_minutes', 60) <= latest_interval.payload.get('interval_minutes', 60)):
                latest_interval = r
        if r.payload.get('interval_minutes') != 60 or r.event_time.minute or r.event_time.second:
            continue
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            continue
        hourly[r.event_time] = (value, r)
    end = decision.replace(minute=0, second=0, microsecond=0)
    sums, coverage = {}, {}
    for hours in WINDOWS:
        values = [hourly.get(end - timedelta(hours=i), (None, None))[0] for i in range(hours)]
        coverage[str(hours)] = sum(v is not None for v in values)
        sums[str(hours)] = round(sum(values), 2) if all(v is not None for v in values) else None
    duration = 0
    duration_censored = True
    for i in range(72):
        value = hourly.get(end - timedelta(hours=i), (None, None))[0]
        if value is None:
            break
        if value < RULES['wet_hour_mm']:
            duration_censored = False
            break
        duration += 1
    latest = max((t for t, (v, _) in hourly.items() if v is not None), default=None)
    record = hourly[latest][1] if latest else None
    return {'window_end': end.isoformat(), 'rain_mm': sums, 'coverage_hours': coverage,
            'wet_duration_hours': duration if sums['1'] is not None else None,
            'duration_at_least': duration_censored,
            'latest_at': latest.isoformat() if latest else None,
            'age_hours': (decision - latest).total_seconds() / 3600 if latest else None,
            'provider': record.provider if record else None,
            'grid': record.payload.get('grid') if record else None,
            'measurement': record.payload.get('measurement') if record else None,
            'latest_interval_mm': latest_interval.payload['precipitation_mm'] if latest_interval else None,
            'latest_interval_minutes': latest_interval.payload.get('interval_minutes') if latest_interval else None,
            'interval_is_fresh': bool(latest_interval and (decision-latest_interval.event_time).total_seconds() <= 3600)}


def report_evidence(records, settlement_id, decision):
    reports = [r for r in records if r.kind == 'report' and r.available_at <= decision
               and r.event_time <= decision and r.payload.get('settlement_id') == settlement_id]
    latest = {}
    for r in sorted(reports, key=lambda r: (r.event_time, r.available_at)):
        # No known sender is not proof of an independent witness. Keep it visible.
        key = (r.payload.get('sender_id') or 'unknown', r.payload.get('road_id') or settlement_id)
        latest[key] = r
    weighted, positive, negative = [], {}, {}
    stale = 0
    mismatch_detected = False
    mismatch_dist = 0.0
    for r in latest.values():
        age = (decision - r.event_time).total_seconds() / 3600
        if age >= RULES['report_expiry_hours']:
            stale += 1
            continue
        weight = 0.5 ** (age / RULES['report_half_life_hours'])
        on_site = r.payload.get('sender_location_type') == 'on_site'
        is_mismatch = bool(r.payload.get('location_mismatch')) or (r.payload.get('sender_location_type') in ('location_mismatch', 'remote_mismatch'))
        if is_mismatch:
            mismatch_detected = True
            mismatch_dist = max(mismatch_dist, float(r.payload.get('mismatch_distance_km') or 2000.0))
            weight *= 0.1
        else:
            weight *= 1 if on_site else .4
        status = r.payload.get('reported_status')
        sender = r.payload.get('sender_id')
        issue = r.payload.get('road_id') or settlement_id
        if sender and on_site and not is_mismatch and age <= RULES['report_half_life_hours']:
            if status in ('closed', 'flooded', 'need_rescue'): positive.setdefault(issue, set()).add(sender)
            if status in ('open', 'no_flood'): negative.setdefault(issue, set()).add(sender)
        if status in ('closed', 'flooded', 'need_rescue'):
            weighted.append(weight)
    conflict = any(negative.get(issue) for issue in positive)
    supporters = max((len(senders) for senders in positive.values()), default=0)
    
    if not reports:
        msg = 'No ground reports received'
    elif mismatch_detected:
        msg = f"{len(reports)} report(s); location mismatch detected (~{int(mismatch_dist)} km away, outside Lakhimpur); unverified remote report."
    else:
        msg = f'{len(reports)} report(s); {supporters} identified, recent on-site sender(s) supporting the same issue.'

    return {'count': len(reports), 'independent_supporters': supporters,
            'conflict': conflict, 'expired_count': stale,
            'support': max(weighted, default=0),
            'location_mismatch': mismatch_detected,
            'mismatch_distance_km': mismatch_dist,
            'message': msg,
            'records': [{'id': r.entity_id, 'event_time': r.event_time.isoformat(),
                         'available_at': r.available_at.isoformat(), 'source': r.source,
                         'replayed_at': r.replayed_at.isoformat() if r.replayed_at else None,
                         'status': r.payload.get('reported_status'),
                         'raw_text': r.payload.get('raw_text'), 'sender_id': r.payload.get('sender_id'),
                         'location_mismatch': r.payload.get('location_mismatch', False),
                         'sender_location': r.payload.get('sender_location_name')}
                        for r in sorted(reports, key=lambda r: r.available_at, reverse=True)]}


def assess(settlements, records, decision, *, unavailable=False):
    cards = []
    for s in settlements:
        rain = rain_features(records, s['id'], decision)
        reports = report_evidence(records, s['id'], decision)
        slope, river = s.get('slope_degrees'), s.get('distance_to_river_m')
        terrain_known = slope is not None and river is not None
        susceptibility = (1 + .5 * max(0, 1 - river / RULES['near_river_m'])
                          + .5 * max(0, 1 - slope / RULES['flat_slope_degrees'])) if terrain_known else 1
        terrain = {'factor': round(susceptibility, 2), 'level': 'unknown' if not terrain_known else
                   'high' if susceptibility >= 1.6 else 'elevated' if susceptibility >= 1.25 else 'lower',
                   'elevation_m': s.get('elevation_m'), 'slope_degrees': slope,
                   'distance_to_river_m': river,
                   'basis': 'Prototype flat-ground / mapped-river proximity proxy; Copernicus surface terrain. Not a flood-hazard atlas or water-depth estimate.'}
        stale = unavailable or rain['age_hours'] is None or rain['age_hours'] > RULES['stale_hours']
        ratios = [(value / RULES['rain_reference_mm'][window], window) for window, value in rain['rain_mm'].items() if value is not None]
        ratio, driver = max(ratios, default=(0, '1'))
        duration = rain['wet_duration_hours'] or 0
        weather_score = min(100, 45 * ratio * susceptibility * (1 + min(duration, 24) / 96))
        report_score = 65 * reports['support']
        score = round(max(weather_score, report_score), 1)
        insufficient = stale or rain['rain_mm']['6'] is None
        severity = 'unknown' if insufficient and report_score == 0 else 'none'
        # Partial evidence can raise a warning; it cannot establish an all-clear.
        for label, threshold in RULES['severity_score'].items():
            if score >= threshold: severity = label
        if stale and report_score == 0: severity = 'unknown'
        confidence = 'low' if insufficient or not terrain_known or reports['conflict'] else 'medium'
        reason = 'Model rainfall and terrain proxy; heuristic hazard rules are not validated.'
        if insufficient: reason += ' Recent six-hour coverage is incomplete or stale.'
        if reports['independent_supporters'] >= 2:
            reason += ' Multiple identified on-site users corroborate a ground issue.'
            # Overall hazard confidence remains capped: corroboration is not model calibration.
        if reports['conflict']: reason += ' Recent on-site reports conflict; human verification needed.'
        if reports['expired_count']: reason += ' Expired reports do not contribute.'
        strength = (25 if insufficient else 55) + min(20, reports['independent_supporters'] * 10)
        if not terrain_known: strength -= 10
        if reports['conflict']: strength -= 30

        if reports.get('location_mismatch'):
            strength = max(10, strength - 25)
            confidence = 'low'
            reason += f" Citizen report has location mismatch (~{int(reports.get('mismatch_distance_km', 2000))} km away, outside Lakhimpur); confidence score reduced."
            if score is not None and score > 0:
                score = round(max(5.0, score - 6.0), 1)
                severity = 'none'
                for label, threshold in RULES['severity_score'].items():
                    if score >= threshold: severity = label

        confidence = 'low' if strength < 40 else 'medium' if strength < 75 else 'high'
        why = (f"{rain['rain_mm'][driver]:g} mm over {driver} h; terrain factor {susceptibility:.2f}."
               if ratios else 'Rainfall history is unavailable; no dry-weather assumption made.')
        if duration: why += f' {"At least " if rain["duration_at_least"] else ""}{duration} consecutive wet hourly intervals.'
        if report_score: why += ' A ground report adds attention priority; it does not confirm a road closure.'
        cards.append({'settlement_id': s['id'], 'name': s['name'], 'severity': severity,
                      'score': score if severity != 'unknown' else None, 'confidence': confidence,
                      'evidence_strength': max(0, strength),
                      'confidence_reason': reason, 'why': why, 'rainfall': rain, 'terrain': terrain,
                      'reports': reports, 'affected': severity in ('watch', 'high', 'critical') or
                      (not unavailable and rain['interval_is_fresh'] and (rain['latest_interval_mm'] or 0) > 0) or
                      (not stale and (rain['rain_mm']['1'] or 0) >= RULES['wet_hour_mm']) or report_score > 0,
                      'data_status': 'stale_or_missing' if stale else 'partial' if insufficient else 'current'})
    order = {'critical': 4, 'high': 3, 'watch': 2, 'none': 1, 'unknown': 0}
    cards.sort(key=lambda c: (-order[c['severity']], -(c['score'] or 0), c['settlement_id']))
    for rank, card in enumerate(cards, 1): card['rank'] = rank
    return cards
