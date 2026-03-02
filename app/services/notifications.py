from __future__ import annotations

from aiogram import Bot

from app.config import settings
from app.enums import OrderPriority, OrderStatus
from app.keyboards.courier import order_card_actions
from app.models import Courier, Order
from app.repositories.courier import CourierRepository
from app.services.formatters import order_card_text


class NotificationService:
    def __init__(self, bot: Bot | None, session) -> None:
        self.bot = bot
        self.session = session
        self.courier_repo = CourierRepository(session)

    async def notify_admins(self, order: Order, text_prefix: str) -> None:
        if self.bot is None:
            return
        text = f"{text_prefix}\n{order_card_text(order)}"
        for admin_id in settings.admin_ids:
            await self.bot.send_message(admin_id, text)

    async def notify_new_order(self, order: Order) -> None:
        if self.bot is None:
            return
        if not settings.enable_priority_notifications:
            targets = await self.courier_repo.get_all_active()
        elif order.priority == OrderPriority.VIP:
            targets = await self.courier_repo.get_all_active()
        else:
            targets = await self.courier_repo.free_couriers()
        await self._notify_couriers(targets, order, "Новый заказ")

    async def notify_assigned_manually(self, order: Order, courier_id: int) -> None:
        if self.bot is None:
            return
        await self.bot.send_message(courier_id, f"Вам назначен заказ\n{order_card_text(order)}", reply_markup=order_card_actions(order))

    async def notify_canceled(self, order: Order) -> None:
        if self.bot is None:
            return
        if order.assigned_courier_id:
            await self.bot.send_message(order.assigned_courier_id, f"Заказ отменен\n{order_card_text(order)}")

    async def notify_problem_by_admin(self, order: Order) -> None:
        if self.bot is None:
            return
        if order.assigned_courier_id:
            await self.bot.send_message(order.assigned_courier_id, f"Заказ переведен в PROBLEM\n{order_card_text(order)}")

    async def notify_released(self, order: Order, courier_id: int) -> None:
        if self.bot is None:
            return
        await self.bot.send_message(courier_id, f"Заказ снят с вас\n{order_card_text(order)}")

    async def notify_status_change(self, order: Order) -> None:
        await self.notify_admins(order, f"Статус изменен: {order.status.value}")

    async def reminder(self, order: Order, label: str) -> None:
        if self.bot is None:
            return
        if order.assigned_courier_id:
            await self.bot.send_message(order.assigned_courier_id, f"{label}\n{order_card_text(order)}", reply_markup=order_card_actions(order))

    async def _notify_couriers(self, couriers: list[Courier], order: Order, label: str) -> None:
        if self.bot is None:
            return
        text = f"{label}\n{order_card_text(order)}"
        for courier in couriers:
            await self.bot.send_message(courier.tg_user_id, text, reply_markup=order_card_actions(order))
