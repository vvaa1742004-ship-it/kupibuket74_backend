from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.enums import OrderPriority, ReasonType, Role
from app.keyboards.admin import (
    admin_menu,
    pickup_points_keyboard,
    priority_keyboard,
    reason_keyboard,
)
from app.keyboards.common import cancel_back_keyboard
from app.repositories.courier import CourierRepository
from app.repositories.lookup import LookupRepository
from app.repositories.order import OrderRepository
from app.services.analytics import AnalyticsService
from app.services.formatters import order_card_text
from app.services.orders import OrderService
from app.states.order_create import OrderCreateStates

router = Router()


async def _push_history(state: FSMContext) -> None:
    data = await state.get_data()
    current = await state.get_state()
    history = data.get("history", [])
    if current:
        history.append(current)
        await state.update_data(history=history)


@router.callback_query(F.data == "admin:create_order")
async def admin_create_order(callback: CallbackQuery, role: Role | None, state: FSMContext, session) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    points = await LookupRepository(session).pickup_points()
    await state.clear()
    await state.set_state(OrderCreateStates.pickup_point)
    await callback.message.edit_text("Выберите точку выдачи", reply_markup=pickup_points_keyboard(points))
    await callback.answer()


@router.callback_query(F.data == "admin:analytics")
async def analytics(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    text = await AnalyticsService(session).summary_text()
    await callback.message.edit_text(text, reply_markup=admin_menu())
    await callback.answer()


@router.callback_query(F.data == "admin:reset_form")
async def reset_form(callback: CallbackQuery, role: Role | None, state: FSMContext) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.clear()
    await callback.answer("Форма сброшена")
    await callback.message.edit_text("Форма сброшена", reply_markup=admin_menu())


@router.callback_query(F.data.startswith("pickup:"), OrderCreateStates.pickup_point)
async def choose_pickup_point(callback: CallbackQuery, state: FSMContext) -> None:
    pickup_point_id = int(callback.data.split(":")[1])
    await _push_history(state)
    await state.update_data(pickup_point_id=pickup_point_id)
    await state.set_state(OrderCreateStates.priority)
    await callback.message.edit_text("Выберите приоритет", reply_markup=priority_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("priority:"), OrderCreateStates.priority)
async def choose_priority(callback: CallbackQuery, state: FSMContext) -> None:
    priority = callback.data.split(":")[1]
    await _push_history(state)
    await state.update_data(priority=priority)
    await state.set_state(OrderCreateStates.order_number)
    await callback.message.answer("Введите номер заказа", reply_markup=cancel_back_keyboard())
    await callback.answer()


@router.message(OrderCreateStates.order_number)
async def create_order_number(message: Message, state: FSMContext) -> None:
    await _push_history(state)
    await state.update_data(order_number=message.text.strip())
    await state.set_state(OrderCreateStates.customer)
    await message.answer("Заказчик: ФИО | Телефон", reply_markup=cancel_back_keyboard())


@router.message(OrderCreateStates.customer)
async def create_order_customer(message: Message, state: FSMContext) -> None:
    full_name, phone = [part.strip() for part in message.text.split("|", 1)]
    await _push_history(state)
    await state.update_data(customer_name=full_name, customer_phone=phone)
    await state.set_state(OrderCreateStates.recipient)
    await message.answer("Получатель: ФИО | Телефон", reply_markup=cancel_back_keyboard())


@router.message(OrderCreateStates.recipient)
async def create_order_recipient(message: Message, state: FSMContext) -> None:
    full_name, phone = [part.strip() for part in message.text.split("|", 1)]
    await _push_history(state)
    await state.update_data(recipient_name=full_name, recipient_phone=phone)
    await state.set_state(OrderCreateStates.delivery_window)
    await message.answer(
        "Окно: YYYY-MM-DD HH:MM | YYYY-MM-DD HH:MM",
        reply_markup=cancel_back_keyboard(),
    )


@router.message(OrderCreateStates.delivery_window)
async def create_order_window(message: Message, state: FSMContext) -> None:
    start_raw, end_raw = [part.strip() for part in message.text.split("|", 1)]
    start = datetime.strptime(start_raw, "%Y-%m-%d %H:%M")
    end = datetime.strptime(end_raw, "%Y-%m-%d %H:%M")
    if start >= end:
        await message.answer("Начало окна должно быть раньше конца")
        return
    await _push_history(state)
    await state.update_data(delivery_window_start=start, delivery_window_end=end)
    await state.set_state(OrderCreateStates.address)
    await message.answer(
        "Адрес | Подъезд | Этаж | Кв | Домофон | Детали | lat | lon\n"
        "Для пустых значений используйте -",
        reply_markup=cancel_back_keyboard(),
    )


@router.message(OrderCreateStates.address)
async def create_order_address(message: Message, state: FSMContext) -> None:
    parts = [part.strip() for part in message.text.split("|")]
    while len(parts) < 8:
        parts.append("-")
    lat = None if parts[6] == "-" else float(parts[6])
    lon = None if parts[7] == "-" else float(parts[7])
    await _push_history(state)
    await state.update_data(
        address_text=parts[0],
        entrance=None if parts[1] == "-" else parts[1],
        floor=None if parts[2] == "-" else parts[2],
        apartment=None if parts[3] == "-" else parts[3],
        intercom_code=None if parts[4] == "-" else parts[4],
        details=None if parts[5] == "-" else parts[5],
        lat=lat,
        lon=lon,
    )
    await state.set_state(OrderCreateStates.comment)
    await message.answer("Комментарий или -", reply_markup=cancel_back_keyboard())


@router.message(OrderCreateStates.comment)
async def create_order_comment(message: Message, state: FSMContext) -> None:
    await _push_history(state)
    await state.update_data(comment=None if message.text.strip() == "-" else message.text.strip())
    data = await state.get_data()
    await state.set_state(OrderCreateStates.confirm)
    summary = (
        f"№ {data['order_number']}\n"
        f"{data['address_text']}\n"
        f"Окно: {data['delivery_window_start']} - {data['delivery_window_end']}\n"
        f"Приоритет: {data['priority']}\n"
        "Отправьте 'Подтвердить'"
    )
    await message.answer(summary, reply_markup=cancel_back_keyboard())


@router.message(OrderCreateStates.confirm, F.text.casefold() == "подтвердить")
async def create_order_confirm(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    payload = {k: v for k, v in data.items() if k != "history"}
    payload["priority"] = OrderPriority(payload["priority"])
    order = await OrderService(session, message.bot).create_order(payload, message.from_user.id)
    await state.clear()
    await message.answer(f"Заказ создан: {order.order_number}", reply_markup=admin_menu())


@router.callback_query(F.data == "admin:search")
async def ask_search(callback: CallbackQuery, role: Role | None) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("Отправьте: /find текст")
    await callback.answer()


@router.message(Command("find"))
async def find_orders(message: Message, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /find запрос")
        return
    orders = await OrderRepository(session).search(parts[1].strip())
    if not orders:
        await message.answer("Ничего не найдено")
        return
    text = "\n\n".join(order_card_text(order) for order in orders)
    await message.answer(text)


@router.message(Command("courier_add"))
async def add_courier(message: Message, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Использование: /courier_add <tg_id> <телефон> <ФИО>")
        return
    tg_id = int(parts[1])
    phone = parts[2]
    full_name = parts[3]
    courier = await CourierRepository(session).upsert(tg_id, full_name, phone, is_active=True)
    await message.answer(f"Курьер сохранен: {courier.full_name}")


@router.message(Command("courier_toggle"))
async def toggle_courier(message: Message, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /courier_toggle <tg_id> <on|off>")
        return
    courier = await CourierRepository(session).set_active(int(parts[1]), parts[2].lower() == "on")
    await message.answer("Обновлено" if courier else "Курьер не найден")


@router.callback_query(F.data.startswith("order:view:"))
async def admin_view_order(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[2])
    order = await OrderRepository(session).get(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    await callback.message.edit_text(order_card_text(order))
    await callback.answer()


@router.callback_query(F.data.startswith("order:cancel:"))
async def admin_cancel_pick_reason(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[2])
    reasons = await LookupRepository(session).reasons(ReasonType.CANCELED)
    await callback.message.edit_text(
        f"Причина отмены для заказа #{order_id}",
        reply_markup=reason_keyboard(reasons, f"cancelreason:{order_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancelreason:"))
async def admin_cancel(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, order_id, reason_id = callback.data.split(":")
    service = OrderService(session, callback.bot)
    text = await service.reason_text(int(reason_id))
    order = await service.cancel(int(order_id), callback.from_user.id, text)
    await callback.message.edit_text(order_card_text(order), reply_markup=admin_menu())
    await callback.answer("Отменено")


@router.callback_query(F.data.startswith("order:problem:"))
async def admin_problem_pick_reason(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[2])
    reasons = await LookupRepository(session).reasons(ReasonType.PROBLEM)
    await callback.message.edit_text(
        f"Причина PROBLEM для заказа #{order_id}",
        reply_markup=reason_keyboard(reasons, f"problemreason:{order_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("problemreason:"))
async def admin_problem(callback: CallbackQuery, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, order_id, reason_id = callback.data.split(":")
    service = OrderService(session, callback.bot)
    text = await service.reason_text(int(reason_id))
    order = await service.set_problem(int(order_id), callback.from_user.id, text)
    await callback.message.edit_text(order_card_text(order), reply_markup=admin_menu())
    await callback.answer("Статус обновлен")


@router.callback_query(F.data.startswith("order:reprio:"))
async def choose_repriority(callback: CallbackQuery, role: Role | None) -> None:
    if role != Role.ADMIN:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[2])
    rows = []
    for item in OrderPriority:
        rows.append(f"/reprio {order_id} {item.value}")
    await callback.message.edit_text("Смена приоритета:\n" + "\n".join(rows))
    await callback.answer()


@router.message(Command("reprio"))
async def set_repriority(message: Message, role: Role | None, session) -> None:
    if role != Role.ADMIN:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /reprio <order_id> <VIP|URGENT|NORMAL>")
        return
    order = await OrderService(session, message.bot).set_priority(
        int(parts[1]), message.from_user.id, OrderPriority(parts[2])
    )
    await message.answer(order_card_text(order) if order else "Заказ не найден")
