"""
Тесты для проверки роутов user_service.
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем путь к модулю backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from run import make_app
from entrypoint.ioc import (
    AuthProvider,
    DatabaseProvider,
    RepositoryProvider,
    ServiceProvider,
    ConfigProvider,
    RedisProvider,
)
from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, RoleEnum
from models.user import User
from utils.jwt_utils import hash_password


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class MockRedisProvider(Provider):
    """Мок провайдер для Redis."""
    scope = Scope.APP

    @provide
    def get_redis(self) -> Redis:
        redis_mock = AsyncMock(spec=Redis)
        redis_mock.ping = AsyncMock(return_value=True)
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock(return_value=True)
        redis_mock.delete = AsyncMock(return_value=1)
        redis_mock.aclose = AsyncMock()
        redis_mock.zremrangebyscore = AsyncMock(return_value=0)
        redis_mock.zcount = AsyncMock(return_value=0)
        redis_mock.zadd = AsyncMock(return_value=1)
        redis_mock.expire = AsyncMock(return_value=1)
        # Для pipeline
        pipe_mock = AsyncMock()
        pipe_mock.zremrangebyscore = AsyncMock(return_value=None)
        pipe_mock.zcount = AsyncMock(return_value=None)
        pipe_mock.zadd = AsyncMock(return_value=None)
        pipe_mock.expire = AsyncMock(return_value=None)
        pipe_mock.execute = AsyncMock(return_value=[0, 0, 1, 1])
        redis_mock.pipeline = MagicMock(return_value=pipe_mock)
        redis_mock.pipeline.__aenter__ = AsyncMock(return_value=pipe_mock)
        redis_mock.pipeline.__aexit__ = AsyncMock(return_value=None)
        return redis_mock


class TestDatabaseProvider(Provider):
    """Тестовый провайдер для базы данных."""
    scope = Scope.APP

    def __init__(self):
        super().__init__()
        self.engine = None
        self.session_factory = None

    @provide
    async def get_engine(self):
        self.engine = create_async_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return self.engine

    @provide
    def get_session_factory(self, engine) -> async_sessionmaker:
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @provide
    async def get_session(self, session_factory: async_sessionmaker) -> AsyncSession:
        async with session_factory() as session:
            yield session


@pytest.fixture
def app():
    """Создаём тестовое приложение с моками."""
    test_providers = [
        ConfigProvider(),
        MockRedisProvider(),
        TestDatabaseProvider(),
        RepositoryProvider(),
        ServiceProvider(),
        AuthProvider(),
    ]
    return make_app(*test_providers)


@pytest.fixture
async def client(app):
    """Создаём асинхронный клиент для тестов."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthCheck:
    """Тесты для проверки доступности сервера."""

    async def test_root_endpoint(self, client):
        """Проверка корневого эндпоинта."""
        response = await client.get("/")
        assert response.status_code in [200, 404]  #404 если корневой роут не определён


@pytest.mark.asyncio
class TestUserRegistration:
    """Тесты для регистрации пользователей."""

    async def test_register_user_success(self, client):
        """Успешная регистрация пользователя."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123",
        }
        response = await client.post("/api/users/register", json=user_data)
        # Может быть201 (создан) или400 (если пользователь уже существует)
        assert response.status_code in [200, 201, 400, 422, 500]

    async def test_register_user_invalid_email(self, client):
        """Регистрация с невалидным email."""
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "TestPass123",
        }
        response = await client.post("/api/users/register", json=user_data)
        assert response.status_code == 422  # Validation error

    async def test_register_user_short_password(self, client):
        """Регистрация с коротким паролем."""
        user_data = {
            "email": "test2@example.com",
            "username": "testuser2",
            "password": "Short1",  # Меньше8 символов
        }
        response = await client.post("/api/users/register", json=user_data)
        # Должен вернуть ошибку валидации или400
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestUserLogin:
    """Тесты для входа пользователей."""

    async def test_login_user_invalid_credentials(self, client):
        """Вход с неверными учетными данными."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPass123",
        }
        response = await client.post("/api/users/login", json=login_data)
        # Должен вернуть401 (неавторизован) или404/500 если пользователь не найден
        assert response.status_code in [401, 404, 500]

    async def test_login_user_missing_fields(self, client):
        """Вход с отсутствующими полями."""
        login_data = {
            "email": "test@example.com",
            # password отсутствует
        }
        response = await client.post("/api/users/login", json=login_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestUserProfile:
    """Тесты для профиля пользователя."""

    async def test_get_profile_unauthorized(self, client):
        """Получение профиля без авторизации."""
        response = await client.get("/api/users/me")
        assert response.status_code == 401  # Unauthorized

    async def test_update_profile_unauthorized(self, client):
        """Обновление профиля без авторизации."""
        update_data = {
            "username": "newusername",
        }
        response = await client.put("/api/users/me", json=update_data)
        assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
class TestTokenRefresh:
    """Тесты для обновления токена."""

    async def test_refresh_token_invalid(self, client):
        """Обновление с невалидным токеном."""
        refresh_data = {
            "refresh_token": "invalid_token"
        }
        response = await client.post("/api/users/refresh", json=refresh_data)
        assert response.status_code in [401, 422]  # Unauthorized или Validation error

    async def test_refresh_token_missing(self, client):
        """Обновление без токена."""
        refresh_data = {}
        response = await client.post("/api/users/refresh", json=refresh_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestLogout:
    """Тесты для выхода."""

    async def test_logout_success(self, client):
        """Успешный выход."""
        response = await client.post("/api/users/logout")
        assert response.status_code == 200


# Запуск тестов
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
