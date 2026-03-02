from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.enums import OrderPriority, OrderStatus, ReasonType
from app.models import Order
from app.repositories.courier import CourierRepository
from app.repositories.lookup import LookupRepository
from app.repositories.order import OrderRepository
from app.services.formatters import haversine_km
from app.services.notifications import NotificationService
from app.services.routing import RoutingService


class OrderService:
    def __init__(self, session, bot=None) -> None:
        self.session = session
        self.bot = bot
        self.repo = OrderRepository(session)
        self.lookup_repo = LookupRepository(session)
        self.courier_repo = CourierRepository(session)
        self.notifications = NotificationService(bot, session)

    async def create_order(self, data: dict, actor_tg_user_id: int) -> Order:
        pickup_point = await self.lookup_repo.get_pickup_point(data["pickup_point_id"])
        eta = pickup_point.base_eta_minutes if pickup_point else 30
        distance = None
        if pickup_point and data.get("lat") is not None and data.get("lon") is not None:
            distance = haversine_km(pickup_point.lat, pickup_point.lon, data["lat"], data["lon"])
            eta += int(round(distance * 4))
        order = await self.repo.create(
            **data,
            eta_minutes=eta,
            distance_km=distance,
            status=OrderStatus.NEW,
        )
        await self.repo.update_status(order, OrderStatus.NEW, actor_tg_user_id, note="Создан заказ")
        await self.notifications.notify_new_order(order)
        return order

    async def take_order(self, order_id: int, courier_id: int) -> tuple[bool, Order | None]:
        batch = await self.courier_repo.get_or_create_active_batch(courier_id)
        success = await self.repo.assign_if_new(order_id, courier_id, batch.id)
        if not success:
            return False, await self.repo.get(order_id)
        order = await self.repo.get(order_id)
        await self.repo.update_status(order, OrderStatus.ASSIGNED, courier_id, note="Взят курьером")
        await self.notifications.notify_status_change(order)
        return True, order

    async def assign_to_courier_admin(
        self, order_id: int, courier_id: int, actor_tg_user_id: int
    ) -> Order | None:
        order = await self.repo.get(order_id)
        if order is None:
            return None
        batch = await self.courier_repo.get_or_create_active_batch(courier_id)
        order.assigned_courier_id = courier_id
        order.batch_id = batch.id
        order.assigned_at = datetime.now(timezone.utc)
        await self.repo.update_status(order, OrderStatus.ASSIGNED, actor_tg_user_id, "Назначен админом")
        await self.notifications.notify_assigned_manually(order, courier_id)
        await self.notifications.notify_status_change(order)
        return order

    async def mark_picked_up(self, order_id: int, courier_id: int) -> Order | None:
        order = await self.repo.get(order_id)
        if order and order.assigned_courier_id == courier_id:
            await self.repo.update_status(order, OrderStatus.PICKED_UP, courier_id)
            await self.notifications.notify_status_change(order)
        return order

    async def mark_delivered(
        self,
        order_id: int,
        courier_id: int,
        proof_photo_file_id: str | None = None,
        proof_comment: str | None = None,
    ) -> Order | None:
        order = await self.repo.get(order_id)
        if order and order.assigned_courier_id == courier_id:
            if settings.require_proof_photo_on_delivery and not proof_photo_file_id and not order.proof_photo_file_id:
                return None
            order.proof_photo_file_id = proof_photo_file_id or order.proof_photo_file_id
            order.proof_comment = proof_comment or order.proof_comment
            await self.repo.update_status(order, OrderStatus.DELIVERED, courier_id)
            if order.batch_id:
                await self.courier_repo.complete_batch_if_done(order.batch_id)
            await self.notifications.notify_status_change(order)
        return order

    async def set_problem(self, order_id: int, actor_tg_user_id: int, reason_text: str) -> Order | None:
        order = await self.repo.get(order_id)
        if order:
            order.problem_reason = reason_text
            await self.repo.update_status(order, OrderStatus.PROBLEM, actor_tg_user_id, note=reason_text)
            await self.notifications.notify_status_change(order)
        return order

    async def cancel(self, order_id: int, actor_tg_user_id: int, reason_text: str) -> Order | None:
        order = await self.repo.get(order_id)
        if order:
            order.canceled_reason = reason_text
            await self.repo.update_status(order, OrderStatus.CANCELED, actor_tg_user_id, note=reason_text)
            if order.batch_id:
                await self.courier_repo.complete_batch_if_done(order.batch_id)
            await self.notifications.notify_canceled(order)
            await self.notifications.notify_status_change(order)
        return order

    async def release(self, order_id: int, actor_tg_user_id: int) -> Order | None:
        order = await self.repo.get(order_id)
        if order and order.assigned_courier_id:
            courier_id = order.assigned_courier_id
            batch_id = order.batch_id
            await self.repo.release_from_courier(order, actor_tg_user_id, note="Снят с курьера")
            if batch_id:
                await self.courier_repo.complete_batch_if_done(batch_id)
            await self.notifications.notify_released(order, courier_id)
        return order

    async def set_priority(self, order_id: int, actor_tg_user_id: int, priority: OrderPriority) -> Order | None:
        order = await self.repo.get(order_id)
        if order:
            order.priority = priority
            await self.session.flush()
            await self.notifications.notify_admins(order, f"Приоритет изменен: {priority.value}")
            if order.status == OrderStatus.NEW:
                await self.notifications.notify_new_order(order)
        return order

    async def route_for_courier(self, courier_id: int) -> list[Order]:
        orders = await self.courier_repo.get_active_batch_orders(courier_id)
        latest = await self.courier_repo.latest_location(courier_id)
        origin = (latest.lat, latest.lon) if latest else None
        return RoutingService.reorder(orders, origin)

    async def save_location(self, courier_id: int, lat: float, lon: float) -> None:
        await self.courier_repo.save_location(courier_id, lat, lon)

    async def reason_text(self, reason_id: int, free_text: str | None = None) -> str:
        reason = await self.lookup_repo.get_reason(reason_id)
        if not reason:
            return free_text or "Без причины"
        if reason.code.startswith("OTHER") and free_text:
            return f"{reason.text}: {free_text}"
        return reason.text
