import re

from pydantic import BaseModel, Field, field_validator

from models import RoleEnum


class UserEmail(BaseModel):
    email: str = Field(..., max_length=255)

    @field_validator("email", mode="after")
    @classmethod
    def validate_email(cls, value) -> str:
        email_validate_pattern = r"^\S+@\S+\.\S+$"
        if not re.match(email_validate_pattern, value):
            raise ValueError(f"{value} is not correct email")
        return value


class UserBase(UserEmail):
    username: str = Field(..., max_length=30)
    password: str = Field(..., max_length=255)


class UserCreate(UserBase):
    pass


class UserCreateConsole(UserBase):
    role: RoleEnum


class UserLogin(BaseModel):
    """Login schema that accepts either email or username."""
    email: str | None = Field(None, max_length=255)
    username: str | None = Field(None, max_length=30)
    password: str = Field(..., max_length=255)

    @field_validator("email", mode="after")
    @classmethod
    def validate_email(cls, value) -> str | None:
        if value is None:
            return None
        email_validate_pattern = r"^\S+@\S+\.\S+$"
        if not re.match(email_validate_pattern, value):
            raise ValueError(f"{value} is not correct email")
        return value

    def get_identifier(self) -> str:
        """Returns email or username for login lookup."""
        if self.email:
            return self.email
        if self.username:
            return self.username
        raise ValueError("Either email or username must be provided")


class UserUpdate(BaseModel):
    username: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=255)
    password: str | None = Field(None, max_length=255)


class UserRequest(BaseModel):
    id: int = Field(...)


class UserResponse(UserEmail):
    id: int = Field(...)
    username: str = Field(..., max_length=30)
    role: RoleEnum | str = Field(..., max_length=10)
    token: str | None = Field(None, description="User's UUID token")


class RefreshToken(BaseModel):
    refresh_token: str = Field(...)


class TokenPair(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    user_uuid: str | None = Field(None, description="User's UUID token")

class AccessToken(BaseModel):
    access_token: str = Field(...)


class TokenResponse(BaseModel):
    """Response schema for token endpoints with success status and tokens."""
    success: bool = Field(True, description="Indicates if the operation was successful")
    code: int = Field(..., description="HTTP status code")
    description: str = Field(..., description="Human-readable message")
    user_uuid: str | None = Field(None, description="User's UUID")
    access_token: str | None = Field(None, description="JWT access token")
    refresh_token: str | None = Field(None, description="JWT refresh token")
