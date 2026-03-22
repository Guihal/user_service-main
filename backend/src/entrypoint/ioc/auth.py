from dishka import Provider, Scope, provide
from fastapi import HTTPException, Request, status
from jwt import InvalidTokenError

from schemas.user import UserResponse
from services.user import UserService
from utils.jwt_utils import decode_jwt


class AuthProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_current_user(
        self,
        user_service: UserService,
        request: Request,
    ) -> UserResponse:
        authorization = request.headers.get("Authorization")

        if authorization:
            try:
                scheme, token = authorization.split()
                if scheme.lower() != "bearer":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication scheme",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header",
                )
        else:
            token = request.cookies.get("access_token")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
            )

        try:
            decoded_token = decode_jwt(token)
        except InvalidTokenError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from err

        user_id = int(decoded_token.get("sub"))

        if user_id:
            user = await user_service.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                token=str(user.token) if user.token else None,
            )
