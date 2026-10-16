# Phase 0 validation

Executed 2026-10-10. No domain functionality beyond the foundation is claimed.

- `.venv/Scripts/python.exe -m pytest -q`: 16 passed, 0 failed, 1 upstream Starlette/httpx deprecation warning.
- `.venv/Scripts/python.exe scripts/smoke_api.py`: PASS. Started real uvicorn server on an available loopback port; checked health and Lakhimpur/Assam configuration through HTTP; stopped the process afterward.
- Test coverage: source enum, replay name/playback requirements, original timestamps retained on serialization, timezone requirements, availability chronology, extra field rejection, deterministic clock advancement, negative time rejection, delayed report exclusion, future forecast validity allowed, shelter bounds, assignment windows, API validation failures, generated OpenAPI and absence of future ingestion endpoint.
- Toolchain: local CPython 3.12.15; FastAPI 0.143.0; Pydantic 2.14.0; uvicorn 0.54.0; pytest 9.1.1. Complete resolution in uv.lock.
- No firmware, frontend, provider integration or model was tested because those phases have not started.
- Test server is stopped; use the README command to start a persistent development server.
