from __future__ import annotations

import asyncio

from aiogram import Bot

from app.config import settings
from app.db import SessionFactory
from app.enums import OrderPriority, OrderStatus
from app.repositories.order import OrderRepository
from app.services.notifications import NotificationService


class ReminderScheduler:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def run(self) -> None:
        while True:
            try:
                await self.tick()
            except Exception:
                pass
            await asyncio.sleep(settings.reminder_poll_seconds)

    async def tick(self) -> None:
        async with SessionFactory() as session:
            repo = OrderRepository(session)
            notifications = NotificationService(self.bot, session)

            assigned = await repo.list_reminder_candidates(
                OrderStatus.ASSIGNED, settings.assigned_reminder_minutes
            )
            for order in assigned:
                await notifications.reminder(order, "Напоминание: заберите заказ из отдела")

            picked = await repo.list_reminder_candidates(
                OrderStatus.PICKED_UP, settings.picked_up_reminder_minutes
            )
            for order in picked:
                await notifications.reminder(order, "Напоминание: доставка ожидается")

            if settings.enable_priority_notifications:
                vip = await repo.list_unassigned_priority_candidates(
                    OrderPriority.VIP, settings.vip_repeat_minutes
                )
                for order in vip:
                    await notifications.notify_new_order(order)

                urgent = await repo.list_unassigned_priority_candidates(
                    OrderPriority.URGENT, settings.urgent_repeat_minutes
                )
                for order in urgent:
                    await notifications.notify_new_order(order)

            await session.commit()

