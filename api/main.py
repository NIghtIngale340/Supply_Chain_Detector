import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.middleware.rate_limiter import RateLimiterMiddleware
from api.routes import analyze_router, health_router, results_router
from storage import init_database


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_database()
    logger.info("Database initialized")
    yield


app = FastAPI(title="Supply Chain Detector API", version="0.1.0", lifespan=lifespan)

app.add_middleware(RateLimiterMiddleware, max_requests=120, window_seconds=60)
app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(results_router)

