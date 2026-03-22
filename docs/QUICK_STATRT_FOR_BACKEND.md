# Описание бэкенд проекта


## Запуск бэкенда и инфраструктуры

Создание jwt сертификатов

```bash
# Перейти в папку бекенда
cd backend

# Создание папки для ключей
mkdir certs

# Переходим в папку для ключей
cd certs

# Если есть openssl
# Генерация RSA приватного ключа
openssl genrsa -out jwt-private.pem 2048

# Генерация публичного ключа
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
# Без openssl, на windows
# Создание RSA ключей через .NET
$rsa = [System.Security.Cryptography.RSA]::Create(2048)

# Сохранение приватного ключа в PEM формате
$privateKey = $rsa.ExportRSAPrivateKeyPem()
Set-Content -Path "jwt-private.pem" -Value $privateKey

# Сохранение публичного ключа в PEM формате
$publicKey = $rsa.ExportRSAPublicKeyPem()
Set-Content -Path "jwt-public.pem" -Value $publicKey
```

В корне проекта создайте `.env` файл следующего содержания:

```env
POSTGRES_NAME=db
POSTGRES_USER=user
POSTGRES_PASSWORD=12345678
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

APP_NAME=app
APP_MODE=dev
APP_HOST=0.0.0.0
APP_PORT=8000
APP_SECRET_KEY=some_secret_key

EMAIL_PORT=465
EMAIL_HOST=smtp.yandex.ru
EMAIL_USERNAME=yandex@yandex.ru (Почта отправителя)
EMAIL_PASSWORD=some_password (Пороль от почтового приложения)
EMAIL_USE_SSL=true

RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//

FRONTEND_URL=http://127.0.0.1:3000

REDIS_PORT=6379
REDIS_HOST=redis
```
По сути нужно заполнить только блок почты (USERNAME, PASSWORD). Здесь - https://www.youtube.com/watch?v=hwW6l5ScmVA объясняют где взять пароль и как зарегестрировать почтовое приложение на примере Яндекс почты.

```bash
docker-compose up --build -d
```

http://127.0.0.1:8000/docs - Swagger документация
http://127.0.0.1:8000/api - API

## Архитектура

Архитектура разделена на 3 главных слоя: роутеры, сервисыб репозитории.

- Роутеры - Объявление маршрутов
- Сервисы - Бизнес логика
- Репозитории - Доступ к данным (SQLalchemy, Redis и т д)

Дополнительные папки:

- Ядро
- Точка входа
- Интерфейсы
- Модели
- Схемы
- Утилиты

## Права доступа

Применяется в сервисном слое. В параметрах декораторо нужно указать списком роли, кому разрешён доступ к этому ресурсу.

```python
class UserService:
    ...

    @require_roles([RoleEnum.ADMIN])
    async def get_all_users(
            self,
            user: UserResponse,
            offset: int = 0,
            limit: int = 20,
    ):
        users = await self.user_repository.get_all(offset, limit)
        if not users:
            raise ValueError("Not a single user was found")
        return users
```

## Ограничитель запросов

Декоратор применяется в роутерах. Есть 2 стратегии блокировки: user id и ip address.

```python
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Request

from core.rate_limiter import RateLimiter, Strategy, rate_limit

router = APIRouter(
    prefix="",
    tags=["Dev Tools"],
    route_class=DishkaRoute,
)

@router.get("/ping")
@rate_limit(strategy=Strategy.IP, policy="30/s;200/m;3000/h")
# Так же есть стратегия ограничения по user id (Strategy.USER)
async def pong(
        request: Request, # Обязательно передавать этот параметр в функцию
        rate_limiter: FromDishka[RateLimiter],# Обязательно передавать этот параметр в функцию
):
    return {"msg": "pong"}
```

## Внедрение нового функционала
