from fastapi import APIRouter

from routers import (
    dev_router,
    user_router,
)


root_router = APIRouter(prefix="/api", tags=["API"])

routers = [
    dev_router,
    user_router,
]

for router in routers:
    root_router.include_router(router)
