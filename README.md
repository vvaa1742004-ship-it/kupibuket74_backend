# Flower Courier Bot + Mini App

Production-oriented backend Telegram-бота и Telegram Mini App для курьеров цветочного бизнеса на `Python 3.11`, `aiogram 3`, `FastAPI`, `PostgreSQL`, `SQLAlchemy async`, `Alembic`, `Redis` (только FSM storage), `React + Vite` и `Docker Compose`.

## Возможности

- роли `ADMIN` и `COURIER` по Telegram `user_id`
- FSM-форма создания заказа в Redis с TTL и сохранением после перезапуска
- приоритеты заказов `VIP`, `URGENT`, `NORMAL`
- транзакционное взятие заказа курьером без двойного назначения
- batch-маршруты без лимита по активным заказам
- live/pin location трекинг курьеров через Telegram location
- уведомления администраторам и курьерам
- фоновые напоминания по SLA и повторные уведомления по приоритетам
- аналитика по курьерам и точкам выдачи
- FastAPI REST API для Mini App
- Telegram WebApp auth через `initData`
- React SPA для панелей администратора и курьера
- nginx-проксирование фронтенда к API

## Структура

```text
.
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 0001_initial.py
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── analytics.py
│   │       ├── auth.py
│   │       ├── batches.py
│   │       ├── couriers.py
│   │       └── orders.py
│   ├── config.py
│   ├── db.py
│   ├── enums.py
│   ├── handlers
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── common.py
│   │   └── courier.py
│   ├── keyboards
│   │   ├── admin.py
│   │   ├── common.py
│   │   └── courier.py
│   ├── main.py
│   ├── middlewares
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── db.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── batch.py
│   │   ├── courier.py
│   │   ├── courier_location.py
│   │   ├── order.py
│   │   ├── pickup_point.py
│   │   ├── problem_reason.py
│   │   └── status_history.py
│   ├── repositories
│   │   ├── __init__.py
│   │   ├── courier.py
│   │   ├── lookup.py
│   │   └── order.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── auth.py
│   │   ├── formatters.py
│   │   ├── notifications.py
│   │   ├── orders.py
│   │   ├── routing.py
│   │   └── scheduler.py
│   └── states
│       ├── __init__.py
│       └── order_create.py
├── webapp
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── src
│       ├── App.tsx
│       ├── main.tsx
│       ├── styles.css
│       ├── types.ts
│       ├── components
│       │   ├── AppShell.tsx
│       │   ├── MapView.tsx
│       │   └── OrderCard.tsx
│       ├── hooks
│       │   └── useAuth.ts
│       ├── lib
│       │   ├── api.ts
│       │   └── telegram.ts
│       └── pages
│           ├── AdminDashboard.tsx
│           ├── CourierDashboard.tsx
│           └── OrderPage.tsx
├── docker-compose.yml
├── pyproject.toml
└── seed.py
```

## Компоненты

- `app.main` — Telegram bot worker (aiogram polling, notifications, FSM, background reminders)
- `app.api.main` — FastAPI REST API for Mini App
- `webapp/` — separate Vercel frontend (`React + Vite + MUI`)
- `docker-compose.yml` — local multi-container setup only (`bot`, `api`, `frontend`, `postgres`, `redis`)
- `webapp/nginx.conf` — local frontend proxy for Docker Compose only; not for Railway

## Быстрый запуск

1. Создайте `.env`:

```bash
cp .env.example .env
```

2. Запустите все сервисы:

```bash
docker compose up -d --build
```

Бот применяет миграции при старте через `docker-entrypoint.sh`.

3. Загрузите тестовые данные:

```bash
docker compose exec bot python seed.py
```

4. Откройте сервисы:

- Mini App UI: [http://localhost:8080](http://localhost:8080)
- API: [http://localhost:8000/health](http://localhost:8000/health)

## Команды

- `/start` — главное меню
- `/find <текст>` — поиск заказа (admin)
- `/courier_add <tg_id> <телефон> <ФИО>` — добавить/обновить курьера
- `/courier_toggle <tg_id> <on|off>` — активировать/деактивировать курьера
- `/reprio <order_id> <VIP|URGENT|NORMAL>` — сменить приоритет
- `/start` также показывает кнопки открытия Mini App через `WebAppInfo`

## Mini App Auth

- фронтенд получает `Telegram.WebApp.initData`
- backend проверяет подпись `initData`
- backend определяет роль по `ADMIN_IDS` и таблице `couriers`
- backend выдает JWT access token

## REST API

- `POST /api/v1/auth/telegram`
- `GET /api/v1/auth/me`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{id}`
- `PATCH /api/v1/orders/{id}`
- `POST /api/v1/orders/{id}/assign`
- `POST /api/v1/orders/{id}/status`
- `GET /api/v1/couriers`
- `GET /api/v1/couriers/{id}`
- `POST /api/v1/couriers/location`
- `GET /api/v1/batches/current`
- `GET /api/v1/analytics/summary`

## Важные допущения MVP

- Redis используется только как FSM storage (`RedisStorage.from_url`)
- бизнес-данные и трекинг хранятся только в PostgreSQL
- форма создания заказа использует компактный текстовый ввод для полей с деталями
- уведомления отправляются из bot-процесса, без внешнего брокера задач
- повторные уведомления по VIP/URGENT реализованы через простой polling scheduler
- API-процесс использует тот же Python image, что и бот
- frontend собирается отдельно и отдается через nginx
- Mini App ожидает запуск из Telegram; для локальной отладки можно подставить `window.__DEV_INIT_DATA__`

## Railway Production Deploy

Railway должен поднимать backend из корня репозитория. `webapp` на Railway не деплоится.

Создайте два Railway service из одного и того же репозитория:

1. `api`
2. `bot-worker`

Для обоих:

- Repository: `vvaa1742004-ship-it/kupibuket74_backend`
- Root Directory: `/`
- Builder: `Dockerfile`
- Dockerfile Path: `Dockerfile`

### Service A: API

Start Command:

```bash
sh -c "alembic upgrade head && python -m app.run_api"
```

Минимальные переменные окружения:

```bash
BOT_TOKEN=123456:token
DATABASE_URL=postgresql+asyncpg://...
ALEMBIC_DATABASE_URL=postgresql+psycopg://...   # опционально; если не задан, derive из DATABASE_URL
JWT_SECRET_KEY=replace-with-32-byte-secret-minimum
FRONTEND_ORIGIN=https://kupibuket74delweb.vercel.app
ADMIN_IDS=826701279                              # опционально
TZ=Europe/Moscow
REDIS_URL=redis://...                            # опционально
```

Проверка:

```bash
curl https://your-railway-domain.up.railway.app/health
curl https://your-railway-domain.up.railway.app/docs
```

Ожидается:

- `/health` -> `{"ok": true}`
- `/docs` открывается

### Service B: bot-worker

Start Command:

```bash
python -m app.run_bot
```

`bot-worker` не должен выполнять Alembic миграции.

Минимальные переменные окружения:

```bash
BOT_TOKEN=123456:token
DATABASE_URL=postgresql+asyncpg://...
ADMIN_IDS=826701279
ADMIN_CHAT_ID=-1001234567890
COURIERS_CHAT_ID=-1001234567891
MINIAPP_URL=https://kupibuket74delweb.vercel.app
TZ=Europe/Moscow
REDIS_URL=redis://...   # опционально
```

Проверка:

- в логах есть `bot started`
- нет `TelegramConflictError`
- бот отвечает на `/start`
