## Возможности API

* Создание коротких ссылок. Доступно всем пользователям. Для
авторизованных пользователей ссылка привязывается к аккаунту.
* Изменение коротких ссылок. Доступно только владельцу ссылки.
* Перенаправление по короткой ссылке. Доступно всем.
* Поиск ссылок по оригинальному URL.
* Удаление ссылок. Владельцы могут удалять свои ссылки, администраторы
--- любые.
* Получение статистики по ссылке (количество переходов, дата создания,
последнее использование).
* Регистрация и аутентификация пользователей с использованием JWT.

## Примеры запросов

### Создание короткой ссылки

``` http
POST /shorten
Content-Type: application/json

{
  "original url": "https://example.com",
  "short code": "example",
  "expires at": "2026-03-31T23:59:59"
}
```

Ответ:

``` json
{
  "short_code": "example",
  "original_url": "https://example.com",
  "expires_at": "2026-03-31T23:59:59",
  "created_at": "2026-03-14T12:11:41",
  "user_id": 1
}
```

### Перенаправление

``` http
GET /example/redirect
```

Ответ:

``` json
{
  "url": "https://example.com"
}
```

### Статистика ссылки

``` http
GET /example/stats
```

Ответ:

``` json
{
  "hits": 10,
  "created_at": "2026-03-14T12:00:00",
  "last_used": "2026-03-14T16:31:02"
}
```

### Регистрация пользователя

``` http
POST /register
Content-Type: application/json

{
  "username": "user1",
  "email": "user1@example.com",
  "password": "password123"
}
```

Ответ:

``` json
{
  "username": "user1",
  "email": "user1@example.com",
  "role": "user"
}
```

### Аутентификация

``` http
POST /login
Content-Type: application/json

{
  "username": "user1",
  "password": "password123"
}
```

Ответ:

``` json
{
  "access_token": "JWT_TOKEN",
  "token_type": "bearer"
}
```

## Запуск проекта

Требуются Docker и Docker Compose.

``` bash
docker-compose up --build
```

После запуска приложение будет доступно по адресу: http://localhost:8000

Документация API: - http://localhost:8000/docs -
http://localhost:8000/redoc

## База данных

### Таблица users

* id --- идентификатор пользователя
* username --- имя пользователя
* email --- электронная почта
* hashed_password --- хеш пароля
* role --- роль пользователя (user или admin)

### Таблица links

* id --- идентификатор ссылки
* short_code --- короткий код
* original_url --- оригинальный URL
* expires_at --- дата истечения
* created_at --- дата создания
* hits --- количество переходов
* last_used --- дата последнего использования
* user_id --- владелец ссылки

