from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.config import settings
from app.handlers import admin_router, common_router, courier_router
from app.middlewares.auth import AuthContextMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.services.scheduler import ReminderScheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    if settings.redis_url:
        storage = RedisStorage.from_url(
            settings.redis_url,
            state_ttl=settings.fsm_ttl_seconds,
            data_ttl=settings.fsm_ttl_seconds,
        )
    else:
        storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    scheduler = ReminderScheduler(bot)

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(AuthContextMiddleware())
    dp.include_router(common_router)
    dp.include_router(admin_router)
    dp.include_router(courier_router)

    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        await scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
