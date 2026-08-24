from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    cables,
    dashboard,
    files,
    inventory,
    materials,
    projects,
    resources,
)

api_router = APIRouter()
for router in [
    auth.router,
    materials.router,
    cables.router,
    inventory.router,
    inventory.read_router,
    resources.router,
    projects.router,
    files.router,
    dashboard.router,
    admin.router,
]:
    api_router.include_router(router)
