from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/live", tags=["live monitoring"])


@router.get("/conditions")
def conditions(request: Request):
    """A district snapshot. Refreshes upstream at most every ten minutes."""
    return request.app.state.assessments.live(request.app.state.live_weather.get())
