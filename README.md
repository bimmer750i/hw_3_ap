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
  "original\_url": "https://example.com",
  "short\_code": "example",
  "expires\_at": "2026-03-31T23:59:59"
}
```

Ответ:

``` json
{
  "short\_code": "example",
  "original\_url": "https://example.com",
  "expires\_at": "2026-03-31T23:59:59",
  "created\_at": "2025-03-15T12:11:41",
  "user\_id": 1
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
  "created\_at": "2025-03-15T12:00:00",
  "last\_used": "2025-03-15T16:31:02"
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
  "access\_token": "JWT\_TOKEN",
  "token\_type": "bearer"
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
* hashed\_password --- хеш пароля
* role --- роль пользователя (user или admin)

### Таблица links

* id --- идентификатор ссылки
* short\_code --- короткий код
* original\_url --- оригинальный URL
* expires\_at --- дата истечения
* created\_at --- дата создания
* hits --- количество переходов
* last\_used --- дата последнего использования
* user\_id --- владелец ссылки

