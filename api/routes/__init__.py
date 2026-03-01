from api.routes.analyze import router as analyze_router
from api.routes.health import router as health_router
from api.routes.results import router as results_router

__all__ = ["analyze_router", "health_router", "results_router"]
