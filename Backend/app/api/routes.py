from fastapi import APIRouter

from app.api.v1.analyze import router as analyze_router

router = APIRouter()

@router.get("/health")
def health() -> dict:
    return {"status": "ok"}

router.include_router(analyze_router, prefix="/v1")
