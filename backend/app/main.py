from fastapi import FastAPI

from engine.clock import Clock, LiveClock
from engine.config import load_district
from engine.schemas import Event
from backend.app.api.geography import router as geography_router
from backend.app.api.scenario import router as scenario_router
from backend.app.api.warnings import router as warnings_router
from backend.app.api.live import router as live_router
from backend.app.services.live_weather import LiveWeatherService
from backend.app.services.assessments import AssessmentService
from backend.app.services.teams import TeamStore
from backend.app.api.teams import router as teams_router
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.app.api.road_predictions import router as road_predictions_router
from backend.app.api.routes import router as routes_router
from backend.app.api.reports import router as reports_router
from backend.app.services.reports import ReportStore, GeminiTriageService
from engine.config import ROOT


def create_app(clock: Clock | None = None, operations_path: Path | None = None) -> FastAPI:
    clock = clock or LiveClock()
    district = load_district()
    app = FastAPI(title="Lakhimpur Flood Response", version="0.3.0")
    app.state.live_weather = LiveWeatherService(clock=clock)
    app.state.teams = TeamStore(operations_path)
    app.state.reports = ReportStore(operations_path)
    app.state.assessments = AssessmentService(clock=clock, report_store=app.state.reports)
    app.state.triage = GeminiTriageService()
    app.include_router(teams_router)
    app.include_router(routes_router)
    app.include_router(road_predictions_router)
    app.include_router(reports_router)
    app.include_router(live_router)
    app.include_router(geography_router)
    app.include_router(scenario_router)
    app.include_router(warnings_router)

    # Serve the built mobile view on the same origin as its API for Android/LAN use.
    web_dist = ROOT / "apps/web/dist"
    app.mount("/assets", StaticFiles(directory=web_dist / "assets", check_dir=False), name="web-assets")

    @app.get("/team-mobile", include_in_schema=False)
    def team_mobile():
        from fastapi import HTTPException
        if not (web_dist / "index.html").exists():
            raise HTTPException(503, "Build apps/web with npm run build first")
        return FileResponse(web_dist / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/team-app.apk", include_in_schema=False)
    def team_apk():
        from fastapi import HTTPException
        apk = ROOT / "apps/team-android/app/build/outputs/apk/debug/app-debug.apk"
        if not apk.exists():
            raise HTTPException(404, "Android debug APK has not been built")
        return FileResponse(apk, media_type="application/vnd.android.package-archive", filename="lakhimpur-team-debug.apk")

    @app.get("/citizen-app.apk", include_in_schema=False)
    def citizen_apk():
        from fastapi import HTTPException
        apk = ROOT / "apps/citizen_flutter/AeroLink-main/apps/mobile/build/app/outputs/flutter-apk/app-debug.apk"
        if not apk.exists():
            raise HTTPException(404, "Citizen Flutter debug APK has not finished building yet")
        return FileResponse(apk, media_type="application/vnd.android.package-archive", filename="lakhimpur-citizen-debug.apk")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": app.version, "time": clock.now()}

    @app.get("/api/config")
    def config():
        return district

    @app.post("/api/events/validate")
    def validate_event(event: Event):
        # Validation only: no intake, persistence or operational state mutation.
        return {"valid": True, "label": event.provenance.display_label, "event": event}

    return app


app = create_app()
