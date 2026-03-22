from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

router = APIRouter(
    prefix="",
    tags=["Dev Tools"],
    route_class=DishkaRoute,
)


@router.get("/ping")
async def pong(
    request: Request,
):
    return {"message": "pong"}
