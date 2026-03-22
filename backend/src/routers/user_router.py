from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Request, status, Response

from schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    RefreshToken,
    # UserToCrossResponse,
    # UserToLocate,
)
from services import UserService
from entrypoint.config import Config

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    route_class=DishkaRoute,
)


@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    service: FromDishka[UserService],
):
    try:
        return await service.register_user(user_data)
    except ValueError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{e}",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    user_data: UserLogin,
    service: FromDishka[UserService],
    config: FromDishka[Config],
):
    try:
        tokens = await service.login_user(user_data)
        return TokenResponse(
            success=True,
            code=status.HTTP_200_OK,
            description="Login successful",
            user_uuid=tokens.user_uuid,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except ValueError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{e}",
        )


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: FromDishka[UserResponse],
):
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    service: FromDishka[UserService],
    token_data: RefreshToken,
):
    try:
        refresh_data = await service.refresh_token(token_data)
        return TokenResponse(
            success=True,
            code=status.HTTP_200_OK,
            description="Token refreshed successfully",
            access_token=refresh_data.access_token,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    service: FromDishka[UserService],
    current_user: FromDishka[UserResponse],
):
    try:
        return await service.update_user(
            current_user.id,
            user_data,
            current_user,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    service: FromDishka[UserService],
    current_user: FromDishka[UserResponse],
):
    try:
        return await service.get_all_users(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{e}",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    service: FromDishka[UserService],
    current_user: FromDishka[UserResponse],
):
    try:
        return await service.get_user(user_id, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e}",
        )


@router.post("/logout", response_model=TokenResponse)
async def logout(
    response: Response,
):
    return TokenResponse(
        success=True,
        code=status.HTTP_200_OK,
        description="Logout successful",
        access_token=None,
        refresh_token=None,
    )
