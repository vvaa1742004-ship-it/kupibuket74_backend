from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.enums import ReasonType, Role
from app.keyboards.courier import courier_menu, order_card_actions
from app.keyboards.admin import reason_keyboard
from app.repositories.lookup import LookupRepository
from app.repositories.order import OrderRepository
from app.services.formatters import maps_link, order_card_text
from app.services.orders import OrderService

router = Router()


@router.callback_query(F.data == "courier:available")
async def list_available(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    orders = await OrderRepository(session).list_available(0, settings.page_size)
    if not orders:
        await callback.message.edit_text("Нет доступных заказов", reply_markup=courier_menu())
        await callback.answer()
        return
    order = orders[0]
    await callback.message.edit_text(order_card_text(order), reply_markup=order_card_actions(order))
    await callback.answer()


@router.callback_query(F.data == "courier:mine")
async def list_mine(callback: CallbackQuery, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    orders = await OrderRepository(session).list_by_courier(courier.tg_user_id, active_only=True)
    if not orders:
        await callback.message.edit_text("Активных заказов нет", reply_markup=courier_menu())
        await callback.answer()
        return
    lines = [order_card_text(order) for order in orders]
    await callback.message.edit_text("\n\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "courier:route")
async def route_view(callback: CallbackQuery, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    service = OrderService(session, callback.bot)
    route_orders = await service.route_for_courier(courier.tg_user_id)
    if not route_orders:
        await callback.message.edit_text("Маршрут пуст", reply_markup=courier_menu())
        await callback.answer()
        return
    lines = [order_card_text(order, idx) for idx, order in enumerate(route_orders, start=1)]
    await callback.message.edit_text("Текущий маршрут\n\n" + "\n\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "courier:stats")
async def my_stats(callback: CallbackQuery, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    orders = await OrderRepository(session).list_by_courier(courier.tg_user_id, active_only=False)
    delivered = sum(1 for order in orders if order.status.value == "DELIVERED")
    problems = sum(1 for order in orders if order.status.value == "PROBLEM")
    avg = round(sum(order.duration_minutes or 0 for order in orders) / delivered, 1) if delivered else 0
    await callback.message.edit_text(
        f"Выполнено: {delivered}\nПроблемных: {problems}\nСреднее время: {avg} мин"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("take:"))
async def take_order(callback: CallbackQuery, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    ok, order = await OrderService(session, callback.bot).take_order(order_id, courier.tg_user_id)
    if not ok:
        await callback.answer("Уже взяли", show_alert=True)
        return
    await callback.message.edit_text(order_card_text(order), reply_markup=order_card_actions(order))
    await callback.answer("Заказ назначен")


@router.callback_query(F.data.startswith("pickup_done:"))
async def pickup_done(callback: CallbackQuery, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = await OrderService(session, callback.bot).mark_picked_up(order_id, courier.tg_user_id)
    await callback.message.edit_text(order_card_text(order), reply_markup=order_card_actions(order))
    await callback.answer("Отмечено")


@router.callback_query(F.data.startswith("delivered:"))
async def delivered(callback: CallbackQuery, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = await OrderService(session, callback.bot).mark_delivered(order_id, courier.tg_user_id)
    if order is None:
        await callback.answer("Сначала прикрепите фото", show_alert=True)
        return
    await callback.message.edit_text(order_card_text(order), reply_markup=courier_menu())
    await callback.answer("Доставлено")


@router.callback_query(F.data.startswith("proof:"))
async def proof_hint(callback: CallbackQuery, role: Role | None) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    await callback.message.answer(f"Отправьте фото с подписью: proof {order_id} комментарий")
    await callback.answer()


@router.message(F.photo)
async def save_proof_photo(message: Message, role: Role | None, courier, session) -> None:
    if role != Role.COURIER or not message.caption or not message.caption.startswith("proof "):
        return
    parts = message.caption.split(maxsplit=2)
    if len(parts) < 2:
        return
    order_id = int(parts[1])
    comment = parts[2] if len(parts) > 2 else None
    order = await OrderRepository(session).get(order_id)
    if not order or order.assigned_courier_id != courier.tg_user_id:
        await message.answer("Заказ не найден")
        return
    order.proof_photo_file_id = message.photo[-1].file_id
    order.proof_comment = comment
    await session.flush()
    await message.answer("Фото сохранено")


@router.callback_query(F.data.startswith("problem:"))
async def courier_problem_pick_reason(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    reasons = await LookupRepository(session).reasons(ReasonType.PROBLEM)
    await callback.message.edit_text(
        f"Причина по заказу #{order_id}",
        reply_markup=reason_keyboard(reasons, f"courierproblem:{order_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("courierproblem:"))
async def courier_problem(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, order_id, reason_id = callback.data.split(":")
    service = OrderService(session, callback.bot)
    text = await service.reason_text(int(reason_id))
    order = await service.set_problem(int(order_id), callback.from_user.id, text)
    await callback.message.edit_text(order_card_text(order), reply_markup=courier_menu())
    await callback.answer("Статус PROBLEM")


@router.callback_query(F.data.startswith("release:"))
async def release(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.COURIER:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = await OrderService(session, callback.bot).release(order_id, callback.from_user.id)
    await callback.message.edit_text(order_card_text(order), reply_markup=courier_menu())
    await callback.answer("Заказ снят")


@router.message(F.location)
async def handle_location(message: Message, role: Role | None, courier, session) -> None:
    if role != Role.COURIER:
        return
    await OrderService(session, message.bot).save_location(
        courier.tg_user_id, message.location.latitude, message.location.longitude
    )
    url = maps_link(message.location.latitude, message.location.longitude)
    await message.answer(f"Геопозиция обновлена\nКарта: {url}")

