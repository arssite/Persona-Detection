from fastapi import APIRouter

from app.api.v1.analyze import router as analyze_router
from app.api.v1.assistant import router as assistant_router

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


router.include_router(analyze_router, prefix="/v1")
router.include_router(assistant_router, prefix="/v1")
