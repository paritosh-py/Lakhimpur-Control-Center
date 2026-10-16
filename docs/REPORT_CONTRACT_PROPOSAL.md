# Ground-report contract proposal v1

Draft for agreement with the teammate training the report model. No runtime schema migration yet. The model extracts claims; backend resolves locations/identity and assesses reliability. Warning severity belongs to the engine, not the parser.

## Model output

One message can contain multiple incidents; use an incidents array. Unknown fields are null, absent claims are not false/zero, and no unstated counts, depths, timestamps or coordinates may be invented. Preserve raw text verbatim separately from cleaned text. A confidence number from an LLM is not a calibrated reliability probability.

```json
{
  "schema_version": "1.0",
  "cleaned_text": "Water is rising near Kadam school. Five people need a boat.",
  "language": "en",
  "incidents": [
    {
      "incident_type": "flooding",
      "location_text": "near Kadam school",
      "observed_at_text": null,
      "reported_road_status": "unknown",
      "water_trend": "rising",
      "water_depth_cm": null,
      "people_affected": 5,
      "injured_count": null,
      "needs": ["boat", "rescue"],
      "evidence_spans": {
        "water_trend": "watr rising",
        "people_affected": "5 ppl",
        "needs": "need boat"
      }
    }
  ],
  "ambiguities": ["Which Kadam school is meant?"],
  "needs_human_review": true
}
```

Illustrative synthetic input: `watr rising near Kadam school 5 ppl need boat`. Evidence spans refer to this original input, not rewritten text. If none of the supported incident types match, use other/unknown and retain description; supported vocabulary to agree: flooding, road_blockage, rescue_request, medical_need, shelter_issue, erosion, landslide, other, unknown. Capturing landslide text does not imply a landslide prediction model exists.

Road status enum: unknown/open/blocked/partially_blocked, always a reported claim. Water trend: rising/falling/stable/unknown. Needs use a controlled list plus free-text other. Units are centimetres for stated water depth and integer people counts; approximations/ranges must remain qualified, never silently converted to exact counts. If a numeric range is supported, add lower/upper/qualifier explicitly in the agreed schema.

## Backend envelope (not authored by NLP)

| Field | Meaning |
|---|---|
| report_id, schema_version, run_id | Backend identifiers and live/replay/exercise isolation |
| source, original_event_id, replayed_at, transformation | Provenance; modified/generated records simulated; original evidence retained |
| transport, transport_message_id | internet/sms/esp_now/lora plus provider/device deduplication key |
| sender_id, sender_role, identity_assurance | Backend-authenticated/pseudonymous sender; never accept model-generated official identity |
| sender_location, accuracy_m, location_method | Claimed/GPS/manual location plus provenance; distinct from incident location |
| received_at, available_at | Server arrival and first usability time; immutable audit fields |
| raw_text, raw_payload_hash | Original input and integrity reference |
| extraction, model_version | Validated output above and parser version |
| resolved_incidents | Per-incident settlement_id, road_segment_id, incident coordinates, match status/candidates and observed_at with time basis |
| verification_status, evidence_ids | Unverified/reviewed/confirmed/rejected with actor and reasoning; history preserved |

All times timezone-aware ISO 8601, UTC storage/IST display. If occurrence time is absent, observed_at remains null and display says time unspecified, received at X. Relative time may be resolved against reception only with ambiguity/time-basis recorded. Receipt is not proof of when an incident happened. available_at guards replay decisions.

Location resolution uses the known gazetteer/road graph; the parser does not guess IDs or GPS. Multiple matches require review. Sender location is not necessarily incident location. Do not infer independent reporters merely from multiple messages/phone numbers; record identity assurance, deduplicate retransmissions and clustered copied reports.

Backend trust assessment includes proximity, age/time uncertainty, source assurance, independent corroboration and conflicts. Preserve extraction confidence separately from report reliability and warning confidence. A single unverified blocked-road claim cannot create an official confirmed closure. Missing ground reports do not block environmental warning generation.

## Transport and teammate handoff

Confirmed by user: teammate parser will be exposed through a Python/FastAPI HTTP API. The JSON shown above remains a proposed contract to agree with that API; its actual endpoint, request/response example and supported languages are not yet supplied.

Use rich JSON internally after receipt. SMS and radio carry compact message IDs, sender/device identity, optional settlement/time/count codes and short text. Gateway reconstructs the envelope; full JSON does not fit the original 50–200 byte radio target. Transport delivery acknowledgement is separate from factual verification. Duplicate radio/SMS delivery must not increase corroboration.

Agree exact JSON Schema, allowed values, missing/ambiguous examples, error/timeout behavior and local-Python versus HTTP delivery before integration. Contract fixtures should cover spelling errors, mixed languages, multiple incidents, negation, unknown location, stale time, copied reports and malformed output. On parser failure, preserve raw input and route it for review; never discard an SOS silently.
