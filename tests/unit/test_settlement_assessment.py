from datetime import datetime, timedelta, timezone
from dataclasses import replace

from engine.warnings.assessment import assess, rain_features
from engine.ingest.source import SourceRecord
from backend.app.services.assessments import AssessmentService

T = datetime(2024, 7, 1, 12, tzinfo=timezone.utc)
SETTLEMENTS = [dict(id='a', name='Near river', elevation_m=90, slope_degrees=0, distance_to_river_m=0),
               dict(id='b', name='Higher slope', elevation_m=130, slope_degrees=5, distance_to_river_m=5000)]


def weather(s='a', mm=5, hours=72):
    return [SourceRecord('weather', s, T-timedelta(hours=i), T-timedelta(hours=i),
             {'precipitation_mm':mm, 'interval_minutes':60}, 'simulated', 'test') for i in range(hours)]


def report(sender, status='closed', age=0, arrival=0, road='r'):
    return SourceRecord('report', f'{sender}-{age}-{status}', T-timedelta(hours=age), T+timedelta(hours=arrival),
        {'settlement_id':'a', 'road_id':road, 'sender_id':sender, 'sender_location_type':'on_site',
         'reported_status':status, 'raw_text':status}, 'simulated', 'test')


def test_exact_windows_missing_duration_and_spatial_independence():
    records = weather() + weather('b', 0)
    a = rain_features(records, 'a', T)
    assert a['rain_mm'] == {'1':5, '3':15, '6':30, '24':120, '72':360}
    assert a['wet_duration_hours'] == 72 and a['duration_at_least']
    assert rain_features(records, 'b', T)['rain_mm']['72'] == 0
    assert rain_features(records[1:], 'a', T)['rain_mm']['1'] is None
    dry = replace(records[2], payload={'precipitation_mm':0, 'interval_minutes':60})
    assert rain_features(records + [dry], 'a', T)['wet_duration_hours'] == 2


def test_future_arrival_and_observation_rejected_duplicates_not_added():
    base = weather(hours=6)
    future = replace(base[0], event_time=T+timedelta(hours=1), payload={'precipitation_mm':999, 'interval_minutes':60})
    delayed = replace(base[0], available_at=T+timedelta(hours=1), payload={'precipitation_mm':999, 'interval_minutes':60})
    assert rain_features(base + base + [future, delayed], 'a', T)['rain_mm']['6'] == 30
    cards = assess(SETTLEMENTS, base + [report('x', arrival=1)], T)
    assert next(c for c in cards if c['settlement_id']=='a')['reports']['count'] == 0


def test_current_interval_rain_is_affected_without_invented_hourly_rain():
    current = SourceRecord('weather','a',T,T,{'precipitation_mm':2,'interval_minutes':15},'live','test')
    c = next(c for c in assess(SETTLEMENTS,[current]+weather(mm=0),T) if c['settlement_id']=='a')
    assert c['affected'] and c['rainfall']['latest_interval_mm']==2
    assert c['rainfall']['rain_mm']['1']==0 and c['severity']=='none'


def test_terrain_changes_risk_not_rain_and_no_terrain_only_alerts():
    cards = {c['settlement_id']: c for c in assess(SETTLEMENTS, weather(mm=3)+weather('b',3), T)}
    assert cards['a']['rainfall']['rain_mm'] == cards['b']['rainfall']['rain_mm']
    assert cards['a']['score'] > cards['b']['score']
    assert len({c['severity'] for c in cards.values()}) == 2
    assert all(c['severity']=='none' for c in assess(SETTLEMENTS, weather(mm=0)+weather('b',0), T))
    assert all(c['severity']=='unknown' for c in assess(SETTLEMENTS, [], T))


def test_report_independence_conflict_staleness_and_source_invariance():
    def card(extra): return next(c for c in assess(SETTLEMENTS, weather(mm=0)+extra, T) if c['settlement_id']=='a')
    single, repeated, pair = card([report('x')]), card([report('x'),report('x')]), card([report('x'),report('y')])
    assert single['evidence_strength'] == repeated['evidence_strength'] < pair['evidence_strength']
    conflict = card([report('x'), report('y','open')])
    assert conflict['confidence'] == 'low' and conflict['reports']['conflict']
    assert not card([report('x'),report('y','open',road='other')])['reports']['conflict']
    assert card([report('x',age=25)])['score'] == 0
    assert card([report('x',age=2)])['score'] < single['score']
    for source in ('live','replay','simulated'):
        c = assess(SETTLEMENTS, [replace(r,source=source) for r in weather()], T)
        assert c[0]['score'] == assess(SETTLEMENTS,weather(),T)[0]['score']


def test_repeated_reads_preserve_delta_new_run_clears_and_stale_is_unknown():
    service = AssessmentService(); service.settlements = SETTLEMENTS
    service.evaluate(weather(mm=0)+weather('b',2), T, 'run1')
    records = weather(mm=20)+weather('b',2)
    changed = service.evaluate(records,T,'run1')
    assert changed[0]['settlement_id']=='a' and changed[0]['rank_delta'] == 1
    assert service.evaluate(records,T,'run1') == changed
    assert all(c['previous_rank'] is None for c in service.evaluate([], T, 'run2'))
    assert all(c['severity']=='unknown' for c in assess(SETTLEMENTS,records,T+timedelta(hours=3)))


def test_location_mismatch_from_pune_decreases_confidence_and_priority():
    # Base scenario: settlement has weather warning (rain 8 mm)
    base_records = weather(mm=8)
    card_before = next(c for c in assess(SETTLEMENTS, base_records, T) if c['settlement_id'] == 'a')
    assert card_before['score'] > 0
    assert card_before['confidence'] in ('medium', 'high')

    # A report sent from Pune (location mismatch: ~2,200 km from Assam)
    pune_report = SourceRecord(
        'report', 'rep-pune-1', T, T,
        {
            'settlement_id': 'a',
            'road_id': None,
            'sender_id': 'device-pune-user',
            'sender_location_type': 'location_mismatch',
            'location_mismatch': True,
            'mismatch_distance_km': 2228.0,
            'sender_location_name': 'Pune, Maharashtra',
            'reported_status': 'flooded',
            'raw_text': 'Heavy water logging reported from Pune device',
        },
        'simulated', 'Citizen Mobile App',
    )

    card_after = next(c for c in assess(SETTLEMENTS, base_records + [pune_report], T) if c['settlement_id'] == 'a')

    # 1. Location mismatch is detected
    assert card_after['reports']['location_mismatch'] is True
    assert card_after['reports']['mismatch_distance_km'] == 2228.0
    assert 'location mismatch' in card_after['reports']['message'].lower()

    # 2. Confidence score is decreased to 'low'
    assert card_after['confidence'] == 'low'
    assert card_after['evidence_strength'] < card_before['evidence_strength']
    assert 'location mismatch' in card_after['confidence_reason'].lower()

    # 3. Priority score decreases slightly because of the location mismatch
    assert card_after['score'] < card_before['score']
    assert round(card_before['score'] - card_after['score'], 1) == 6.0
