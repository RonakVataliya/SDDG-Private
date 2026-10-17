from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.diagram_generation import generate_plantuml
from app.schemas.diagrams import DiagramGenerationRequest, DiagramGenerationResult
from app.services.kroki_service import KrokiServiceError, get_kroki_service

router = APIRouter(prefix="/diagrams", tags=["diagram-generation"])


@router.post("/generate", response_model=DiagramGenerationResult)
async def generate(request: DiagramGenerationRequest) -> DiagramGenerationResult:
    try:
        source = generate_plantuml(request)
        svg, duration = await run_in_threadpool(get_kroki_service().render_svg, source, "plantuml")
        return DiagramGenerationResult(plantuml_source=source, svg=svg, render_duration_seconds=duration)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KrokiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
