from fastapi import APIRouter
from app.api.v1.endpoints import health, images, analyses, disaster, timeseries, review, agent, reports
from app.api.v1.endpoints import search, discover, ingestion, change

api_router = APIRouter()
api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(images.router)
api_router.include_router(analyses.router)
api_router.include_router(disaster.router)
api_router.include_router(timeseries.router)
api_router.include_router(review.router)
api_router.include_router(agent.router)
api_router.include_router(reports.router)

# PS 26227 — New capability routers
api_router.include_router(search.router)
api_router.include_router(discover.router)
api_router.include_router(ingestion.router)
api_router.include_router(change.router)

