from app.routers.auth import router as auth_router
from app.routers.provinces import router as provinces_router
from app.routers.districts import router as districts_router
from app.routers.grid_substations import router as grid_substations_router
from app.routers.solar_installations import router as solar_installations_router
from app.routers.generation_readings import router as generation_readings_router
from app.routers.summaries import router as summaries_router
from app.routers.users import router as users_router

__all__ = [
    "auth_router",
    "provinces_router",
    "districts_router",
    "grid_substations_router",
    "solar_installations_router",
    "generation_readings_router",
    "summaries_router",
    "users_router",
]
