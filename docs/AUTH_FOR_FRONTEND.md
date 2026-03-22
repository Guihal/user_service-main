# Авторизация в API

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

## Процесс авторизации

Access Token(15 минут) и Refresh Token(7 дней) хранятся в HttpOnly cookie.

### 1) Регистрация 

`POST http://127.0.0.1:8000/api/users/register`

Ограничение запросов (3/минута, 10/час, 20/день)

```json
    {
    "email": "example@gmail.com",
    "username": "Kaban",
    "password": "12345678"
}
```

На пароль есть ограничение (8 символов для пользователя, 12 для админов и других ролей выше пользователя + Хотябы 1 больщая буква + Спец символы)

### 1) Верификация email 

`GET http://127.0.0.1:8000/api/users/verify-email?token=XYZ`

```text
# Письмо
Для активации перейдите по ссылке: http://127.0.0.1:3000verify-email?40d43450-5246-42ef-beed-bddcd0ee5d19
```

Если всё хорошо и почта верифицирована, то сервер возращает `true`.

### 3) Пользователь логиниться 

`POST http://127.0.0.1:8000/api/users/login`

Ограничение запросов (5/минута, 20/час, 50/день)

```json
{
    "email": "example@gmail.com",
    "password": "12345678"
}
```

На пароль есть ограничение (8 символов для пользователя, 12 для админов и других ролей выше пользователя + Хотябы 1 больщая буква + Спец символы)

При успехе записывается `access_token` в HttpOnly cookie. (По ключу `access_token` записан в печеньки). Этот токен живёт 5 минут. Это нужно для дальнейшего подтверждение кода (приходит на почту). На почту отправляется письмо:

```text
Ваш код для входа:

362602

Код действует 5 минут.
```

### 4) Проверка кода 

`POST http://127.0.0.1:8000/api/users/check-code`

Ограничение запросов (5/минута, 20/час)

```json
{
    "otp_code": "123456"
}
```

в Headers нужно отправлять:
```
Key = Authorization
Value = Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMCIsImV4cCI6MTc3MTc2Nzc5NywiaWF0IjoxNzcxNzY3NDk3fQ.gBfoleZhDg8uWOWkwhLjlug2Pw5baEzZAWk95xRfQMtlzd9jlVj3RHWTSpwVVb_gStYe_5ub1M903wQUFSYHRnnCsOjVPZ9WbF2Zd4G9J4VV190ixT0rF3d_GzO041m70nvV-4lCst7Y5bxUW3Fg0iCtKg7HQ4h94BKu-rrDpwxj6PPupEbkPSyEfKTZPFUGM_4A8JKUEqPOg8DikSj-uliSDaZTdZSqlrWLaaOHLhabfvjef4rofQ4yuVPk5EjXc_TWHi2Pm6hPEyANAC8dE4cj0bQC4jRfFgzvjr1oH7YYJ86OoKycV19RiLWev_EAG6DoiiCCsDQ_VNbm3MfeHA
```

Если код верный, то записываются `access_token` и `refresh_token` токены в HttpOnly cookie (Время жизни стандартное 15 мин и 7 д.). В печеньках храняться по тем же ключам.

### 5) Повторная отправка кода 

`POST http://127.0.0.1:8000/api/users/resend-otp`

Ограничение запросов (2/минута, 5/час)

в Headers нужно отправлять:
```
Key = Authorization
Value = Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMCIsImV4cCI6MTc3MTc2Nzc5NywiaWF0IjoxNzcxNzY3NDk3fQ.gBfoleZhDg8uWOWkwhLjlug2Pw5baEzZAWk95xRfQMtlzd9jlVj3RHWTSpwVVb_gStYe_5ub1M903wQUFSYHRnnCsOjVPZ9WbF2Zd4G9J4VV190ixT0rF3d_GzO041m70nvV-4lCst7Y5bxUW3Fg0iCtKg7HQ4h94BKu-rrDpwxj6PPupEbkPSyEfKTZPFUGM_4A8JKUEqPOg8DikSj-uliSDaZTdZSqlrWLaaOHLhabfvjef4rofQ4yuVPk5EjXc_TWHi2Pm6hPEyANAC8dE4cj0bQC4jRfFgzvjr1oH7YYJ86OoKycV19RiLWev_EAG6DoiiCCsDQ_VNbm3MfeHA
```

Возможно было бы полезно в хедерах отправлять `Content-Type: application/json`, но я при тестирование через Postman не отправлял.

### 6) Выход из системы  

`POST http://127.0.0.1:8000/api/users/logout`

Токены выкидываются из печеняк

### 7) Обновление токенов, когда access_token истекает

### 8) Профиль пользователя

Профиль пользователя 

`GET, PUT http://127.0.0.1:8000/api/users/me`

Ответ: 200 OK

```json
{
    "id": 1,
    "email": "example@gmail.com",
    "username": "Kaban",
    "role": "user"
}
```

Так же "role" может быть "user", "admin", "empolee" (Можно их поменять на другие.)

При `PUT` запросе следует отправлять все поля, чтобы они не затирались пустой строкой. (Либо же поменять метод на `PATCH` на бэкенде)

## Основные коды ответов

`200` Успех Обработать данные
`201` Создано Успешная регистрация
`400` Неверные данные Показать ошибку валидации
`401` Не авторизован Обновить токены или редирект на логин
`403` Доступ запрещен Показать сообщение о недостатке прав
`404` Не найдено Показать 404
`429` Too Many Requests Подождать и повторить
