# Open questions

None blocks the completed Phase 1 reference-data foundation. Phase 2 awaits approval of PHASE_2_PLAN.md.

Remaining data limitations:
- Official GIS boundary and district profile area differ; published polygon retained without forced reshaping.
- Road accessibility, population and current shelter availability are unknown. Later synthetic needs/resources must be labeled simulated.
- IMD observations and WRIS river gauges were not acquired. Open-Meteo model weather and Copernicus terrain are available.
- Historical event context and ERA5 weather are acquired; historical road closure truth and original forecast issuance times are unavailable.

Before relevant later phases:
- User confirmation of closure reopening rule: newer official observation OR multiple trusted on-site observations; define counts, distance and staleness thresholds.
- Confirm false-alert horizon and operational risk thresholds before computing metrics.
- Gemini API account access and model; configure secrets locally, never in chat or Git.
- ESP32 attached LoRa module pins, USB/serial ports and available power/cables before firmware.
- Phone LAN access and final demonstration network arrangement before app integration.

Resolved: district is Lakhimpur, Assam; time budget about 20 hours; stack delegated; laptop hosts locally with internet access; two ESP32 DevKitV1 boards.


### Resolved model clarifications and remaining questions (2026-10-11)
Road windows now confirmed by model owner as backward accumulated mm at common observation time; ETA is decision-to-arrival travel duration. Model GET works for 30/60/120 using a saved snapshot. Earlier notes saying these definitions are unknown are superseded. Physical Android phone on same Wi-Fi confirmed. Remaining: phone smoke test; custom POST inference request/response; complete timestamped road-feature schema, min/max elevation provenance and verified closure policy for later routing.
